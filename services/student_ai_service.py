import asyncio
import logging
import time

from datetime import (
    datetime,
    timezone,
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

from services.context_service import (
    ConversationContextService,
)

from services.date_service import (
    DateService,
)

from cache.pending_action_cache import (
    PendingActionCache,
)

from cache.conversation_cache import (
    ConversationCache,
)

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)

from utils import (
    process_and_sanitize_grades,
)


from services.chat_session_service import (
    ChatSessionService,
    current_turn,
)

from services.session_memory_service import (
    SessionMemoryService,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
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

        turn = current_turn.get()

        predicted_intent = (
            parsed_intent.intent.value
            if isinstance(
                parsed_intent.intent,
                StudentIntent,
            )
            else str(
                parsed_intent.intent
            )
        )

        # The next turn reads its context from Redis, so the
        # cache is written before the slower audit insert.

        await ConversationCache.append(
            getattr(
                turn,
                "session_id",
                None,
            ),
            {
                "turn_id": getattr(
                    turn,
                    "session_id",
                    None,
                ),

                "query": query,

                "predicted_intent": predicted_intent,

                "parsed_intent": (
                    parsed_intent.model_dump()
                ),

                "selected_tools": selected_tools,

                "summary": summary or "",

                "created_at": datetime.now(
                    timezone.utc
                ),
            },
        )

        try:

            async with AsyncSessionLocal() as db:

                await self.audit_repository.create(

                    db=db,

                    user_id=context.user_id,

                    role=context.role,

                    query=query,

                    predicted_intent=predicted_intent,

                    parsed_intent=(
                        parsed_intent.model_dump()
                    ),

                    context_resolution=(
                        getattr(
                            parsed_intent,
                            "context_resolution",
                            None,
                        )
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
    # SESSION MEMORY (ACTIONS)
    # ==================================================

    @staticmethod
    async def _remember_pending_action(
        *,
        query: str,
        tool_result: dict,
    ):

        turn = current_turn.get()

        try:

            await SessionMemoryService.record_pending(
                getattr(turn, "session_id", None),
                action_type=tool_result.get("action_type"),
                payload=SessionMemoryService.payload_from_result(
                    tool_result
                ),
                query=query,
                turn_id=getattr(turn, "session_id", None),
            )

        except Exception:

            logger.exception(
                "Failed to record pending action in session memory."
            )

    @staticmethod
    async def _remember_resolved_action(
        *,
        query: str,
        action_type: str | None,
        status: str,
        payload: dict | None = None,
    ):

        turn = current_turn.get()

        try:

            await SessionMemoryService.resolve_pending(
                getattr(turn, "session_id", None),
                action_type=action_type,
                status=status,
                payload=payload,
                turn_id=getattr(turn, "session_id", None),
                query=query,
            )

        except Exception:

            logger.exception(
                "Failed to resolve action in session memory."
            )

    # ==================================================
    # ANSWER
    # ==================================================

    async def answer(
        self,
        query: str,
        context,
        session_id: int,
    ):

        turn = ChatSessionService.start_turn(
            session_id=session_id,
        )
        print("\n====Turn====\n", turn)
        token = current_turn.set(
            turn
        )

        try:

            response = await self._answer(
                query=query,
                context=context,
                session_id=session_id,
            )

        finally:

            current_turn.reset(
                token
            )

        response["session_id"] = session_id

        return response

    async def _answer(
        self,
        query: str,
        context,
        session_id: int,
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
        # CONVERSATION CONTEXT
        # ==================================================

        recent_turns = (
            await ConversationContextService.load_recent_turns(
                session_id=session_id,
            )
        )

        # ==================================================
        # CONFIRMATION SHORT CIRCUIT
        # ==================================================

        pending_action = (
            await PendingActionCache.get(
                context.user_id,
                session_id=session_id,
            )
        )

        if pending_action:

            if normalized_query.strip("?!., ") in [

                "yes",
                "y",
                "yeah",
                "yep",
                "yup",
                "sure",
                "yes please",
                "confirm",
                "ok",
                "okay",
                "proceed",
                "go ahead",
                "do it",
                "create it",
                "save it",
                "yes create it",
                "yes save it",
                "yes do it",
                "ok create it",
                "okay create it",
                "ok save it",
                "okay save it",
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

            elif normalized_query.strip("?!., ") in [

                "no",
                "n",
                "nope",
                "cancel",
                "stop",
                "don't",
                "dont",
                "never mind",
                "nevermind",
                "no thanks",
                "cancel it",
            ]:

                await PendingActionCache.delete(
                    context.user_id,
                    session_id=session_id,
                )

                cancelled_action_type = pending_action.get(
                    "action_type"
                )

                await self._remember_resolved_action(
                    query=query,
                    action_type=cancelled_action_type,
                    status=STATUS_CANCELLED,
                )


                cancel_results = {
                    "action_executor_tool": {
                        "module": "action",
                        "action_cancelled": True,
                        "action_type": cancelled_action_type,
                        "payload": pending_action.get(
                            "payload",
                            {},
                        ),
                    }
                }

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

                    tool_results=cancel_results,

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

                    "session_id":
                        session_id,

                    "role":
                        context.role,

                    "query":
                        query,

                    "summary":
                        summary,

                    "parsed_intent":
                        parsed_intent.model_dump(),

                    "selected_tools":
                        [],

                    "context_resolution":
                        None,

                    "status":
                        "completed",

                    "data":
                        {},
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
                        enrollment_id=context.enrollment_id,
                        turns=recent_turns,
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
                    enrollment_id=context.enrollment_id,
                    turns=recent_turns,
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

                "session_id":
                    session_id,

                "role":
                    context.role,

                "query":
                    query,

                "summary":
                    summary,

                "parsed_intent":
                    parsed_intent.model_dump(),

                "selected_tools":
                    [],

                "context_resolution":
                    getattr(
                        parsed_intent,
                        "context_resolution",
                        None,
                    ),

                "status":
                    "completed",

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    {},
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

            result = process_and_sanitize_grades(result)

            results[tool_name] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result
            )

        # ==================================================
        # SESSION MEMORY: EXECUTED ACTION
        # ==================================================

        executed = results.get(
            "action_executor_tool"
        )

        if (
            isinstance(
                executed,
                dict,
            )
            and
            executed.get(
                "action_completed"
            )
        ):

            await self._remember_resolved_action(
                query=query,
                action_type=executed.get("action_type"),
                status=STATUS_COMPLETED,
                payload=executed.get("payload"),
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

                await self._remember_pending_action(
                    query=query,
                    tool_result=tool_result,
                )

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

                    "session_id":
                        session_id,

                    "role":
                        context.role,

                    "query":
                        query,

                    "summary":
                        summary,

                    "parsed_intent":
                        parsed_intent.model_dump(),

                    "selected_tools":
                        selected_tools,

                    "context_resolution":
                        getattr(
                            parsed_intent,
                            "context_resolution",
                            None,
                        ),

                    "status":
                        "completed",

                    "intent":
                        parsed_intent.model_dump(),

                    "data":
                        results,

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

                "session_id":
                    session_id,

                "role":
                    context.role,

                "query":
                    query,

                "summary":
                    None,

                "parsed_intent":
                    parsed_intent.model_dump(),

                "selected_tools":
                    selected_tools,

                "context_resolution":
                    getattr(
                        parsed_intent,
                        "context_resolution",
                        None,
                    ),

                "status":
                    "completed",

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    results,
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

            "session_id":
                session_id,

            "role":
                context.role,

            "query":
                query,

            "summary":
                summary,

            "parsed_intent":
                parsed_intent.model_dump(),

            "selected_tools":
                selected_tools,

            "context_resolution":
                getattr(
                    parsed_intent,
                    "context_resolution",
                    None,
                ),

            "status":
                "completed",

            "intent":
                parsed_intent.model_dump(),

            "data":
                results,
        }