import pytz
import calendar
import difflib
from datetime import datetime
from datetime import date
from zoneinfo import ZoneInfo

import re

from datetime import (
    date,
    datetime,
    timedelta,
)


IST = ZoneInfo("Asia/Kolkata")

MARKS_QUERY_KEYWORDS = ("marks", "grade", "score", "result")

HOMEWORK_QUERY_KEYWORDS = ("homework", "assignment", "worksheet", "submission", " hw")

FEEDBACK_QUERY_KEYWORDS = ("feedback", "remarks", "comments", "teacher say", "teacher said")

VALID_HOMEWORK_GRADES = ("A*", "A", "B", "C", "D", "E", "U")

MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november",
    "december", "jan", "feb", "mar", "apr", "jun", "jul",
    "aug", "sep", "oct", "nov", "dec",
)


def detect_invalid_date(query):
    lower = query.lower()
    for month in MONTH_NAMES:
        idx = lower.find(month)
        if idx == -1:
            continue
        tokens = lower[:idx].strip().split()
        if not tokens:
            continue
        token = tokens[-1].rstrip("stndrdth.,")
        if token.isdigit() and int(token) not in range(1, 32):
            return True
    return False


MARKS_MANIPULATION_KEYWORDS = (
    "give me 100", "give me 100%", "100% marks", "100% grade",
    "100 percent", "change my marks", "set my marks",
    "update my marks", "increase my marks", "boost my marks",
    "full marks",
)


def resolve_canonical_name(raw, names, cutoff=0.6):
    match = difflib.get_close_matches(
        str(raw).lower(),
        [str(n).lower() for n in names],
        n=1,
        cutoff=cutoff,
    )
    if match:
        return next(n for n in names if str(n).lower() == match[0])
    return None


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def ist_datetime():
    return ist_now()



def convert_to_ist(dt):

    if dt is None:
        return None

    return (
        dt.astimezone(IST)
        .isoformat()
    )



# ==========================================================
# DATE RESOLUTION
# ==========================================================

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# Phrases that name a time window on their own.

DATE_WINDOW_PHRASES = (
    "day before yesterday",
    "yesterday",
    "today",
    "tomorrow",
    "this week",
    "last week",
    "next week",
    "this month",
    "last month",
    "next month",
    "this year",
    "last year",
    "next year",
)


def date_query(
    parsed: dict,
) -> str:

    raw = str(
        parsed.get(
            "raw_query"
        )
        or ""
    ).lower().strip()

    resolved = str(
        parsed.get(
            "original_query"
        )
        or ""
    ).lower().strip()

    if raw and (
        any(
            phrase in raw
            for phrase in DATE_WINDOW_PHRASES
        )
        or month_window(raw) is not None
    ):

        return raw

    return resolved


_MONTH_NUMBERS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


# Month names that are also ordinary words ("may i see my homework")
# or too short to be safe on their own ("sep my homework"). These only
# count as a date when the query uses them like one.

_AMBIGUOUS_MONTHS = {
    "may",
    "jan", "feb", "mar", "apr", "jun",
    "jul", "aug", "sept", "sep", "oct",
    "nov", "dec",
}


# Words that introduce a date: "homework of may", "due in sept".

_DATE_MARKERS = {
    "of",
    "in",
    "for",
    "during",
    "from",
    "since",
    "till",
    "until",
    "through",
    "between",
}


_MONTH_PATTERN = re.compile(
    r"\b(?:(?P<day1>\d{1,2})\s*(?:st|nd|rd|th)?\s+(?:of\s+)?)?"
    r"(?P<month>january|february|march|april|may|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)"
    r"(?:\s+(?P<day2>\d{1,2})\s*(?:st|nd|rd|th)?)?"
    r"(?:\s*,?\s*(?P<year>\d{4}))?\b"
)


# A relative window is more specific than a bare month name, so
# "last week" wins over an incidental month word.

_RELATIVE_WINDOW_PHRASES = (
    "this week",
    "last week",
    "next week",
    "this month",
    "last month",
    "next month",
    "this year",
    "last year",
    "next year",
)


def _is_date_usage(
    query: str,
    match,
) -> bool:

    # An unambiguous month name is always a date. An ambiguous one
    # needs evidence: an explicit day, a year, or a preposition that
    # only ever introduces a date.

    token = match.group(
        "month"
    )

    if token not in _AMBIGUOUS_MONTHS:

        return True

    if (
        match.group("day1")
        or match.group("day2")
        or match.group("year")
    ):

        return True

    preceding = query[: match.start()].split()

    return bool(
        preceding
        and preceding[-1] in _DATE_MARKERS
    )


def month_window(
    query: str,
):

    #
    # Resolve a named month ("july", "homework of july 2025",
    # "28 july") into a concrete window.
    #
    # Returns (start, end) or None. A bare month means that month of
    # the CURRENT year - in an April-March academic year a month that
    # has not arrived yet is still this year's, not last year's.
    #

    if not query:

        return None

    lowered = query.lower()

    if any(
        phrase in lowered
        for phrase in _RELATIVE_WINDOW_PHRASES
    ):

        return None

    for match in _MONTH_PATTERN.finditer(
        lowered
    ):

        if not _is_date_usage(
            lowered,
            match,
        ):

            continue

        month = _MONTH_NUMBERS[
            match.group("month")
        ]

        year = (
            int(
                match.group("year")
            )
            if match.group("year")
            else ist_today().year
        )

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        day = (
            match.group("day1")
            or match.group("day2")
        )

        if day:

            day = int(day)

            if not 1 <= day <= last_day:

                # An impossible day ("35 july") is reported by
                # detect_invalid_date, never widened to the month.

                return None

            target = date(
                year,
                month,
                day,
            )

            return (
                target,
                target,
            )

        return (
            date(year, month, 1),
            date(year, month, last_day),
        )

    return None


def resolve_dates(
    parsed: dict,
):

    today = ist_today()

    query = date_query(
        parsed
    )

    # ------------------------------------------------------
    # Explicit dates already parsed by LLM
    # ------------------------------------------------------

    start_date = parsed.get("start_date")
    end_date = parsed.get("end_date")

    #
    # If the LLM already returned ISO dates,
    # don't resolve again.
    #

    if (
        isinstance(start_date, date)
        and
        isinstance(end_date, date)
    ):
        return parsed

    if (
        isinstance(start_date, str)
        and
        isinstance(end_date, str)
    ):

        try:

            parsed["start_date"] = date.fromisoformat(
                start_date
            )

            parsed["end_date"] = date.fromisoformat(
                end_date
            )

            return parsed

        except ValueError:

            #
            # Not ISO dates (e.g. "yesterday"),
            # continue resolving below.
            #
            pass

    # ------------------------------------------------------
    # Day before yesterday
    # ------------------------------------------------------

    if any(
        phrase in query
        for phrase in [
            "day before yesterday",
            "the day before yesterday",
        ]
    ):

        target = today - timedelta(days=2)

        parsed["start_date"] = target
        parsed["end_date"] = target

        return parsed

    
    # ------------------------------------------------------
    # Relative day phrases
    # ------------------------------------------------------

    #
    # day before yesterday
    # day before day before yesterday
    # last day before yesterday
    #

    if "yesterday" in query:

        days = 1

        #
        # Count:
        # day before yesterday
        # day before day before yesterday
        #

        days += query.count(
            "day before"
        )

        #
        # Count any "last"
        #
        # yesterday                -> 0
        # last yesterday           -> 1
        # last last yesterday      -> 2
        # last to last yesterday   -> 2
        #

        days += query.count(
            "last"
        )

        target = (
            today - timedelta(days=days)
        )

        parsed["start_date"] = target
        parsed["end_date"] = target

        return parsed


    #
    # today
    #

    if "today" in query:

        parsed["start_date"] = today
        parsed["end_date"] = today

        return parsed


    #
    # tomorrow
    #

    if "tomorrow" in query:

        days = 1

        #
        # tomorrow
        # next tomorrow
        # next next tomorrow
        #

        days += query.count(
            "next"
        )

        target = (
            today + timedelta(days=days)
        )

        parsed["start_date"] = target
        parsed["end_date"] = target

        return parsed

    # ------------------------------------------------------
    # Named month ("july", "july 2025", "28 july")
    # ------------------------------------------------------

    window = month_window(
        query
    )

    if window:

        parsed["start_date"] = window[0]
        parsed["end_date"] = window[1]

        return parsed

    # ------------------------------------------------------
    # This week
    # ------------------------------------------------------

    if "this week" in query:

        start = (
            today
            - timedelta(days=today.weekday())
        )

        parsed["start_date"] = start
        parsed["end_date"] = today

        return parsed

    # ------------------------------------------------------
    # Relative weeks
    # ------------------------------------------------------

    if "week" in query:

        current_week_start = (
            today - timedelta(days=today.weekday())
        )

        if "last" in query:

            weeks = query.count("last")

            start = (
                current_week_start
                - timedelta(days=7 * weeks)
            )

            end = (
                start + timedelta(days=6)
            )

            parsed["start_date"] = start
            parsed["end_date"] = end

            return parsed

        if "next" in query:

            weeks = query.count("next")

            start = (
                current_week_start
                + timedelta(days=7 * weeks)
            )

            end = (
                start + timedelta(days=6)
            )

            parsed["start_date"] = start
            parsed["end_date"] = end

            return parsed

        #
        # this week
        #

        parsed["start_date"] = current_week_start
        parsed["end_date"] = today

        return parsed

    # ------------------------------------------------------
    # This month
    # ------------------------------------------------------

    if "this month" in query:

        parsed["start_date"] = today.replace(
            day=1,
        )

        parsed["end_date"] = today

        return parsed

    if "month" in query:

        if "last" in query:

            months_back = query.count("last")

            year = today.year
            month = today.month

            for _ in range(months_back):

                month -= 1

                if month == 0:
                    month = 12
                    year -= 1

            first = date(year, month, 1)

            last = date(
                year,
                month,
                calendar.monthrange(year, month)[1],
            )

            parsed["start_date"] = first
            parsed["end_date"] = last

            return parsed

        if "next" in query:

            months_forward = query.count("next")

            year = today.year
            month = today.month

            for _ in range(months_forward):

                month += 1

                if month == 13:
                    month = 1
                    year += 1

            first = date(year, month, 1)

            last = date(
                year,
                month,
                calendar.monthrange(year, month)[1],
            )

            parsed["start_date"] = first
            parsed["end_date"] = last

            return parsed

        #
        # this month
        #

        parsed["start_date"] = today.replace(day=1)
        parsed["end_date"] = today

        return parsed

    # ------------------------------------------------------
    # Past X days
    # ------------------------------------------------------

    match = re.search(
        r"(?:past|last)\s+(\d+)\s+days",
        query,
    )

    if match:

        days = int(
            match.group(1)
        )

        parsed["start_date"] = (
            today - timedelta(days=days)
        )

        parsed["end_date"] = today

        return parsed

    # ------------------------------------------------------
    # Next X days
    # ------------------------------------------------------

    match = re.search(
        r"next\s+(\d+)\s+days",
        query,
    )

    if match:

        days = int(
            match.group(1)
        )

        parsed["start_date"] = today

        parsed["end_date"] = (
            today + timedelta(days=days)
        )

        return parsed

    # ------------------------------------------------------
    # Weekday
    # Monday
    # Tuesday
    # Last Monday
    # Next Friday
    # ------------------------------------------------------

    for weekday_name, weekday in _WEEKDAY_MAP.items():

        if f"last {weekday_name}" in query:

            delta = (
                today.weekday() - weekday
            ) % 7

            if delta == 0:
                delta = 7

            target = (
                today - timedelta(days=delta)
            )

            parsed["start_date"] = target
            parsed["end_date"] = target

            return parsed

        if f"next {weekday_name}" in query:

            delta = (
                weekday - today.weekday()
            ) % 7

            if delta == 0:
                delta = 7

            target = (
                today + timedelta(days=delta)
            )

            parsed["start_date"] = target
            parsed["end_date"] = target

            return parsed

        if re.search(
            rf"\b{weekday_name}\b",
            query,
        ):

            delta = (
                weekday - today.weekday()
            ) % 7

            target = (
                today + timedelta(days=delta)
            )

            parsed["start_date"] = target
            parsed["end_date"] = target

            return parsed

    return parsed


# ==========================================================
# DATETIME FORMATTER
# ==========================================================

def format_datetime(
    value,
):

    if not isinstance(
        value,
        datetime,
    ):
        value = datetime.fromisoformat(
            str(value)
        )

    ist = pytz.timezone(
        "Asia/Kolkata",
    )

    if value.tzinfo is None:

        value = pytz.utc.localize(
            value,
        )

    return value.astimezone(
        ist,
    ).strftime(
        "%d %b %Y at %I:%M %p",
    )

def resolve_canonical_name(raw, names, cutoff=0.6):
    match = difflib.get_close_matches(
        str(raw).lower(),
        [str(n).lower() for n in names],
        n=1,
        cutoff=cutoff,
    )
    if match:
        return next(n for n in names if str(n).lower() == match[0])
    return None


def format_homework_graded_response(title: str, role: str = "student", close_match_note: str = "") -> str:
    if role == "guardian":
        return f"{close_match_note}Your child's {title} homework has been graded. The grade will be available on the report card."
    return f"{close_match_note}Your {title} homework has been graded. Your grade will be available on the report card."


def format_homework_ungraded_response(title: str, role: str = "student", close_match_note: str = "") -> str:
    if role == "guardian":
        return f"{close_match_note}Your child's {title} homework has not been graded yet. The grade will be available on the report card once declared."
    return f"{close_match_note}Your {title} homework has not been graded yet. Your grade will be available on the report card once declared."


_MARKS_KEYS_TO_REMOVE = {
    "grade",
    "marks",
    "marks_obtained",
    "total_marks",
    "score",
    "final_grade",
    "percentage",
    "average_percentage",
    "highest_percentage",
    "lowest_percentage",
}


def process_and_sanitize_grades(data):
    """
    Recursively inspects data structures returned by tools.
    If marks or grade keys are present, sets boolean isGrade/isGraded/is_graded,
    and removes all raw marks, grades, and percentages.
    """
    if isinstance(data, dict):
        has_grade_mark_indicator = any(
            k in data for k in (
                "grade",
                "marks",
                "marks_obtained",
                "total_marks",
                "score",
                "final_grade",
                "percentage",
                "is_graded",
                "isGrade",
                "isGraded",
            )
        ) or (
            data.get("status") in (2, 3)
            or data.get("status_tag") in ("graded", "submitted_not_graded")
        )

        if has_grade_mark_indicator:
            is_graded = False
            if "isGrade" in data and isinstance(data["isGrade"], bool):
                is_graded = data["isGrade"]
            elif "isGraded" in data and isinstance(data["isGraded"], bool):
                is_graded = data["isGraded"]
            elif "is_graded" in data and isinstance(data["is_graded"], bool):
                is_graded = data["is_graded"]
            elif data.get("status") in (2, 3) or data.get("status_tag") == "graded":
                is_graded = True
            elif data.get("marks_obtained") is not None or (data.get("grade") and str(data.get("grade")).strip()):
                is_graded = True

            data["isGrade"] = is_graded
            data["isGraded"] = is_graded
            data["is_graded"] = is_graded

            for key in _MARKS_KEYS_TO_REMOVE:
                data.pop(key, None)

        for k, v in list(data.items()):
            data[k] = process_and_sanitize_grades(v)

        return data

    elif isinstance(data, list):
        return [process_and_sanitize_grades(item) for item in data]

    return data