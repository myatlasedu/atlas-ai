import logging

from contextvars import ContextVar

from dataclasses import dataclass

from uuid import UUID

from db.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
    build_title,
)

from db.session import AsyncSessionLocal

from cache.conversation_cache import (
    ConversationCache,
)


logger = logging.getLogger(__name__)


@dataclass
class ChatTurnHandle:

    # Everything the AI services need to close a turn once
    # the answer is ready.

    session_id: str

    message_id: int

    turn_index: int


# The AI services write their audit row from a background
# task, so the turn it belongs to is carried on the request
# context rather than passed down through every call site.

current_turn: ContextVar["ChatTurnHandle | None"] = ContextVar(
    "current_chat_turn",
    default=None,
)


class ChatSessionService:

    repository = AIChatSessionRepository()

    MAX_SESSIONS_PAGE = 50

    MAX_MESSAGES_PAGE = 200

    # ==================================================
    # TURN LIFECYCLE
    # ==================================================

    @classmethod
    async def start_turn(
        cls,
        *,
        context,
        query: str,
        session_id: str | None = None,
        role: str | None = None,
    ) -> ChatTurnHandle | None:

        resolved_role = cls._resolve_role(
            context=context,
            role=role,
        )

        try:

            async with AsyncSessionLocal() as db:

                session = await cls._resolve_session(
                    db,
                    user_id=context.user_id,
                    role=resolved_role,
                    session_id=session_id,
                    query=query,
                )

                message = await cls.repository.create_message(
                    db,
                    session_id=session["id"],
                    user_id=context.user_id,
                    role=resolved_role,
                    query=query,
                )

                print("\n=====Message Created in DB====")
                print(message)

                # A session created before this turn already
                # carries the title. An existing session that
                # never got one (first turn failed) gets it now.

                if not session.get("title"):

                    await cls.repository.update_session_title(
                        db,
                        session_id=session["id"],
                        title=build_title(query),
                        only_if_empty=True,
                    )

            return ChatTurnHandle(
                session_id=str(
                    session["id"]
                ),
                message_id=message["id"],
                turn_index=message["turn_index"],
            )

        except Exception:

            logger.exception(
                "Failed to open chat turn; continuing without history."
            )

            return None

    @classmethod
    async def complete_turn(
        cls,
        handle: ChatTurnHandle | None,
        *,
        answer: str | None,
        audit_id: int | None = None,
    ) -> None:

        if handle is None:

            return

        try:

            async with AsyncSessionLocal() as db:

                await cls.repository.complete_message(
                    db,
                    message_id=handle.message_id,
                    answer=answer,
                    status="completed",
                    audit_id=audit_id,
                )

        except Exception:

            logger.exception(
                "Failed to close chat turn %s.",
                handle.message_id,
            )

    @classmethod
    async def fail_turn(
        cls,
        handle: ChatTurnHandle | None,
        *,
        error_message: str,
    ) -> None:

        if handle is None:

            return

        try:

            async with AsyncSessionLocal() as db:

                await cls.repository.complete_message(
                    db,
                    message_id=handle.message_id,
                    answer=None,
                    status="failed",
                    error_message=error_message[:2000],
                )

        except Exception:

            logger.exception(
                "Failed to mark chat turn %s as failed.",
                handle.message_id,
            )

    @classmethod
    async def attach_intent(
        cls,
        handle: ChatTurnHandle | None,
        *,
        predicted_intent: str | None = None,
        parsed_intent: dict | None = None,
        selected_tools: list | None = None,
        audit_id: int | None = None,
    ) -> None:

        # A turn only knows its intent once it has been
        # answered. Storing it on the turn row is what lets the
        # cache be rebuilt from ai_chat_message alone, without
        # reaching into the audit table.

        if handle is None:

            return

        try:

            async with AsyncSessionLocal() as db:

                await cls.repository.attach_intent(
                    db,
                    message_id=handle.message_id,
                    predicted_intent=predicted_intent,
                    parsed_intent=parsed_intent,
                    selected_tools=selected_tools,
                    audit_id=audit_id,
                )

        except Exception:

            logger.exception(
                "Failed to store intent on chat turn %s.",
                handle.message_id,
            )

    # ==================================================
    # READ SIDE (FRONTEND)
    # ==================================================

    @classmethod
    async def list_sessions(
        cls,
        *,
        user_id: int,
        role: str,
        limit: int = 20,
        offset: int = 0,
        include_archived: bool = False,
    ) -> list[dict]:

        async with AsyncSessionLocal() as db:

            return await cls.repository.list_sessions(
                db,
                user_id=user_id,
                role=role,
                limit=min(
                    limit,
                    cls.MAX_SESSIONS_PAGE,
                ),
                offset=offset,
                include_archived=include_archived,
            )

    @classmethod
    async def get_transcript(
        cls,
        *,
        session_id: str,
        user_id: int,
        role: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict | None:

        if cls._safe_uuid(session_id) is None:

            return None

        async with AsyncSessionLocal() as db:

            session = await cls.repository.get_session(
                db,
                session_id=session_id,
                user_id=user_id,
                role=role,
            )

            if session is None:

                return None

            messages = await cls.repository.list_messages(
                db,
                session_id=session["id"],
                limit=min(
                    limit,
                    cls.MAX_MESSAGES_PAGE,
                ),
                offset=offset,
            )

        return {
            "session": session,
            "messages": messages,
        }

    @classmethod
    async def rename_session(
        cls,
        *,
        session_id: str,
        user_id: int,
        role: str,
        title: str,
    ) -> bool:

        if cls._safe_uuid(session_id) is None:

            return False

        async with AsyncSessionLocal() as db:

            return await cls.repository.update_session_title(
                db,
                session_id=session_id,
                title=title.strip(),
                user_id=user_id,
                role=role,
            )

    @classmethod
    async def set_status(
        cls,
        *,
        session_id: str,
        user_id: int,
        role: str,
        status: str,
    ) -> bool:

        if cls._safe_uuid(session_id) is None:

            return False

        async with AsyncSessionLocal() as db:

            updated = await cls.repository.set_session_status(
                db,
                session_id=session_id,
                user_id=user_id,
                role=role,
                status=status,
            )

        if (
            updated
            and
            status == "deleted"
        ):

            # A deleted thread must not keep feeding context.

            await ConversationCache.clear(
                session_id
            )

        return updated

    @classmethod
    async def create_session(
        cls,
        *,
        user_id: int,
        role: str,
        title: str | None = None,
    ) -> dict:

        async with AsyncSessionLocal() as db:

            return await cls.repository.create_session(
                db,
                user_id=user_id,
                role=role,
                title=(
                    title.strip()
                    if title
                    else None
                ),
            )

    # ==================================================
    # INTERNAL
    # ==================================================

    @classmethod
    async def _resolve_session(
        cls,
        db,
        *,
        user_id: int,
        role: str,
        session_id: str | None,
        query: str,
    ) -> dict:

        if cls._safe_uuid(session_id):
            print("\n====Session ID as INPUT in resolve session====")
            print(session_id)

            session = await cls.repository.get_session(
                db,
                session_id=session_id,
                user_id=user_id,
                role=role,
            )

            if session is not None:

                return session

            # An unknown or foreign session id must never be
            # written into - start a fresh thread instead.

            logger.warning(
                "Session %s not available for user=%s role=%s; starting a new one.",
                session_id,
                user_id,
                role,
            )

        elif session_id:

            logger.warning(
                "Ignoring malformed session id: %s",
                session_id,
            )

        return await cls.repository.create_session(
            db,
            user_id=user_id,
            role=role,
            title=build_title(query),
        )

    @staticmethod
    def _safe_uuid(
        value,
    ) -> str | None:

        # A session id reaches us from the frontend, so a
        # malformed one is a 404, never a 500.

        if not value:

            return None

        try:

            return str(
                UUID(
                    str(value)
                )
            )

        except (ValueError, AttributeError, TypeError):

            return None

    @staticmethod
    def _resolve_role(
        *,
        context,
        role: str | None,
    ) -> str:

        # MentorContext carries no role field, so the calling
        # service passes its own.

        return (
            getattr(
                context,
                "role",
                None,
            )
            or role
            or "student"
        )
