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

        value = parsed.get(
            field
        )

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
    prior_context: str | None = None,
) -> ParsedStudentIntent:

    try:

        # ==================================================
        # STEP 1
        # CLASSIFY INTENT
        # ==================================================

        classified_intent = (
            await classify_student_intent(
                query,
                prior_context=prior_context,
            )
        )

        logger.info(
            "Classified intent: %s",
            classified_intent.value,
        )

        # ==================================================
        # STEP 2
        # PARAMETER EXTRACTION
        #
        # The classifier's intent is authoritative.
        # The second LLM must NOT re-classify the query.
        # ==================================================

        prompt = (
            get_student_intent_prompt(
                classified_intent
            )
        )

        user_content = query

        if prior_context:

            user_content = (
                f"PRIOR CONVERSATION\n\n"
                f"{prior_context}\n\n"
                f"QUESTION\n\n{query}\n\n"
                "Use the prior conversation only to "
                "resolve references (subjects, dates, "
                "pronouns)."
            )

        response = await chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            expect_json=True
        )

        content = (
            response["message"]["content"]
        )

        logger.info(
            "RAW PARAMETER MODEL RESPONSE >>> %r",
            content,
        )

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Parsed parameters >>> %s",
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
        # Narrow safety net: marks FOR a specific titled homework /
        # assignment / worksheet must route to homework_summary,
        # never assessment_summary. Only applies when the intent
        # parser set asks_for_marks AND a specific topic title.
        # ------------------------------------------------------

        if (
            intent == StudentIntent.ASSESSMENT_SUMMARY.value
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

        # ==================================================
        # STEP 5
        # ORIGINAL QUERY
        # ==================================================

        parsed["original_query"] = query

        # ==================================================
        # STEP 6
        # NORMALIZE DATES
        # ==================================================

        parsed = _normalize_dates(
            parsed
        )

        # ==================================================
        # STEP 7
        # NORMALIZE MODULES
        # ==================================================

        parsed = _normalize_modules(
            parsed
        )

        # ==================================================
        # STEP 8
        # BUILD FINAL SCHEMA
        # ==================================================

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