import logging

from datetime import date

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

    "calendar":
        StudentIntent.CALENDAR_SUMMARY.value,

         "timetable":
        StudentIntent.TIMETABLE_SUMMARY.value,

    "schedule":
        StudentIntent.TIMETABLE_SUMMARY.value,

    "structure_of_day":
        StudentIntent.TIMETABLE_SUMMARY.value,

    "structure of the day":
        StudentIntent.TIMETABLE_SUMMARY.value,

    "sod":
        StudentIntent.TIMETABLE_SUMMARY.value,
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

        elif isinstance(
            value,
            str,
        ):

            #
            # Defensive: the LLM sometimes returns
            # non-ISO date strings (e.g. "28 July").
            # Never let them crash intent validation.
            #

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
            ],
            expect_json=True
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

        # ------------------------------------------------------
        # Narrow safety net: marks FOR a specific homework /
        # assignment / worksheet must route to homework_summary,
        # never assessment_summary. Only applies when BOTH a
        # homework object word and a marks/result word appear.
        # ------------------------------------------------------

        if intent == StudentIntent.ASSESSMENT_SUMMARY.value:

            normalized_query = (
                query
                .strip()
                .lower()
            )

            homework_words = [
                "homework",
                "assignment",
                "worksheet",
                "submission",
            ]

            marks_words = [
                "marks",
                "mark",
                "score",
                "grade",
                "result",
                "did i get",
            ]

            has_homework_word = any(
                word in normalized_query
                for word in homework_words
            )

            has_marks_word = any(
                word in normalized_query
                for word in marks_words
            )

            if (
                has_homework_word
                and
                has_marks_word
            ):

                logger.info(
                    "Reclassifying assessment intent to homework_summary: %r",
                    query,
                )

                intent = (
                    StudentIntent.HOMEWORK_SUMMARY.value
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