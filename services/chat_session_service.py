import logging

from contextvars import ContextVar

from dataclasses import dataclass

from db.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
)

from db.session import AsyncSessionLocal

from cache.conversation_cache import (
    ConversationCache,
)

from cache.session_memory_cache import (
    SessionMemoryCache,
)


logger = logging.getLogger(__name__)


@dataclass
class ChatTurnHandle:

    session_id: int


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
    def start_turn(
        cls,
        *,
        session_id: int,
    ) -> ChatTurnHandle | None:


        if not session_id:

            return None

        return ChatTurnHandle(
            session_id=session_id,
        )

    # ==================================================
    # READ SIDE
    # ==================================================

    @classmethod
    async def get_transcript(
        cls,
        *,
        session_id: int,
        user_id: int,
        role: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict | None:

        async with AsyncSessionLocal() as db:

            session = await cls.repository.get_session(
                db,
                session_id=session_id,
                user_id=user_id,
                role=role,
            )

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
        session_id: int,
        user_id: int,
        role: str,
        title: str,
    ) -> bool:

        if not session_id:

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
        session_id: int,
        user_id: int,
        role: str,
        status: str,
    ) -> bool:

        if not session_id:

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

            await SessionMemoryCache.clear(
                session_id
            )

        return updated

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
                limit=limit,
                offset=offset,
                include_archived=include_archived,
            )

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
