import logging

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

from services.chat_session_service import (
    ChatSessionService,
    current_turn,
)

logger = logging.getLogger(__name__)


class MentorAIService:

    async def answer(
        self,
        query: str,
        context,
        session_id: str | None = None,
    ):

        # MentorContext carries no role field, so the thread
        # is tagged explicitly.

        turn = await ChatSessionService.start_turn(
            context=context,
            query=query,
            session_id=session_id,
            role="mentor",
        )

        token = current_turn.set(
            turn
        )

        try:

            response = await self._answer(
                query=query,
                context=context,
            )

        except Exception as error:

            await ChatSessionService.fail_turn(
                turn,
                error_message=str(
                    error
                ),
            )

            raise

        finally:

            current_turn.reset(
                token
            )

        await ChatSessionService.complete_turn(
            turn,
            answer=response.get(
                "summary"
            ),
        )

        if turn is not None:

            response["session_id"] = (
                turn.session_id
            )

        return response

    async def _answer(
        self,
        query: str,
        context
    ):

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