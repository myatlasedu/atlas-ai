import logging

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
)

from db.session import (
    AsyncSessionLocal,
)

from schemas.conversation import (
    ConversationTurn,
)


logger = logging.getLogger(__name__)


class ConversationContextService:

    # Loads the recent conversation a follow-up can lean on.

    MAX_TURNS = 1

    # Anything older than this is a different conversation

    SESSION_WINDOW_MINUTES = 360

    # Turns that carry no reusable intent or parameters.

    NON_CONTEXTUAL_INTENTS = frozenset(
        {
            "unknown",
            "action_confirmation",
            "",
        }
    )

    #
    # Rows are read per usable turn, because the ones filtered out
    # above still occupy the newest slots.
    #

    SCAN_MULTIPLIER = 4

    repository = AIConversationAuditRepository()

    @classmethod
    async def load_recent_turns(
        cls,
        *,
        context,
        limit: int | None = None,
    ) -> list[ConversationTurn]:

        limit = (
            limit
            or cls.MAX_TURNS
        )

        try:

            async with AsyncSessionLocal() as db:

                rows = await cls.repository.list_recent_turns(

                    db,

                    user_id=context.user_id,

                    role=context.role,

                    limit=(
                        limit
                        * cls.SCAN_MULTIPLIER
                    ),

                    window_minutes=(
                        cls.SESSION_WINDOW_MINUTES
                    ),
                )

        except Exception:

            logger.exception(
                "Failed to load conversation context; "
                "continuing without history."
            )

            return []

        turns: list[ConversationTurn] = []

        for row in rows:

            intent = (
                str(
                    row.get(
                        "predicted_intent",
                        "",
                    )
                )
                .strip()
                .lower()
            )

            if intent in cls.NON_CONTEXTUAL_INTENTS:

                continue

            if not row.get("query"):

                continue

            try:

                turns.append(
                    ConversationTurn(**row)
                )

            except Exception:

                logger.warning(
                    "Skipping malformed conversation turn: %s",
                    row.get("turn_id"),
                )

            if len(turns) >= limit:

                break

        logger.info(
            "Loaded %s conversation turn(s) for user=%s role=%s",
            len(turns),
            context.user_id,
            context.role,
        )

        return turns

    @staticmethod
    def previous_turn(
        turns: list[ConversationTurn],
    ) -> ConversationTurn | None:

        # Turns arrive newest-first.

        return (
            turns[0]
            if turns
            else None
        )
