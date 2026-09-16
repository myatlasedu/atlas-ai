import logging

from cache.conversation_cache import (
    ConversationCache,
)

from db.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
)

from db.session import AsyncSessionLocal

from schemas.conversation import ConversationTurn

logger = logging.getLogger(__name__)


class ConversationContextService:

    MAX_TURNS = 5

    # History is session scoped: Redis holds it, and ai_chat_message
    # rebuilds it when the key has expired. ai_conversation_audit is a
    # debug table and is never read here - a query with no session is
    # a fresh chat, not a query to be answered from someone's past.

    session_repository = AIChatSessionRepository()

    @classmethod
    async def load_recent_turns(
        cls,
        *,
        turn=None,
        limit: int | None = None,
    ) -> list[ConversationTurn]:

        target_limit = limit or cls.MAX_TURNS

        session_id = getattr(
            turn,
            "session_id",
            None,
        )

        if not session_id:

            logger.info(
                "No session on this turn; answering as a fresh chat."
            )

            return []

        if (
            getattr(
                turn,
                "turn_index",
                0,
            )
            <= 1
        ):

            logger.info(
                "First turn of session=%s; skipping history lookup.",
                session_id,
            )

            return []

        return await cls._load_session_turns(
            session_id=session_id,
            limit=target_limit,
        )

    # ==================================================
    # SESSION SCOPED (REDIS FIRST)
    # ==================================================

    @classmethod
    async def _load_session_turns(
        cls,
        *,
        session_id: str,
        limit: int,
    ) -> list[ConversationTurn]:

        rows = await ConversationCache.load(
            session_id,
            limit=limit,
        )

        if rows is None:

            rows = await cls._rebuild_cache(
                session_id=session_id,
                limit=limit,
            )

        else:

            logger.info(
                "Loaded %s cached turn(s) for session=%s",
                len(rows),
                session_id,
            )

        return cls._build_turns(
            rows
        )

    @classmethod
    async def _rebuild_cache(
        cls,
        *,
        session_id: str,
        limit: int,
    ) -> list[dict]:

        try:

            async with AsyncSessionLocal() as db:

                rows = await cls.session_repository.list_recent_turns(
                    db,
                    session_id=session_id,
                    limit=limit,
                )

        except Exception:

            logger.exception(
                "Failed to rebuild conversation cache; continuing without history."
            )

            return []

        logger.info(
            "Rebuilt %s turn(s) from ai_chat_message for session=%s",
            len(rows),
            session_id,
        )

        await ConversationCache.seed(
            session_id,
            rows,
        )

        return rows

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _build_turns(
        rows: list[dict],
    ) -> list[ConversationTurn]:

        turns: list[ConversationTurn] = []

        for row in rows:

            try:

                turns.append(
                    ConversationTurn(
                        **row
                    )
                )

            except Exception:

                logger.warning(
                    "Skipping malformed turn ID: %s",
                    row.get(
                        "turn_id"
                    ),
                )

        return turns

    @staticmethod
    def previous_turn(
        turns: list[ConversationTurn],
    ) -> ConversationTurn | None:

        return turns[0] if turns else None
