import asyncio
import logging
import time

from asyncio import (
    gather,
)

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

from cache.response_cache import (
    ResponseCache,
)

from cache.conversation_cache import (
    ConversationCache,
)

from schemas.conversation import (
    ConversationTurn,
)

from services.conversation_manager import (
    conversation_scope_key,
    resolve as resolve_conversation,
    label as conversation_label,
    build_prior_context,
    normalize_intent,
)

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)

from services.intent_audit_service import (
    IntentAuditService,
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

        if task.cancelled():

            return

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

        # =====================================
        # CONVERSATION SESSION LOAD
        # =====================================

        scope_key = conversation_scope_key(context)

        session = None

        if scope_key:

            session = await ConversationCache.get(
                scope_key
            )

        rev = (
            session.rev
            if session
            else 0
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

        # =====================================
        # RESPONSE CACHE CHECK (only when no pending action)
        # =====================================

        if not pending_action:

            cached = (
                await ResponseCache.get(
                    context=context,
                    query=query,
                    rev=rev,
                    session_marker=(
                        session.session_id
                        if session
                        else None
                    ),
                )
            )

            if cached is not None:

                logger.info(
                    "CACHE HIT - returning cached response"
                )

                return cached

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

                intent_start = (
                    time.perf_counter()
                )

                parsed_intent = await parse_intent(
                    query=query,
                    role=context.role,
                    prior_context=(
                        build_prior_context(session)
                        if session
                        else None
                    ),
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

        else:

            intent_start = (
                time.perf_counter()
            )

            parsed_intent = await parse_intent(
                query=query,
                role=context.role,
                prior_context=(
                    build_prior_context(session)
                    if session
                    else None
                ),
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
            "Parsed Intent: %s",
            parsed_intent.model_dump()
        )

        # =====================================
        # AI CONVERSATION CATCHER
        # =====================================

        await IntentAuditService.capture(
            query=query,
            context=context,
            parsed_intent=parsed_intent,
        )

        # =====================================
        # GUARDRAIL SHORT CIRCUITS
        # =====================================

        is_injection = getattr(
            parsed_intent,
            "is_injection",
            False,
        )

        is_content_gen = getattr(
            parsed_intent,
            "generate_content",
            False,
        )

        if is_injection:

            logger.warning(
                "Prompt injection detected. Refusing query: %s",
                query,
            )

        if is_content_gen:

            logger.info(
                "Content-generation request. Refusing query: %s",
                query,
            )

        if (
            is_injection
            or
            is_content_gen
        ):

            parsed_intent.intent = (
                StudentIntent.UNKNOWN
            )

        # =====================================
        # CONVERSATION CONTEXT RESOLUTION
        # =====================================

        resolution = await resolve_conversation(
            context=context,
            parsed_intent=parsed_intent,
            query=query,
            session=session,
        )

        if resolution.is_continuation:

            parsed_intent.intent = (
                resolution.session.current_intent
            )

            logger.info(
                "Continuation fallback - intent set to %s",
                parsed_intent.intent,
            )

        if resolution.is_switch:

            logger.info(
                "Intent switch detected - answering with switch notice"
            )

            switch_notice = (
                f"You switched from "
                f"{conversation_label(resolution.switched_from)} to "
                f"{conversation_label(parsed_intent.intent)} topic. "
                "A new session has started.\n\n"
            )

        else:

            switch_notice = None

        # =====================================
        # UNKNOWN INTENT SHORT CIRCUIT
        # =====================================

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

        # =====================================
        # TOOL SELECTION
        # =====================================

        tools_to_run = (
            get_tools_for_intent(
                intent=parsed_intent.intent
            )
        )

        selected_tools = tools_to_run

        logger.info(
            "Selected Tools: %s",
            tools_to_run,
        )

        async def _run_tool(
            tool_name,
        ):

            tool = TOOL_REGISTRY.get(
                tool_name
            )

            if tool is None:

                logger.warning(
                    "Tool not found: %s",
                    tool_name,
                )

                return (
                    tool_name,
                    None,
                )

            t0 = time.perf_counter()

            try:

                result = await tool.run(
                    context=context,
                    parsed_intent=parsed_intent,
                )

            except Exception as e:

                logger.exception(
                    "Tool [%s] failed: %s",
                    tool_name,
                    e,
                )

                result = {

                    "module":
                        tool_name,

                    "error":
                        str(e),

                    "direct_answer":
                        (
                            "Unable to load "
                            "this information."
                        ),
                }

            t1 = time.perf_counter()

            tool_latency_current = int(
                (t1 - t0) * 1000
            )

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result,
            )

            return (
                tool_name,
                result,
                tool_latency_current,
            )

        outcomes = await gather(
            *[
                _run_tool(
                    tool_name,
                )
                for tool_name in tools_to_run
            ]
        )

        results = {}

        for (
            tool_name,
            result,
            latency,
        ) in outcomes:

            tool_latency_ms += latency

            if result is not None:

                results[
                    tool_name
                ] = result

        # =====================================
        # ACTION REQUIRED SHORT CIRCUIT
        # =====================================

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

        # =====================================
        # SCREEN NAVIGATION SHORT CIRCUIT
        # =====================================

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

        # =====================================
        # SUMMARIZER
        # =====================================

        summarizer_start = (
            time.perf_counter()
        )

        summary = await summarize_response(

            query=query,

            data=results,

            context=context,

            intent=parsed_intent.intent,

            history=resolution.prior_context,
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

        if switch_notice:

            summary = (
                switch_notice
                + (summary or "")
            )

        response = {

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

        if switch_notice:

            response["intent_switched"] = True

        if (
            scope_key
            and
            resolution.session is not None
        ):

            turn = ConversationTurn(
                user_query=query,
                assistant_summary=summary or "",
                intent=normalize_intent(
                    parsed_intent.intent
                ),
                target_modules=getattr(
                    parsed_intent,
                    "target_modules",
                    [],
                ) or [],
                start_date=getattr(
                    parsed_intent,
                    "start_date",
                    None,
                ),
                end_date=getattr(
                    parsed_intent,
                    "end_date",
                    None,
                ),
            )

            resolution.session = await ConversationCache.add_turn(
                scope_key,
                resolution.session,
                turn,
            )

        await ResponseCache.set(
            context=context,
            query=query,
            response=response,
            rev=(
                resolution.session.rev
                if resolution.session
                else 0
            ),
            session_marker=(
                resolution.session.session_id
                if resolution.session
                else None
            ),
        )

        # =====================================
        # FINAL AUDIT
        # =====================================

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

        return response