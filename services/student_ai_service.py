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
import time

import random

PROMPT_CATEGORIES = {

    "Atlas Score": [

        "Show my Atlas score.",
        "How can I improve my Atlas score?",
        "Which Atlas pillar needs the most improvement?",
    ],

    "Performance": [

        "How am I doing overall?",
        "Which subject needs the most attention?",
        "Compare my subjects.",
    ],

    "Topics": [

        "Show completed topics.",
        "Which topics are still pending?",
        "Which topics am I weak in?",
    ],

    "Homework": [

        "What homework is due today?",
        "Show my homework this week.",
        "Do I have any overdue homework?",
    ],

    "Assessments": [

        "Show my upcoming assessments.",
        "How did I perform in my recent assessments?",
        "Which assessment affected my performance the most?",
    ],

    "Attendance": [

        "Show my attendance this month.",
        "How consistent has my attendance been?",
    ],

    "Timetable": [

        "What classes do I have today?",
        "Show tomorrow's timetable.",
    ],

    "Journal": [

        "Show my journal.",
        "Show my journal from last week.",
        "Save this in my journal: Today I finally understood quadratic equations.",
        "Journal this: Today was a productive day.",
        "Today I learned how to solve simultaneous equations. Save this in my journal.",
        "Journal my goal to complete homework before dinner every day."
        # "Show my journal about Mathematics.",
    ],

    "Announcements": [
        "Show recent announcements.",
        # "Did I miss any announcements this week?",
    ],
}

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
                
                t0 = time.perf_counter()
                parsed_intent = await parse_intent(
                    query=query,
                    role=context.role
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
                role=context.role
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
        # UNKNOWN INTENT SHORT CIRCUIT
        # =====================================

        if (
            parsed_intent.intent
            ==
            StudentIntent.UNKNOWN
        ):
            examples = []

            for category, prompts in PROMPT_CATEGORIES.items():

                examples.append(
                    (
                        category,
                        random.choice(prompts),
                    )
                )

            summary = (
                "I'm not quite sure what you're looking for.\n\n"
                "Atlas can help with many aspects of your academic journey. "
                "Here are a few things you can try:\n\n"
            )

            for category, prompt in examples:

                summary += (
                    f"{category}\n"
                    f"• {prompt}\n\n"
                )

            summary += (
                "You don't need to use these exact phrases—"
                "you can ask naturally, and I'll do my best to understand."
            )
            return {

                "success": True,

                "query":
                    query,

                "intent":
                    parsed_intent.model_dump(),

                "data":
                    {},

                "summary": summary
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
            t0 = time.perf_counter()
            result = await tool.run(
                context=context,
                parsed_intent=parsed_intent
            )
            t1 = time.perf_counter()

            print(f"Tool Time: {t1-t0:.2f}s")
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
        t0 = time.perf_counter()
        summary = await summarize_response(
            query=query,
            data=results,
            context=context,
            intent=parsed_intent.intent
        )
        t1 = time.perf_counter()

        print(f"Summarize Time: {t1-t0:.2f}s")
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