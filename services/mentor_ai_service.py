import logging

from asyncio import (
    gather,
)

from intents.router import (
    parse_intent
)

from intents.mentor.enums import (
    MentorIntent
)

from routing.mentor_tool_router import (
    get_tools_for_intent
)

from tools.mentor.registry import (
    TOOL_REGISTRY
)

from llm.mentor_summarizer import (
    summarize_response
)

from services.date_service import (
    DateService
)

from cache.response_cache import (
    ResponseCache
)

logger = logging.getLogger(__name__)


class MentorAIService:

    async def answer(
        self,
        query: str,
        context
    ):

        cached = (
            await ResponseCache.get(
                context=context,
                query=query,
            )
        )

        if cached is not None:

            logger.info(
                "CACHE HIT - returning cached response"
            )

            return cached

        parsed_intent = await parse_intent(
            query=query,
            role="mentor"
        )

        parsed_intent = DateService.validate(
            parsed_intent
        )

        logger.info(
            "Parsed Mentor Intent: %s",
            parsed_intent.model_dump()
        )

        # =====================================
        # UNKNOWN INTENT
        # =====================================

        if (
            parsed_intent.intent
            ==
            MentorIntent.UNKNOWN
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
                    (
                        "I couldn't determine "
                        "what information you "
                        "are looking for."
                    )
            }

        # =====================================
        # TOOL ROUTING
        # =====================================

        tools_to_run = get_tools_for_intent(
            parsed_intent.intent
        )

        logger.info(
            "Selected Mentor Tools: %s",
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

            try:

                result = await tool.run(
                    context=context,
                    parsed_intent=parsed_intent
                )

            except Exception as e:

                logger.exception(
                    "Mentor tool [%s] failed: %s",
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
        # DIRECT ANSWER
        # =====================================

        direct_answer = None

        for tool_result in results.values():

            if not isinstance(
                tool_result,
                dict
            ):
                continue

            answer = tool_result.get(
                "direct_answer"
            )

            if answer:

                direct_answer = answer
                break

        # =====================================
        # SUMMARIZE
        # =====================================

        if direct_answer:

            summary = direct_answer

        else:

            summary = await summarize_response(
                query=query,
                data=results,
                context=context,
                intent=parsed_intent.intent
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

        await ResponseCache.set(
            context=context,
            query=query,
            response=response,
        )

        return response