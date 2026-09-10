import logging
import calendar
from datetime import date
from datetime import timedelta
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
    ist_today,
    MARKS_QUERY_KEYWORDS,
    HOMEWORK_QUERY_KEYWORDS,
    FEEDBACK_QUERY_KEYWORDS,
    detect_invalid_date,
    resolve_canonical_name,
)

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.homework_repository import (
    HomeworkRepository,
)


logger = logging.getLogger(__name__)


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

            parsed[field] = (
                value.isoformat()
            )

        elif isinstance(
            value,
            str,
        ):

            # LLM sometimes returns non-ISO dates ("28 July"); never crash validation.

            try:

                parsed[field] = (
                    date.fromisoformat(
                        value
                    )
                    .isoformat()
                )

            except ValueError:

                parsed[field] = None

    if detect_invalid_date(
        str(
            parsed.get(
                "original_query",
                "",
            )
        )
    ):

        parsed["invalid_date"] = True

        parsed["start_date"] = None

        parsed["end_date"] = None

    return parsed


VALID_HOMEWORK_FOCUS = {
    "topic_status",
    "pending",
    "overdue",
    "due_today",
    "due_tomorrow",
    "submitted",
    "graded",
    "feedback",
    "resubmit",
    "upcoming",
    "awaiting_marks",
    "due_range",
    "next_up",
    "general",
}


def clean_topic(
    value: str,
) -> str:

    # Strip whitespace/trailing punctuation so titled lookups never miss on grammar.

    trimmed = (
        value
        .strip()
        .strip("?!.,;:'\"")
        .strip()
    )

    return trimmed


def normalize_focus(
    parsed: dict,
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

    # A named title with no explicit focus is a question about that homework's status/details.

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
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

    # Week/month: force due_range for the full window (homework-only; resolve_dates stays end-at-today).

    query_lower = (
        parsed.get("original_query", "")
        .lower()
    )

    window_phrase = any(
        phrase in query_lower
        for phrase in (
            "this week",
            "last week",
            "next week",
            "this month",
            "last month",
            "next month",
        )
    )

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        window_phrase
        and
        focus in (None, "general", "pending", "next_up", "due_range")
    ):

        parsed["homework_focus"] = "due_range"

        if "this week" in query_lower:

            today = ist_today()

            monday = today - timedelta(
                days=today.weekday()
            )

            sunday = monday + timedelta(days=6)

            parsed["start_date"] = monday.isoformat()

            parsed["end_date"] = sunday.isoformat()

        elif "last week" in query_lower:

            today = ist_today()

            monday = (
                today
                - timedelta(days=today.weekday())
                - timedelta(days=7)
            )

            sunday = monday + timedelta(days=6)

            parsed["start_date"] = monday.isoformat()

            parsed["end_date"] = sunday.isoformat()

        elif "next week" in query_lower:

            today = ist_today()

            monday = (
                today
                - timedelta(days=today.weekday())
                + timedelta(days=7)
            )

            sunday = monday + timedelta(days=6)

            parsed["start_date"] = monday.isoformat()

            parsed["end_date"] = sunday.isoformat()

        elif "this month" in query_lower:

            today = ist_today()

            last_day = calendar.monthrange(
                today.year,
                today.month,
            )[1]

            parsed["start_date"] = today.replace(
                day=1,
            ).isoformat()

            parsed["end_date"] = today.replace(
                day=last_day,
            ).isoformat()

        elif "last month" in query_lower:

            today = ist_today()

            year = today.year

            month = today.month - 1

            if month == 0:

                month = 12

                year -= 1

            last_day = calendar.monthrange(
                year,
                month,
            )[1]

            parsed["start_date"] = date(
                year,
                month,
                1,
            ).isoformat()

            parsed["end_date"] = date(
                year,
                month,
                last_day,
            ).isoformat()

        elif "next month" in query_lower:

            today = ist_today()

            year = today.year

            month = today.month + 1

            if month == 13:

                month = 1

                year += 1

            last_day = calendar.monthrange(
                year,
                month,
            )[1]

            parsed["start_date"] = date(
                year,
                month,
                1,
            ).isoformat()

            parsed["end_date"] = date(
                year,
                month,
                last_day,
            ).isoformat()

    # Late submissions ("late homework submitted last week") = handed in after the due date.

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        any(
            word in query_lower
            for word in ("late", "delayed")
        )
        and
        any(
            word in query_lower
            for word in ("submitted", "submission", "handed", "turned in")
        )
        and
        focus in (None, "general", "overdue", "submitted", "pending", "due_range")
    ):

        parsed["homework_focus"] = "submitted"

        focus = "submitted"

        parsed["late_only"] = True

    # Upcoming/future: force "upcoming" focus (due after today); skipped when a week/month window is set.

    upcoming_phrase = (
        not window_phrase
        and any(
            phrase in query_lower
            for phrase in (
                "upcoming",
                "coming up",
                "future homework",
                "future assignment",
            )
        )
    )

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        upcoming_phrase
        and
        focus in (None, "general", "pending", "overdue", "next_up", "due_range")
    ):

        parsed["homework_focus"] = "upcoming"

    # "Submitted ... this week/month" must use the deterministic calendar window:
    # clear the LLM's ISO dates and re-run resolve_dates (backend owns dates).

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        focus == "submitted"
        and
        not parsed.get("topic")
        and
        window_phrase
    ):

        parsed["start_date"] = None

        parsed["end_date"] = None

        parsed = resolve_dates(
            parsed
        )

    # General marks questions are graded; detect from the query (the LLM only sets it for a named homework).

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        focus in (None, "general")
        and
        any(
            keyword in query_lower
            for keyword in MARKS_QUERY_KEYWORDS
        )
    ):

        parsed["homework_focus"] = "graded"

    # General feedback questions must reach the feedback branch (the LLM may default them to general).

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        focus in (None, "general")
        and
        any(
            keyword in query_lower
            for keyword in FEEDBACK_QUERY_KEYWORDS
        )
    ):

        parsed["homework_focus"] = "feedback"

    # Next/last year is a year-wide window; resolves to an honest (often empty) due_range.

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        focus in (None, "general", "due_range")
    ):

        if "next year" in query_lower:

            year = ist_today().year + 1

            parsed["homework_focus"] = "due_range"

            parsed["start_date"] = f"{year}-01-01"

            parsed["end_date"] = f"{year}-12-31"

        elif "last year" in query_lower:

            year = ist_today().year - 1

            parsed["homework_focus"] = "due_range"

            parsed["start_date"] = f"{year}-01-01"

            parsed["end_date"] = f"{year}-12-31"

    # "due"/"pending" are synonyms for the full open list; "due/pending today" -> due today.

    if (
        parsed.get("intent")
        ==
        StudentIntent.HOMEWORK_SUMMARY.value
        and
        not parsed.get("topic")
        and
        focus in (None, "general", "pending", "due_range", "overdue", "upcoming", "next_up")
        and
        any(
            word in query_lower.split()
            for word in ("due", "pending")
        )
        and
        not any(
            phrase in query_lower
            for phrase in (
                "this week",
                "last week",
                "next week",
                "this month",
                "last month",
                "next month",
                "tomorrow",
                "upcoming",
                "next",
                "submitted",
                "graded",
                "marks",
                "feedback",
                "resubmit",
            )
        )
    ):

        parsed["homework_focus"] = (
            "due_today"
            if "today" in query_lower
            else "pending"
        )

    return parsed


async def parse_student_intent(
    query: str,
    enrollment_id: int | None = None,
) -> ParsedStudentIntent:

    try:

        # ==================================================
        # STEP 1
        # CLASSIFY INTENT
        # ==================================================

        normalized_query = query.strip().lower()

        classified_intent = (
            await classify_student_intent(
                normalized_query
            )
        )

        query_lower = normalized_query

        if (
            classified_intent == StudentIntent.UNKNOWN
            and any(
                word in query_lower
                for word in HOMEWORK_QUERY_KEYWORDS
            )
        ):

            logger.info(
                "UNKNOWN overridden to homework_summary: %r",
                query,
            )

            classified_intent = StudentIntent.HOMEWORK_SUMMARY

        logger.info(
            "Classified intent: %s",
            classified_intent.value,
        )

        # ==================================================
        # STEP 2: PARAMETER EXTRACTION (never re-classify)
        # ==================================================

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
                    "content": normalized_query,
                },
            ],
            expect_json=True,
            thinking=False
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

        # ==================================================
        # STEP 3: FORCE CLASSIFIER INTENT (never trust the second LLM's intent)
        # ==================================================

        parsed["intent"] = (
            classified_intent.value
        )

        # Safety net: marks for a specific homework must route to homework_summary,
        # but NEVER when the user explicitly asked about an assessment/test/exam,
        # and only if the topic actually matches a known homework title.

        if (
            enrollment_id
            and parsed["intent"]
            ==
            StudentIntent.ASSESSMENT_SUMMARY.value
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
            and not any(
                w in query_lower
                for w in ["assessment", "assessments", "exam", "exams"]
            )
        ):

            async with AsyncSessionLocal() as db:

                hw_repo = HomeworkRepository(db)

                hw_titles = [
                    t["title"]
                    for t in (
                        await hw_repo.list_enrollment_homework_titles(
                            enrollment_id
                        )
                    )
                ]

            canonical_hw = resolve_canonical_name(
                str(parsed["topic"]),
                hw_titles,
            )

            if canonical_hw:

                logger.info(
                    "Reclassifying assessment intent to homework_summary "
                    "(matches homework title %r): %r",
                    canonical_hw,
                    query,
                )

                parsed["intent"] = (
                    StudentIntent.HOMEWORK_SUMMARY.value
                )

                parsed["topic"] = canonical_hw

        # Clean the extracted title: trailing punctuation would break exact lookups.

        if parsed.get(
            "topic",
            None,
        ):

            cleaned = clean_topic(
                str(parsed["topic"])
            )

            if cleaned != parsed["topic"]:

                logger.info(
                    "Cleaned topic %r -> %r",
                    parsed["topic"],
                    cleaned,
                )

            parsed["topic"] = (
                cleaned
                or None
            )

        # Homework-first: a topic that names a real homework title is homework.

        if (
            enrollment_id
            and parsed["intent"]
            in (
                StudentIntent.TOPIC_SUMMARY.value,
                StudentIntent.SUBJECT_SUMMARY.value,
            )
            and parsed.get(
                "topic",
                None,
            )
        ):

            async with AsyncSessionLocal() as db:

                repo = HomeworkRepository(db)

                titles = [
                    t["title"]
                    for t in (
                        await repo.list_enrollment_homework_titles(
                            enrollment_id
                        )
                    )
                ]

            canonical = resolve_canonical_name(
                str(parsed["topic"]),
                titles,
            )

            if canonical:

                logger.info(
                    "Reclassifying %s to homework_summary "
                    "(matches homework title %r).",
                    parsed["intent"],
                    canonical,
                )

                parsed["intent"] = (
                    StudentIntent.HOMEWORK_SUMMARY.value
                )

                parsed["topic"] = canonical

        # ==================================================
        # STEP 4
        # DEFAULT MODULES
        # ==================================================

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
        # STEP 7b
        # NORMALIZE HOMEWORK FOCUS
        # ==================================================

        parsed = normalize_focus(
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