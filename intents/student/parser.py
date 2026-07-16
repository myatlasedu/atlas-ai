import logging

from llm.client import (
    chat_completion,
)

from intents.base.fallbacks import (
    build_fallback_student_intent,
)

from intents.base.parser import (
    parse_llm_json,
)

from intents.student.classifier import (
    classify_student_intent,
)

from intents.student.enums import (
    StudentIntent,
)

from intents.student.prompts import (
    get_student_intent_prompt,
)

from intents.student.schemas import (
    ParsedStudentIntent,
)

from utils import (
    resolve_dates,
)

logger = logging.getLogger(__name__)


INTENT_ALIASES = {

    "homework":
        StudentIntent.HOMEWORK_SUMMARY.value,

    "attendance":
        StudentIntent.ATTENDANCE_SUMMARY.value,

    "assessment":
        StudentIntent.ASSESSMENT_SUMMARY.value,

    "atlas":
        StudentIntent.ATLAS_SCORE_SUMMARY.value,

    "performance":
        StudentIntent.STUDENT_PERFORMANCE.value,

    "subject":
        StudentIntent.SUBJECT_SUMMARY.value,

    "topic":
        StudentIntent.TOPIC_SUMMARY.value,

    "announcement":
        StudentIntent.ANNOUNCEMENT_SUMMARY.value,

    "forum":
        StudentIntent.FORUM_SUMMARY.value,

    "journal":
        StudentIntent.JOURNAL_SUMMARY.value,

    "event":
        StudentIntent.PERSONAL_EVENT_SUMMARY.value,

    "confirmation":
        StudentIntent.ACTION_CONFIRMATION.value,

    "navigation":
        StudentIntent.SCREEN_NAVIGATION.value,
}

VALID_INTENTS = {
    item.value
    for item in StudentIntent
}


def _fallback(
    query: str,
) -> ParsedStudentIntent:

    data = build_fallback_student_intent()

    data["original_query"] = query

    return ParsedStudentIntent(
        **data
    )


def _normalize_modules(
    parsed: dict,
) -> dict:

    modules = parsed.get(
        "target_modules",
        [],
    )

    if not isinstance(
        modules,
        list,
    ):
        modules = []

    parsed["target_modules"] = list(
        dict.fromkeys(
            str(module).lower().strip()
            for module in modules
            if module
        )
    )

    return parsed


def _normalize_dates(
    parsed: dict,
) -> dict:

    parsed = resolve_dates(
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

    return parsed


async def parse_student_intent(
    query: str,
) -> ParsedStudentIntent:

    try:

        classified_intent = (
            await classify_student_intent(
                query
            )
        )

        logger.info(
            "Classified intent: %s",
            classified_intent.value,
        )

        prompt = (
            get_student_intent_prompt(
                classified_intent
            )
        )

        response = await chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ]
        )

        content = (
            response["message"]["content"]
        )

        logger.info(
            "RAW MODEL RESPONSE >>> %r",
            content,
        )

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Parsed JSON >>> %s",
            parsed,
        )

        intent = (
            str(
                parsed.get(
                    "intent",
                    classified_intent.value,
                )
            )
            .strip()
            .lower()
        )

        intent = (
            INTENT_ALIASES.get(
                intent,
                intent,
            )
        )

        if intent not in VALID_INTENTS:

            logger.warning(
                "Unknown parsed intent '%s'. Falling back to classifier intent.",
                intent,
            )

            intent = (
                classified_intent.value
            )

        parsed["intent"] = intent

        parsed.setdefault(
            "target_modules",
            [],
        )

        parsed.setdefault(
            "confidence",
            0.95,
        )

        parsed["original_query"] = query

        parsed = _normalize_dates(
            parsed
        )

        parsed = _normalize_modules(
            parsed
        )

        return ParsedStudentIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Student intent parsing failed."
        )

        return _fallback(
            query
        )