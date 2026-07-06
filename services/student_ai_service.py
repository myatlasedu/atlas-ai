import logging

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

logger = logging.getLogger(__name__)


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
        # CONFIRMATION SHORT CIRCUIT
        # =====================================

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

                parsed_intent = await parse_intent(
                    query=query,
                    role=context.role
                )

                parsed_intent = (
                    DateService.validate(
                        parsed_intent
                    )
                )

        else:

            parsed_intent = await parse_intent(
                query=query,
                role=context.role
            )

            parsed_intent = (
                DateService.validate(
                    parsed_intent
                )
            )

        logger.info(
            "Parsed Intent: %s",
            parsed_intent.model_dump()
        )

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
                    (
                        "I couldn't determine "
                        "what information you "
                        "are looking for."
                    )
            }

        tools_to_run = get_tools_for_intent(
            intent=parsed_intent.intent
        )

        logger.info(
        "Mentor tools: %s",
        tools_to_run
    )

        logger.info(
            "Selected Tools: %s",
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

            results[tool_name] = result

            logger.info(
                "Tool result [%s]: %s",
                tool_name,
                result
            )

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