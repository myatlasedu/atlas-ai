import logging

from db.session import AsyncSessionLocal

from db.repositories.intent_audit_repository import (
    IntentAuditRepository,
)

logger = logging.getLogger(__name__)


class IntentAuditService:

    @classmethod
    async def capture(
        cls,
        *,
        query,
        context,
        parsed_intent,
    ):

        try:

            async with AsyncSessionLocal() as db:

                repo = IntentAuditRepository(db)

                await repo.create(

                    query=query,

                    role=context.role,

                    user_id=context.user_id,

                    predicted_intent=parsed_intent.intent,

                    confidence=parsed_intent.confidence,

                    parser_output=parsed_intent.model_dump(),
                )

        except Exception:

            logger.exception(
                "Failed to capture intent audit."
            )