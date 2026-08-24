import logging

from datetime import timedelta, datetime, date

from llm.client import (
    chat_completion
)

from intents.base.parser import (
    parse_llm_json
)

from intents.guardian.classifier import (
    classify_guardian_intent
)

from intents.guardian.enums import (
    GuardianIntent
)

from intents.guardian.prompts import (
    get_guardian_intent_prompt
)

from intents.guardian.schemas import (
    ParsedGuardianIntent
)

from utils import (
    resolve_dates,
    ist_today
)

logger = logging.getLogger(__name__)


VALID_INTENTS = {

    item.value

    for item

    in GuardianIntent
}

VALID_HOMEWORK_FOCUS = {
    "topic_status",
    "pending",
    "overdue",
    "due_today",
    "due_tomorrow",
    "submitted",
    "graded",
    "feedback",
    "due_range",
    "next_up",
    "general",
}


def normalize_homework_focus(
    parsed: dict,
    intent: str,
) -> dict:

    focus = parsed.get(
        "homework_focus",
        None,
    )

    if focus:

        focus = (
            str(focus)
            .strip()
            .lower()
        )

        if focus not in VALID_HOMEWORK_FOCUS:

            focus = None

    parsed["homework_focus"] = focus

    #
    # A named title without an explicit focus is always
    # a question about THAT homework's status/details.
    #

    if (
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
        and
        not focus
        and
        parsed.get(
            "topic",
            None,
        )
    ):

        parsed["homework_focus"] = (
            "topic_status"
        )

    #
    # "This week" is deterministic: Monday to Sunday of
    # the current week, regardless of LLM output.
    #

    if (
        parsed.get("homework_focus")
        ==
        "due_range"
        and
        "this week" in (
            parsed.get("original_query", "")
            .lower()
        )
    ):

        today = ist_today()

        monday = today - timedelta(
            days=today.weekday()
        )

        sunday = monday + timedelta(days=6)

        parsed["start_date"] = monday.isoformat()

        parsed["end_date"] = sunday.isoformat()

    return parsed

async def normalize_dates(
    parsed: dict,
) -> dict:

    parsed = await resolve_dates(
        parsed
    )

    for field in (
        "start_date",
        "end_date",
    ):

        value = parsed.get(field)

        if hasattr(
            value,
            "isoformat",
        ):
            parsed[field] = value.isoformat()

        elif isinstance(
            value,
            str,
        ):

            try:

                parsed[field] = (
                    date.fromisoformat(
                        value
                    )
                    .isoformat()
                )

            except ValueError:

                parsed[field] = None

    return parsed

async def parse_guardian_intent(
    query: str
) -> ParsedGuardianIntent:

    try:

        classified_intent = (
            await classify_guardian_intent(
                query
            )
        )

        logger.info(
            "Guardian classified intent: %s",
            classified_intent.value
        )

        response = await chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": get_guardian_intent_prompt(
                        classified_intent
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            expect_json=True
        )

        content = (
            response["message"]["content"]
        )

        logger.info(
            "GUARDIAN RAW RESPONSE >>> %r",
            content
        )

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Guardian parsed JSON >>> %s",
            parsed
        )

        intent = (
            str(
                parsed.get(
                    "intent",
                    classified_intent.value
                )
            )
            .strip()
            .lower()
        )

        if intent not in VALID_INTENTS:

            logger.warning(
                "Unknown guardian intent '%s'. Falling back to classifier intent.",
                intent
            )

            intent = (
                classified_intent.value
            )

        # ------------------------------------------------------
        # Narrow safety net: marks FOR a specific homework /
        # assignment / worksheet must route to homework_summary,
        # never assessment_summary. Only applies when the
        # parser set asks_for_marks AND a specific topic title.
        # ------------------------------------------------------

        if (
            intent
            ==
            GuardianIntent.ASSESSMENT_SUMMARY.value
            and
            parsed.get(
                "asks_for_marks",
                False,
            )
            and
            parsed.get(
                "topic",
                None,
            )
        ):

            logger.info(
                "Reclassifying guardian assessment intent to homework_summary: %r",
                query,
            )

            intent = (
                GuardianIntent.HOMEWORK_SUMMARY.value
            )

        # ------------------------------------------------------
        # Narrow safety net: the classifier occasionally labels
        # submission-status questions about a specific homework
        # as unknown. When the parameter model still produced a
        # homework topic, route them to homework_summary so the
        # titled lookup can answer from real data.
        # ------------------------------------------------------

        if (
            intent
            ==
            GuardianIntent.UNKNOWN.value
            and
            parsed.get(
                "topic",
                None,
            )
        ):

            logger.info(
                "Reclassifying guardian unknown intent with homework topic to homework_summary: %r",
                query,
            )

            intent = (
                GuardianIntent.HOMEWORK_SUMMARY.value
            )

        parsed["intent"] = intent
        
        parsed["original_query"] = query
        parsed = await normalize_dates( parsed )

        parsed = normalize_homework_focus(
            parsed,
            intent
        )

        parsed.setdefault(
            "target_modules",
            []
        )

        parsed.setdefault(
            "confidence",
            0.95
        )


        return ParsedGuardianIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Guardian intent parsing failed."
        )

        return ParsedGuardianIntent(

            intent=GuardianIntent.UNKNOWN.value,

            target_modules=[],

            confidence=0.0,

            original_query=query
        )