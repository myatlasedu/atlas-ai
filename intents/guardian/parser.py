import calendar
import logging

from datetime import date
from datetime import timedelta

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
    "resubmit",
    "upcoming",
    "awaiting_marks",
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

    # A named title with no explicit focus is a question about that homework's status/details.

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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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

    # Feedback questions must reach the feedback branch.

    if (
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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
        intent
        ==
        GuardianIntent.HOMEWORK_SUMMARY.value
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

def normalize_dates(
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


async def parse_guardian_intent(
    query: str,
    enrollment_id: int | None = None,
) -> ParsedGuardianIntent:

    try:

        normalized_query = query.strip().lower()

        classified_intent = (
            await classify_guardian_intent(
                normalized_query
            )
        )

        query_lower = normalized_query

        if (
            classified_intent == GuardianIntent.UNKNOWN
            and any(
                word in query_lower
                for word in HOMEWORK_QUERY_KEYWORDS
            )
        ):

            logger.info(
                "UNKNOWN overridden to homework_summary: %r",
                query,
            )

            classified_intent = GuardianIntent.HOMEWORK_SUMMARY

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
                    "content": normalized_query
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

        # Safety net: marks for a specific homework must route to homework_summary.

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

        # Safety net: an unknown with a homework topic routes to homework_summary.

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

        # Homework-first: a subject that names a real homework title is homework.

        if (
            enrollment_id
            and intent
            ==
            GuardianIntent.SUBJECT_SUMMARY.value
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
                    "Reclassifying guardian subject_summary to homework_summary "
                    "(matches homework title %r).",
                    canonical,
                )

                intent = (
                    GuardianIntent.HOMEWORK_SUMMARY.value
                )

                parsed["topic"] = canonical

        parsed["intent"] = intent

        parsed["original_query"] = query

        parsed = normalize_dates(
            parsed
        )

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