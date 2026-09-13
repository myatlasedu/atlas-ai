import logging

from datetime import (
    datetime,
    timedelta,
    timezone,
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

    MAX_AGE = timedelta(hours=6)

    repository = AIConversationAuditRepository()

    @classmethod
    async def load_recent_turns(
        cls,
        *,
        context,
        limit: int | None = None,
    ) -> list[ConversationTurn]:
        target_limit = limit or cls.MAX_TURNS

        try:
            async with AsyncSessionLocal() as db:
                rows = await cls.repository.list_recent_turns(
                    db,
                    user_id=context.user_id,
                    role=context.role,
                    limit=target_limit,
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
