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

from schemas.conversation import (
    DATE_PARAMETERS,
    QueryResolution,
)

from services.conversation_context_service import (
    ConversationContextService,
)

from services.query_resolution_service import (
    QueryResolutionService,
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
    # CONTEXT RESOLUTION + INTENT PARSING
    # ==================================================

    async def _resolve_and_parse(
        self,
        *,
        query: str,
        context,
    ):

        #
        # Runs BEFORE intent detection:
        #
        #   1. load the last few relevant turns from the audit log
        #   2. rewrite a follow-up into a standalone query
        #   3. classify + extract parameters on that standalone query
        #   4. fill any gap the follow-up left from the prior turn
        #
        # Returns (parsed_intent, resolution, latency_ms). When the
        # resolution needs a clarification, parsed_intent is None
        # and the caller must ask instead of answering.
        #

        intent_start = (
            time.perf_counter()
        )

        turns = (
            await ConversationContextService.load_recent_turns(
                context=context
            )
        )

        resolution = (
            await QueryResolutionService.resolve(
                query=query,
                context=context,
                turns=turns,
            )
        )

        if resolution.clarification_required.required:

            return (
                None,
                resolution,
                int(
                    (
                        time.perf_counter()
                        - intent_start
                    )
                    * 1000
                ),
            )

        parsed_intent = await parse_intent(

            query=resolution.resolved_query,

            role=context.role,

            enrollment_id=context.enrollment_id,

            forced_intent=(
                resolution.intent
                if resolution.inherited_intent
                else None
            ),

            raw_query=query,
        )

        parsed_intent = self._apply_resolution(
            parsed_intent=parsed_intent,
            resolution=resolution,
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

        return (
            parsed_intent,
            resolution,
            intent_latency_ms,
        )

    @staticmethod
    def _apply_resolution(
        *,
        parsed_intent,
        resolution: QueryResolution,
    ):

        #
        # Overlays the carried-over parameters onto the freshly
        # parsed intent.
        #
        # Anything the user restated in this turn wins: the parser
        # saw the standalone query, so a value it produced came
        # from the user, not from context. Only the gaps are filled
        # from the previous turn.
        #
        # Dates are the exception: the resolver computes them in
        # the user's timezone, which the parser's IST-based
        # helpers cannot do, so a resolved window overrides.
        #

        overrides = {}

        inherited_fields = []

        for field, value in resolution.parameters.items():

            if not hasattr(
                parsed_intent,
                field,
            ):

                continue

            if field in DATE_PARAMETERS:

                continue

            current = getattr(
                parsed_intent,
                field,
            )

            if current not in (
                None,
                "",
                [],
                False,
            ):

                continue

            overrides[field] = value

            inherited_fields.append(
                field
            )

        # ----------------------------------------------
        # Timezone-resolved window
        # ----------------------------------------------

        start = resolution.parameters.get(
            "start_date"
        )

        end = resolution.parameters.get(
            "end_date"
        )

        if (
            start
            and end
            and not parsed_intent.invalid_date
        ):

            overrides["start_date"] = start

            overrides["end_date"] = end

            inherited_fields.extend(
                [
                    "start_date",
                    "end_date",
                ]
            )

        # ----------------------------------------------
        # Provenance
        # ----------------------------------------------

        context_used = (
            resolution.context_used.model_dump()
        )

        context_used["resolution_latency_ms"] = (
            resolution.latency_ms
        )

        overrides["resolved_query"] = (
            resolution.resolved_query
        )

        overrides["inherited_intent"] = (
            resolution.inherited_intent
        )

        overrides["context_used"] = context_used

        overrides["inherited_parameters"] = (
            inherited_fields
        )

        if inherited_fields:

            logger.info(
                "Inherited parameters from context: %s",
                inherited_fields,
            )

        # Rebuilding (rather than setattr) runs pydantic
        # validation, so ISO strings become real dates.

        return type(parsed_intent)(
            **{
                **parsed_intent.model_dump(),
                **overrides,
            }
        )

    # ==================================================
    # CLARIFICATION
    # ==================================================

    def _clarification_response(
        self,
        *,
        query: str,
        context,
        resolution: QueryResolution,
        request_start: float,
        intent_latency_ms: int,
    ):

        summary = (
            resolution.clarification_required.question
        )

        context_used = (
            resolution.context_used.model_dump()
        )

        context_used["resolution_latency_ms"] = (
            resolution.latency_ms
        )

        parsed_intent = ParsedStudentIntent(

            intent="clarification_required",

            start_date=None,

            end_date=None,

            target_modules=[],

            confidence=0.0,

            original_query=(
                resolution.resolved_query
            ),

            raw_query=query,

            resolved_query=(
                resolution.resolved_query
            ),

            context_used=context_used,
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

        logger.info(
            "Clarification requested: %s",
            summary,
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

            "clarification_required":
                True,

            "resolution":
                resolution.contract(),
        }

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
        print("=======In student_ai_services======")
        print("At 547")
        print("Normalize Query: ", normalized_query)
        # ==================================================
        # DEFAULT AUDIT VALUES
        # ==================================================

        parsed_intent = None

        resolution = QueryResolution.passthrough(
            query,
            reason="Resolution not reached for this turn.",
        )
        print("At 559")
        print("resolution: ", normalized_query)
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
            print("At 584: Pending Action Confirm")
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

                    "resolution":
                        resolution.contract(),
                }

            else:
                print("At 711: After Pending action cofirmation")
                # ==========================================
                # CONTEXT RESOLUTION + INTENT PARSING
                # ==========================================

                (
                    parsed_intent,
                    resolution,
                    intent_latency_ms,
                ) = await self._resolve_and_parse(
                    query=query,
                    context=context,
                )
                # print("At 724, Parsed_Intent: ", parse_intent)
                print("At 725, RESOLUTION: ", resolution)

                if parsed_intent is None:
                    print("*******No intent Parse******")
                    return self._clarification_response(
                        query=query,
                        context=context,
                        resolution=resolution,
                        request_start=request_start,
                        intent_latency_ms=(
                            intent_latency_ms
                        ),
                    )

        else:
            print("\nAt 740, No pending Action involve")
            # ==========================================
            # CONTEXT RESOLUTION + INTENT PARSING
            # ==========================================

            (
                parsed_intent,
                resolution,
                intent_latency_ms,
            ) = await self._resolve_and_parse(
                query=query,
                context=context,
            )
            print("At 753, RESOLUTION: ", resolution)
            if parsed_intent is None:
                print("*******No intent Parse******")
                return self._clarification_response(
                    query=query,
                    context=context,
                    resolution=resolution,
                    request_start=request_start,
                    intent_latency_ms=(
                        intent_latency_ms
                    ),
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
            print("****Unknown Intent found****")
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

                "resolution":
                    resolution.contract(),
            }

        # ==================================================
        # SELECT TOOLS
        # ==================================================
        print(f'****{parsed_intent.intent} found****')
        selected_tools = (
            get_tools_for_intent(
                intent=parsed_intent.intent
            )
        )
        print("\n SELECTED TOOLS: ")
        print(selected_tools)
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
            print("****Tool name****: ", tool)
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

                    "resolution":
                        resolution.contract(),
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

                "resolution":
                    resolution.contract(),
            }

        # ==================================================
        # SUMMARIZER
        # ==================================================

        summarizer_start = (
            time.perf_counter()
        )
        print("\n****Go for summary At 1078****")
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

            "resolution":
                resolution.contract(),
        }