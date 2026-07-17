import logging

from intents.guardian.parser import (
    parse_guardian_intent
)

from intents.guardian.enums import (
    GuardianIntent
)

from routing.guardian_tool_router import (
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

from intents.common.prompt_categories import (
    build_unknown_intent_summary,
)

logger = logging.getLogger(__name__)


class GuardianAIService:

    async def answer(
        self,
        query: str,
        context
    ):

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

        logger.info(
            "Parsed Guardian Intent: %s",
            parsed_intent.model_dump()
        )

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
                    build_unknown_intent_summary("guardian"),
            }

        # =====================================
        # TOOL SELECTION
        # =====================================

        tools_to_run = get_tools_for_intent(
            intent=parsed_intent.intent
        )

        logger.info(
            "Guardian tools: %s",
            tools_to_run
        )

        results = {}

        for tool_name in tools_to_run:

            tool = TOOL_REGISTRY.get(
                tool_name
            )

            if tool is None:

                logger.warning(
                    "Tool not found: %s",
                    tool_name
                )

                continue

            result = await tool.run(

                context=context,

                parsed_intent=parsed_intent
            )

            results[
                tool_name
            ] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result
            )

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
        # SUMMARY
        # =====================================

        # if direct_answer:

        #     logger.info(
        #         "Using direct answer: %s",
        #         direct_answer
        #     )

        #     summary = direct_answer

        # else:

        summary = await summarize_response(

            query=query,

            data=results,

            context=context,

            intent=parsed_intent.intent
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
                summary
        }