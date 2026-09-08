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


# ==========================================================
# NAMED MONTH RESOLUTION
# ==========================================================

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

#
# Abbreviations, and "may", double as ordinary English words
# ("may I", "a sep"), so they only count as a month when the
# query gives a date signal around them.
#

_AMBIGUOUS_MONTH_WORDS = {
    "may",
    "jan", "feb", "mar", "apr", "jun",
    "jul", "aug", "sept", "sep", "oct",
    "nov", "dec",
}

_MONTH_PATTERN = re.compile(
    r"\b("
    r"january|february|march|april|june|july|august|"
    r"september|october|november|december|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec"
    r")\b"
)

_YEAR_PATTERN = re.compile(
    r"\b(20\d{2})\b"
)


_MONTH_ALT = (
    "january|february|march|april|june|july|august|"
    "september|october|november|december|"
    "jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec"
)

_RANGE_SEP = r"(?:to|till|until|through|upto|up\s+to|-|–|—)"

#
# "20 to 26 August", "1 August to 24 August", "20 July - 3 Aug"
#

_DAY_FIRST_RANGE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?"
    rf"(?:({_MONTH_ALT})\b)?\s*"
    rf"{_RANGE_SEP}\s*"
    r"(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?"
    rf"(?:({_MONTH_ALT})\b)?"
)

#
# "August 20 to August 25"
#

_MONTH_DAY_BOTH_RANGE = re.compile(
    rf"\b({_MONTH_ALT})\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?\s*"
    rf"{_RANGE_SEP}\s*"
    rf"({_MONTH_ALT})\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?\b"
)

#
# "August 20 to 26"
#

_MONTH_FIRST_RANGE = re.compile(
    rf"\b({_MONTH_ALT})\s+"
    r"(\d{1,2})(?:st|nd|rd|th)?\s*"
    rf"{_RANGE_SEP}\s*"
    r"(\d{1,2})(?:st|nd|rd|th)?\b"
)


def _resolve_month_year(
    query: str,
    month: int,
    today: date,
) -> int:

    year_match = _YEAR_PATTERN.search(
        query
    )

    if year_match:

        return int(
            year_match.group(1)
        )

    if "next" in query:

        return (
            today.year
            if month > today.month
            else today.year + 1
        )

    if "last" in query or "previous" in query:

        return (
            today.year
            if month < today.month
            else today.year - 1
        )

    # A bare month name means that month of the current year.

    return today.year


def resolve_named_month_range(
    query: str,
    today: date,
):

    #
    # Explicit day ranges inside a month: "from 20 to 26 August",
    # "1 August to 24 August".
    #
    # Without this the single-month resolver below matches only the
    # LAST day mentioned and silently narrows the window to one day.
    #

    #
    # "August 20 to 26" is checked first: it names the month up
    # front, so the day-first pattern would match its bare
    # "20 to 26" tail, find no month, and give up.
    #

    match = _MONTH_DAY_BOTH_RANGE.search(
        query
    )

    if match:

        start_month = _MONTH_NUMBERS[match.group(1)]

        start_day = int(match.group(2))

        end_month = _MONTH_NUMBERS[match.group(3)]

        end_day = int(match.group(4))

    elif _MONTH_FIRST_RANGE.search(query):

        match = _MONTH_FIRST_RANGE.search(
            query
        )

        start_month = end_month = _MONTH_NUMBERS[
            match.group(1)
        ]

        start_day = int(match.group(2))

        end_day = int(match.group(3))

    else:

        match = _DAY_FIRST_RANGE.search(
            query
        )

        if not match:

            return None

        start_name = match.group(2) or match.group(4)

        end_name = match.group(4) or match.group(2)

        if not start_name:

            # "from 20 to 26" with no month named anywhere.

            return None

        start_month = _MONTH_NUMBERS[start_name]

        end_month = _MONTH_NUMBERS[end_name]

        start_day = int(match.group(1))

        end_day = int(match.group(3))

    try:

        start = date(
            _resolve_month_year(query, start_month, today),
            start_month,
            start_day,
        )

        end = date(
            _resolve_month_year(query, end_month, today),
            end_month,
            end_day,
        )

    except ValueError:

        return None

    if start > end:

        start, end = end, start

    return (start, end)


def _month_reference_is_real(
    query: str,
    match,
) -> bool:

    word = match.group(1)

    if word not in _AMBIGUOUS_MONTH_WORDS:

        return True

    before = query[: match.start()].rstrip()

    after = query[match.end() :].lstrip()

    # "in july", "during may", "for aug"

    if re.search(
        r"\b(in|of|during|for|on|by|since|until|till|from|after|before)$",
        before,
    ):
        return True

    # "july 2026", "may 5", "5 may", "july month"

    if re.match(
        r"^(20\d{2}|\d{1,2}(st|nd|rd|th)?\b|month\b)",
        after,
    ):
        return True

    if re.search(
        r"\d{1,2}(st|nd|rd|th)?$",
        before,
    ):
        return True

    return False


def resolve_named_month(
    query: str,
    today: date,
):

    #
    # "events in July", "july month", "3 August", "March 2025".
    #
    # Without this, a bare month name resolves to nothing and the
    # phrase "<month> month" falls through to the generic "month"
    # branch below, which silently answers for the CURRENT month.
    #

    match = _MONTH_PATTERN.search(
        query
    )

    if not match:

        return None

    if not _month_reference_is_real(
        query,
        match,
    ):

        return None

    month = _MONTH_NUMBERS[
        match.group(1)
    ]

    # ------------------------------------------------------
    # Year
    # ------------------------------------------------------

    year = _resolve_month_year(
        query,
        month,
        today,
    )

    # ------------------------------------------------------
    # Specific day: "3 August", "August 3rd"
    # ------------------------------------------------------

    day = None

    day_before = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+$",
        query[: match.start()],
    )

    day_after = re.match(
        r"^\s*(\d{1,2})(?:st|nd|rd|th)?\b",
        query[match.end() :],
    )

    if day_before:

        day = int(day_before.group(1))

    elif day_after:

        day = int(day_after.group(1))

    try:

        if day:

            target = date(year, month, day)

            return (target, target)

        last_day = calendar.monthrange(
            year,
            month,
        )[1]

        return (
            date(year, month, 1),
            date(year, month, last_day),
        )

    except ValueError:

        # Out-of-range day ("45 July"); detect_invalid_date
        # already flags these for the caller.

        return None


def resolve_dates(
    parsed: dict,
):

    today = ist_today()

    query = (
        parsed.get(
            "original_query",
            "",
        )
        .lower()
        .strip()
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
    # Named month
    # "in July", "july month", "3 August", "March 2025"
    #
    # Must run before the generic week/month branches: the phrase
    # "july month" contains "month" and would otherwise resolve to
    # the CURRENT month, silently answering for the wrong period.
    # ------------------------------------------------------

    named_month = (
        resolve_named_month_range(
            query,
            today,
        )
        or
        resolve_named_month(
            query,
            today,
        )
    )

    if named_month:

        parsed["start_date"] = named_month[0]

        parsed["end_date"] = named_month[1]

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