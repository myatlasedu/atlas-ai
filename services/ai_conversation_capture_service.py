import asyncio
import logging

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
)


logger = logging.getLogger(__name__)


class AIConversationCaptureService:

    def __init__(self):

        self.repository = (
            AIConversationAuditRepository()
        )

    async def capture(
        self,
        *,
        user_id: int,
        role: str,
        query: str,
        predicted_intent: str,
        parsed_intent: dict | None = None,
        selected_tools: list | None = None,
        tool_results: dict | None = None,
        summary: str = "",
        total_latency_ms: int | None = None,
        intent_latency_ms: int | None = None,
        tool_latency_ms: int | None = None,
        summarizer_latency_ms: int | None = None,
    ):

        try:

            async with AsyncSessionLocal() as db:

                audit_id = await self.repository.create(

                    db=db,

                    user_id=user_id,

                    role=role,

                    query=query,

                    predicted_intent=
                        predicted_intent,

                    parsed_intent=
                        parsed_intent,

                    selected_tools=
                        selected_tools,

                    tool_results=
                        tool_results,

                    summary=
                        summary,

                    total_latency_ms=
                        total_latency_ms,

                    intent_latency_ms=
                        intent_latency_ms,

                    tool_latency_ms=
                        tool_latency_ms,

                    summarizer_latency_ms=
                        summarizer_latency_ms,
                )

                logger.info(
                    "AI conversation captured: audit_id=%s",
                    audit_id,
                )

                return audit_id

        except Exception:

            logger.exception(
                "Failed to capture AI conversation audit"
            )

            return None

    def capture_background(
        self,
        **kwargs,
    ):

        task = asyncio.create_task(
            self.capture(
                **kwargs
            )
        )

        task.add_done_callback(
            self._background_task_done
        )

    @staticmethod
    def _background_task_done(
        task: asyncio.Task,
    ):

        try:

            task.result()

        except Exception:

            logger.exception(
                "AI audit background capture failed"
            )


ai_conversation_capture_service = (
    AIConversationCaptureService()
)