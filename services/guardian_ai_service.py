import logging

from asyncio import (
    gather,
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


class GuardianAIService:

    async def answer(
        self,
        query: str,
        context,
    ):

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

        # =====================================
        # INTENT PARSING
        # =====================================

        parsed_intent = (
            await parse_guardian_intent(
                query,
                prior_context=(
                    build_prior_context(session)
                    if session
                    else None
                ),
            )
        )

        parsed_intent = (
            DateService.validate(
                parsed_intent
            )
        )

        logger.info(
            "Parsed Guardian Intent: %s",
            parsed_intent.model_dump(),
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
                GuardianIntent.UNKNOWN
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
            GuardianIntent.UNKNOWN
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
                    build_unknown_intent_summary(
                        "guardian"
                    ),
            }

        # =====================================
        # TOOL SELECTION
        # =====================================

        tools_to_run = (
            get_tools_for_intent(
                intent=parsed_intent.intent
            )
        )

        logger.info(
            "Guardian tools: %s",
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

            try:

                result = await tool.run(
                    context=context,
                    parsed_intent=parsed_intent,
                )

            except Exception as e:

                logger.exception(
                    "Guardian tool [%s] failed: %s",
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

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result,
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
        # SUMMARY
        # =====================================

        summary = await summarize_response(
            query=query,
            data=results,
            context=context,
            intent=parsed_intent.intent,
            history=resolution.prior_context,
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

        return response
