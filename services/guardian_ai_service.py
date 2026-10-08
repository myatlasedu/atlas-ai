import asyncio
import logging
import time

from datetime import date

from sqlalchemy import text

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

from tools.guardian.attendance_tool import (
    AttendanceTool as GuardianAttendanceTool,
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

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)

from cache.conversation_recall_cache import (
    ConversationRecallCache,
)


from services.chat_session_service import (
    ChatSessionService,
    current_turn,
)

from utils import (
    process_and_sanitize_grades,
)


logger = logging.getLogger(__name__)

GUARDIAN_TOOL_OVERRIDES = {
    "attendance_tool": GuardianAttendanceTool(),
}


def get_predicted_intent(parsed_intent):
    intent = parsed_intent.intent
    return intent.value if isinstance(intent, GuardianIntent) else str(intent)


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

        predicted_intent = get_predicted_intent(parsed_intent)

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
    # CONTEXT
    # ==================================================

    @staticmethod
    async def _resolve_academic_class(
        context,
    ):

        if getattr(
            context,
            "academic_class_id",
            None,
        ):

            return

        try:

            async with AsyncSessionLocal() as db:

                result = await db.execute(
                    text(
                        """
                        SELECT academic_class_id
                        FROM students_studentenrollment
                        WHERE id = :enrollment_id
                        """
                    ),
                    {
                        "enrollment_id": context.enrollment_id,
                    },
                )

                context.academic_class_id = (
                    result.scalar_one_or_none()
                )

        except Exception:

            logger.exception(
                "Failed to resolve academic class for enrollment %s.",
                context.enrollment_id,
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
        # CONVERSATION CONTEXT
        # ==================================================

        recent_turns = (
            await ConversationContextService.load_recent_turns(
                session_id=session_id,
            )
        )

        # ==================================================
        # INTENT PARSING
        # ==================================================

        intent_start = (
            time.perf_counter()
        )

        parsed_intent = (
            await parse_guardian_intent(
                query,
                enrollment_id=context.enrollment_id,
                turns=recent_turns,
            )
        )

        parsed_intent = (
            DateService.validate(
                parsed_intent
            )
        )

        # The guardian parser keeps dates as ISO strings; the shared
        # tools and their queries need real dates, as students send.

        for field in (
            "start_date",
            "end_date",
        ):

            value = getattr(
                parsed_intent,
                field,
                None,
            )

            if isinstance(value, str):

                try:

                    setattr(
                        parsed_intent,
                        field,
                        date.fromisoformat(value),
                    )

                except ValueError:

                    setattr(
                        parsed_intent,
                        field,
                        None,
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

                "predicted_intent":
                    get_predicted_intent(parsed_intent),

                "status":
                    "completed",

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    {},
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

        await self._resolve_academic_class(
            context
        )

        for tool_name in selected_tools:

            tool = (
                GUARDIAN_TOOL_OVERRIDES.get(
                    tool_name
                )
                or TOOL_REGISTRY.get(
                    tool_name
                )
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

            result = process_and_sanitize_grades(result)

            results[
                tool_name
            ] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result,
            )

        # ==================================================
        # SCREEN NAVIGATION SHORT CIRCUIT
        # ==================================================

        if (
            parsed_intent.intent
            ==
            GuardianIntent.SCREEN_NAVIGATION
        ):

            navigation_target = parsed_intent.navigation_target

            await ConversationRecallCache.append(
                session_id,
                user_query=query,
                chatbot_summary=(
                    f"Navigated to {navigation_target}"
                    if navigation_target
                    else "Screen navigation requested."
                ),
            )

            self._schedule_audit(

                context=context,

                query=query,

                parsed_intent=parsed_intent,

                selected_tools=selected_tools,

                tool_results=results,

                summary="",

                total_latency_ms=int(
                    (
                        time.perf_counter()
                        - request_start
                    )
                    * 1000
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

                "predicted_intent":
                    get_predicted_intent(parsed_intent),

                "data":
                    results,
            }

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

            intent=get_predicted_intent(parsed_intent),
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
        # CONVERSATION RECALL CACHE
        # ==================================================

        if parsed_intent.intent not in [
            GuardianIntent.UNKNOWN,
            GuardianIntent.CONVERSATION_RECALL,
        ]:
            await ConversationRecallCache.append(
                session_id,
                user_query=query,
                chatbot_summary=summary or "",
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

            "predicted_intent":
                get_predicted_intent(parsed_intent),

            "status":
                "completed",

            "intent":
                parsed_intent.model_dump(),

            "data":
                results,
        }