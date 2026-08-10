import logging

from asyncio import (
    gather,
)

from intents.router import (
    parse_intent
)

from intents.student.enums import (
    StudentIntent
)

from intents.student.schemas import (
    ParsedStudentIntent
)

from routing.student_tool_router import (
    get_tools_for_intent
)

from tools.student.registry import (
    TOOL_REGISTRY
)

from llm.summarizer import (
    summarize_response
)

from services.date_service import (
    DateService
)

from cache.pending_action_cache import (
    PendingActionCache
)

from cache.response_cache import (
    ResponseCache
)

from cache.conversation_cache import (
    ConversationCache
)

from schemas.conversation import (
    ConversationTurn
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

logger = logging.getLogger(__name__)
import time

import random


class StudentAIService:

    async def answer(
        self,
        query: str,
        context
    ):

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

        # =====================================
        # CONFIRMATION SHORT CIRCUIT
        # =====================================

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
                "do it"
            ]:

                logger.info(
                    "Pending action confirmation detected"
                )

                parsed_intent = (
                    ParsedStudentIntent(

                        intent=
                            StudentIntent.ACTION_CONFIRMATION,

                        start_date=None,

                        end_date=None,

                        target_modules=[],

                        confidence=1.0,

                        original_query=query
                    )
                )

            elif normalized_query in [

                "no",
                "n",
                "cancel",
                "stop",
                "don't",
                "dont",
                "never mind"
            ]:

                await PendingActionCache.delete(
                    context.user_id
                )

                return {

                    "success": True,

                    "query":
                        query,

                    "data":
                        {},

                    "summary":
                        "The pending action has been cancelled."
                }

            else:
                
                t0 = time.perf_counter()
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
                t1 = time.perf_counter()

                print(f"Intent: {t1-t0:.2f}s")

        else:
            t0 = time.perf_counter()
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
            t1 = time.perf_counter()

            print(f"Intent: {t1-t0:.2f}s")

        logger.info(
            "Parsed Intent: %s",
            parsed_intent.model_dump()
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

            return {

                "success": True,

                "query":
                    query,

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    {},

                "summary":
                    build_unknown_intent_summary("student"),
            }

        tools_to_run = get_tools_for_intent(
            intent=parsed_intent.intent
        )


        logger.info(
            "Selected Tools: %s",
            tools_to_run
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
                    tool_name
                )

                return (
                    tool_name,
                    None,
                )

            t0 = time.perf_counter()

            try:

                result = await tool.run(
                    context=context,
                    parsed_intent=parsed_intent
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

            print(f"Tool Time: {t1-t0:.2f}s")

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result
            )

            return (
                tool_name,
                result,
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
        ) in outcomes:

            if result is not None:

                results[
                    tool_name
                ] = result

        # =====================================
        # ACTION REQUIRED SHORT CIRCUIT
        # =====================================

        for tool_result in results.values():

            if (
                isinstance(tool_result, dict)
                and
                tool_result.get(
                    "action_required"
                )
            ):

                return {

                    "success": True,

                    "query":
                        query,

                    "intent":
                        parsed_intent.model_dump(),

                    "data":
                        results,

                    "summary":
                        tool_result.get(
                            "confirmation_message"
                        ),

                    "action_required":
                        True,

                    "confirmation_required":
                        tool_result.get(
                            "confirmation_required",
                            False
                        ),

                    "action_type":
                        tool_result.get(
                            "action_type"
                        )
                }
            
        # =====================================
        # SCREEN NAVIGATION SHORT CIRCUIT
        # =====================================

        if (
            parsed_intent.intent
            ==
            StudentIntent.SCREEN_NAVIGATION
        ):

            return {

                "success": True,

                "query":
                    query,

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    results,

                "summary":
                    None
            }


        # # =====================================
        # # DIRECT ANSWER SHORT CIRCUIT
        # # =====================================

        # direct_answer = None

        # for tool_result in results.values():

        #     if not isinstance(
        #         tool_result,
        #         dict
        #     ):
        #         continue

        #     answer = tool_result.get(
        #         "direct_answer"
        #     )

        #     if answer:

        #         direct_answer = answer
        #         break

        # =====================================
        # DETERMINISTIC RESPONSE
        # =====================================

        # if direct_answer:

        #     logger.info(
        #         "Using direct answer: %s",
        #         direct_answer
        #     )

        #     summary = direct_answer

        # else:
        t0 = time.perf_counter()
        summary = await summarize_response(
            query=query,
            data=results,
            context=context,
            intent=parsed_intent.intent,
            history=resolution.prior_context,
        )
        t1 = time.perf_counter()

        print(f"Summarize Time: {t1-t0:.2f}s")

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
                summary
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

        return response