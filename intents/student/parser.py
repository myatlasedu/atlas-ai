import logging

from llm.client import (
    chat_completion
)

from intents.student.schemas import (
    ParsedStudentIntent
)

from intents.student.prompts import (
    get_student_intent_prompt
)

from intents.base.parser import (
    parse_llm_json
)

from intents.base.fallbacks import (
    build_fallback_student_intent
)

logger = logging.getLogger(__name__)


async def parse_student_intent(
    query: str
) -> ParsedStudentIntent:

    response = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": get_student_intent_prompt()
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    content = response["message"]["content"]

    logger.info(
        "RAW INTENT RESPONSE: %s",
        content
    )

    try:

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Parsed intent json: %s",
            parsed
        )

        # =====================================
        # INTENT NORMALIZATION
        # =====================================

        intent = parsed.get(
            "intent"
        )

        if (
            intent
            ==
            "event_summary"
        ):

            parsed["intent"] = (
                "personal_event_summary"
            )

        elif (
            intent
            ==
            "event_create"
        ):

            parsed["intent"] = (
                "personal_event_create"
            )

        elif (
            intent
            ==
            "event_confirmation"
        ):

            parsed["intent"] = (
                "action_confirmation"
            )

        logger.info(
            "Normalized intent: %s",
            parsed.get(
                "intent"
            )
        )

        parsed[
            "original_query"
        ] = query

        return ParsedStudentIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Intent parsing failed"
        )

        fallback = (
            build_fallback_student_intent()
        )

        fallback[
            "original_query"
        ] = query

        return ParsedStudentIntent(
            **fallback
        )