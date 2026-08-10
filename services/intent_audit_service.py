import logging

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
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

                repo = (
                    AIConversationAuditRepository()
                )

                await repo.create(

                    db,

                    query=query,

                    role=context.role,

                    user_id=context.user_id,

                    predicted_intent=(
                        parsed_intent.intent
                    ),

                    parsed_intent=(
                        parsed_intent.model_dump()
                    ),
                )

        except Exception:

            # Audit failure must never
            # break the AI request.

            logger.exception(
                "Failed to capture AI conversation audit."
            )