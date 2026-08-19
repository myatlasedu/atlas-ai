import asyncio
import logging
import time

from db.repositories.ai_conversation_audit_repository import (
    AIConversationAuditRepository,
)

from db.session import (
    AsyncSessionLocal,
)

from intents.router import (
    parse_intent,
)

from intents.student.enums import (
    StudentIntent,
)

from intents.student.schemas import (
    ParsedStudentIntent,
)

from routing.student_tool_router import (
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

from cache.pending_action_cache import (
    PendingActionCache,
)

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)


logger = logging.getLogger(__name__)


class StudentAIService:

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
                        if isinstance(
                            parsed_intent.intent,
                            StudentIntent,
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

        request_start = time.perf_counter()

        normalized_query = (
            query
            .strip()
            .lower()
        )

        # ==================================================
        # DEFAULT AUDIT VALUES
        # ==================================================

        parsed_intent = None

        selected_tools = []

        results = {}

        intent_latency_ms = 0

        tool_latency_ms = 0

        summarizer_latency_ms = 0

        summary = ""

        # ==================================================
        # CONFIRMATION SHORT CIRCUIT
        # ==================================================

        pending_action = (
            await PendingActionCache.get(
                context.user_id
            )
        )

        if pending_action:

            if normalized_query in [

                "yes",
                "y",
                "yeah",
                "yep",
                "confirm",
                "ok",
                "okay",
                "proceed",
                "go ahead",
                "do it",
            ]:

                logger.info(
                    "Pending action confirmation detected"
                )

                parsed_intent = (
                    ParsedStudentIntent(

                        intent=(
                            StudentIntent.ACTION_CONFIRMATION
                        ),

                        start_date=None,

                        end_date=None,

                        target_modules=[],

                        confidence=1.0,

                        original_query=query,
                    )
                )

            elif normalized_query in [

                "no",
                "n",
                "cancel",
                "stop",
                "don't",
                "dont",
                "never mind",
            ]:

                await PendingActionCache.delete(
                    context.user_id
                )

                summary = (
                    "The pending action has been cancelled."
                )

                total_latency_ms = int(
                    (
                        time.perf_counter()
                        - request_start
                    )
                    * 1000
                )

                parsed_intent = (
                    ParsedStudentIntent(

                        intent=(
                            StudentIntent.ACTION_CONFIRMATION
                        ),

                        start_date=None,

                        end_date=None,

                        target_modules=[],

                        confidence=1.0,

                        original_query=query,
                    )
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

                    intent_latency_ms=0,

                    tool_latency_ms=0,

                    summarizer_latency_ms=0,
                )

                return {

                    "success": True,

                    "query":
                        query,

                    "data":
                        {},

                    "summary":
                        summary,
                }

            else:

                # ==========================================
                # INTENT PARSING
                # ==========================================

                intent_start = (
                    time.perf_counter()
                )

                parsed_intent = (
                    await parse_intent(
                        query=query,
                        role=context.role,
                    )
                )

                parsed_intent = (
                    DateService.validate(
                        parsed_intent,
                        query=query,
                    )
                )

                intent_latency_ms = int(
                    (
                        time.perf_counter()
                        - intent_start
                    )
                    * 1000
                )

        else:

            # ==========================================
            # INTENT PARSING
            # ==========================================

            intent_start = (
                time.perf_counter()
            )

            parsed_intent = (
                await parse_intent(
                    query=query,
                    role=context.role,
                )
            )

            parsed_intent = (
                DateService.validate(
                    parsed_intent,
                    query=query,
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
            "Parsed Intent: %s",
            parsed_intent.model_dump()
        )

        # ==================================================
        # UNKNOWN INTENT SHORT CIRCUIT
        # ==================================================

        if (
            parsed_intent.intent
            ==
            StudentIntent.UNKNOWN
        ):

            summary = (
                build_unknown_intent_summary(
                    "student"
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
        # SELECT TOOLS
        # ==================================================

        selected_tools = (
            get_tools_for_intent(
                intent=parsed_intent.intent
            )
        )

        logger.info(
            "Selected Tools: %s",
            selected_tools
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
                    tool_name
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

            results[tool_name] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result
            )

        # ==================================================
        # ACTION REQUIRED SHORT CIRCUIT
        # ==================================================

        for tool_result in results.values():

            if (
                isinstance(
                    tool_result,
                    dict,
                )
                and
                tool_result.get(
                    "action_required"
                )
            ):

                summary = (
                    tool_result.get(
                        "confirmation_message"
                    )
                    or ""
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

                    summarizer_latency_ms=0,
                )

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

                    "action_required":
                        True,

                    "confirmation_required":
                        tool_result.get(
                            "confirmation_required",
                            False,
                        ),

                    "action_type":
                        tool_result.get(
                            "action_type"
                        ),
                }

        # ==================================================
        # SCREEN NAVIGATION SHORT CIRCUIT
        # ==================================================

        if (
            parsed_intent.intent
            ==
            StudentIntent.SCREEN_NAVIGATION
        ):

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

                summary="",

                total_latency_ms=(
                    total_latency_ms
                ),

                intent_latency_ms=(
                    intent_latency_ms
                ),

                tool_latency_ms=(
                    tool_latency_ms
                ),

                summarizer_latency_ms=0,
            )

            return {

                "success": True,

                "query":
                    query,

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    results,

                "summary":
                    None,
            }

        # ==================================================
        # SUMMARIZER
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
            "Summarizer completed."
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