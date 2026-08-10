import asyncio
import logging
import time

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
)

from db.session import (
    AsyncSessionLocal,
)

from intents.guardian.parser import (
    parse_guardian_intent,
)

from intents.guardian.enums import (
    GuardianIntent,
)

from routing.guardian_tool_router import (
    get_tools_for_intent,
)

from tools.student.registry import (
    TOOL_REGISTRY,
)

from llm.summarizer import (
    summarize_response,
)

from services.date_service import (
    DateService,
)

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)


logger = logging.getLogger(__name__)


class GuardianAIService:

    def __init__(self):

        self.audit_repository = (
            AIConversationAuditRepository()
        )

    # ==================================================
    # AUDIT CAPTURE
    # ==================================================

    async def _capture_audit(
        self,
        *,
        context,
        query: str,
        parsed_intent,
        selected_tools: list,
        tool_results: dict,
        summary: str,
        total_latency_ms: int,
        intent_latency_ms: int,
        tool_latency_ms: int,
        summarizer_latency_ms: int,
    ):

        try:

            async with AsyncSessionLocal() as db:

                await self.audit_repository.create(

                    db=db,

                    user_id=context.user_id,

                    role=context.role,

                    query=query,

                    predicted_intent=(
                        parsed_intent.intent.value
                        if hasattr(
                            parsed_intent.intent,
                            "value",
                        )
                        else str(
                            parsed_intent.intent
                        )
                    ),

                    parsed_intent=(
                        parsed_intent.model_dump()
                    ),

                    selected_tools=(
                        selected_tools
                    ),

                    tool_results=(
                        tool_results
                    ),

                    summary=(
                        summary or ""
                    ),

                    total_latency_ms=(
                        total_latency_ms
                    ),

                    intent_latency_ms=(
                        intent_latency_ms
                    ),

                    tool_latency_ms=(
                        tool_latency_ms
                    ),

                    summarizer_latency_ms=(
                        summarizer_latency_ms
                    ),
                )

        except Exception:

            logger.exception(
                "Failed to capture AI conversation audit."
            )

    def _schedule_audit(
        self,
        **kwargs,
    ):

        task = asyncio.create_task(
            self._capture_audit(
                **kwargs
            )
        )

        task.add_done_callback(
            self._audit_task_done
        )

    @staticmethod
    def _audit_task_done(
        task: asyncio.Task,
    ):

        try:

            task.result()

        except Exception:

            logger.exception(
                "AI conversation audit background task failed."
            )

    # ==================================================
    # ANSWER
    # ==================================================

    async def answer(
        self,
        query: str,
        context,
    ):

        request_start = (
            time.perf_counter()
        )

        # ==================================================
        # DEFAULT AUDIT VALUES
        # ==================================================

        selected_tools = []

        results = {}

        intent_latency_ms = 0

        tool_latency_ms = 0

        summarizer_latency_ms = 0

        summary = ""

        # ==================================================
        # INTENT PARSING
        # ==================================================

        intent_start = (
            time.perf_counter()
        )

        parsed_intent = (
            await parse_guardian_intent(
                query
            )
        )

        parsed_intent = (
            DateService.validate(
                parsed_intent
            )
        )

        intent_latency_ms = int(
            (
                time.perf_counter()
                - intent_start
            )
            * 1000
        )

        logger.info(
            "Parsed Guardian Intent: %s",
            parsed_intent.model_dump(),
        )

        # ==================================================
        # UNKNOWN INTENT SHORT CIRCUIT
        # ==================================================

        if (
            parsed_intent.intent
            ==
            GuardianIntent.UNKNOWN
        ):

            summary = (
                build_unknown_intent_summary(
                    "guardian"
                )
            )

            total_latency_ms = int(
                (
                    time.perf_counter()
                    - request_start
                )
                * 1000
            )

            self._schedule_audit(

                context=context,

                query=query,

                parsed_intent=parsed_intent,

                selected_tools=[],

                tool_results={},

                summary=summary,

                total_latency_ms=(
                    total_latency_ms
                ),

                intent_latency_ms=(
                    intent_latency_ms
                ),

                tool_latency_ms=0,

                summarizer_latency_ms=0,
            )

            return {

                "success": True,

                "query":
                    query,

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    {},

                "summary":
                    summary,
            }

        # ==================================================
        # TOOL SELECTION
        # ==================================================

        selected_tools = (
            get_tools_for_intent(
                intent=parsed_intent.intent
            )
        )

        logger.info(
            "Guardian tools: %s",
            selected_tools,
        )

        # ==================================================
        # TOOL EXECUTION
        # ==================================================

        for tool_name in selected_tools:

            tool = TOOL_REGISTRY.get(
                tool_name
            )

            if tool is None:

                logger.warning(
                    "Tool not found: %s",
                    tool_name,
                )

                continue

            tool_start = (
                time.perf_counter()
            )

            result = await tool.run(

                context=context,

                parsed_intent=parsed_intent,
            )

            current_tool_latency_ms = int(
                (
                    time.perf_counter()
                    - tool_start
                )
                * 1000
            )

            tool_latency_ms += (
                current_tool_latency_ms
            )

            results[
                tool_name
            ] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result,
            )

        # ==================================================
        # SUMMARY
        # ==================================================

        summarizer_start = (
            time.perf_counter()
        )

        summary = await summarize_response(

            query=query,

            data=results,

            context=context,

            intent=parsed_intent.intent,
        )

        summarizer_latency_ms = int(
            (
                time.perf_counter()
                - summarizer_start
            )
            * 1000
        )

        logger.info(
            "Guardian summarizer completed."
        )

        # ==================================================
        # FINAL AUDIT
        # ==================================================

        total_latency_ms = int(
            (
                time.perf_counter()
                - request_start
            )
            * 1000
        )

        self._schedule_audit(

            context=context,

            query=query,

            parsed_intent=parsed_intent,

            selected_tools=selected_tools,

            tool_results=results,

            summary=summary,

            total_latency_ms=(
                total_latency_ms
            ),

            intent_latency_ms=(
                intent_latency_ms
            ),

            tool_latency_ms=(
                tool_latency_ms
            ),

            summarizer_latency_ms=(
                summarizer_latency_ms
            ),
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        return {

            "success": True,

            "query":
                query,

            "intent":
                parsed_intent.model_dump(),

            "data":
                results,

            "summary":
                summary,
        }