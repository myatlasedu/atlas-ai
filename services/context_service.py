import logging

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from cache.conversation_cache import (
    ConversationCache,
)

from db.repositories.ai_chat_session_repository import (
    AIChatSessionRepository,
)

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
)
from db.session import AsyncSessionLocal

from schemas.conversation import ConversationTurn

logger = logging.getLogger(__name__)


class ConversationContextService:

    MAX_TURNS = 5

    # Older turns are a different conversation, not context for this one.
    # Only applies to the legacy path - a session is its own boundary.

    MAX_AGE = timedelta(hours=24)

    repository = AIConversationAuditRepository()

    session_repository = AIChatSessionRepository()

    @classmethod
    async def load_recent_turns(
        cls,
        *,
        context,
        turn=None,
        limit: int | None = None,
    ) -> list[ConversationTurn]:

        target_limit = limit or cls.MAX_TURNS

        session_id = getattr(
            turn,
            "session_id",
            None,
        )

        if session_id:
            print("\n====Session Present====")
            print(session_id)

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

        print("\n====Session Not Present=====")
        return await cls._load_user_turns(
            context=context,
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
            print("\n=====Session Cache Expire/not build in redis=====")
            print()

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
                print("\n====Listing recent turn====")

                rows = await cls.session_repository.list_recent_turns(
                    db,
                    session_id=session_id,
                    limit=limit,
                )
                print("\n==== Recent Turns during building cache====")
                print(rows)

        except Exception:

            logger.exception(
                "Failed to rebuild conversation cache; continuing without history."
            )

            return []

        logger.info(
            "Rebuilt %s turn(s) from Postgres for session=%s",
            len(rows),
            session_id,
        )

        await ConversationCache.seed(
            session_id,
            rows,
        )

        return rows

    # ==================================================
    # USER SCOPED (LEGACY FALLBACK)
    # ==================================================

    @classmethod
    async def _load_user_turns(
        cls,
        *,
        context,
        limit: int,
    ) -> list[ConversationTurn]:

        try:
            async with AsyncSessionLocal() as db:
                rows = await cls.repository.list_recent_turns(
                    db,
                    user_id=context.user_id,
                    role=context.role,
                    limit=limit,
                )
        except Exception:
            logger.exception(
                "Failed to load conversation context; continuing without history."
            )
            return []

        turns: list[ConversationTurn] = []
        for row in rows:
            try:
                turn = ConversationTurn(**row)
            except Exception:
                logger.warning(
                    "Skipping malformed turn ID: %s",
                    row.get("turn_id"),
                )
                continue

            if cls._is_stale(turn):
                # Newest-first ordering: everything below is older still.
                break

            turns.append(turn)

        logger.info(
            "Loaded %s genuine turn(s) for user=%s role=%s",
            len(turns),
            context.user_id,
            context.role,
        )
        return turns

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

    @classmethod
    def _is_stale(
        cls,
        turn: ConversationTurn,
    ) -> bool:

        if turn.created_at is None:
            return False

        created_at = turn.created_at

        # The column is naive UTC in some environments, aware in others.
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        return (
            datetime.now(timezone.utc) - created_at
        ) > cls.MAX_AGE

    @staticmethod
    def previous_turn(
        turns: list[ConversationTurn],
    ) -> ConversationTurn | None:
        return turns[0] if turns else None
