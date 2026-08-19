import pytz
import calendar

from datetime import datetime
from datetime import date
from zoneinfo import ZoneInfo

from datetime import (
    date,
    datetime,
    timedelta,
)


IST = ZoneInfo("Asia/Kolkata")


# Academic year runs April - March (India).
# Dates in April through December belong to the year
# that starts on 1 April; January through March belong
# to the previous year's academic year.
ACADEMIC_YEAR_START_MONTH = 4


def academic_year_for(day: date) -> int:

    if day.month >= ACADEMIC_YEAR_START_MONTH:
        return day.year

    return day.year - 1


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

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

ORDINAL_SUFFIXES = (
    "th",
    "st",
    "nd",
    "rd",
)


def month_number(name):

    clean = (
        str(name)
        .strip()
        .strip(".,;:!?()[]\"")
        .lower()
    )

    return MONTH_NAMES.get(clean)


def has_month_name(query):

    for token in query.split():

        if month_number(token) is not None:
            return True

    return False


def has_weekday_name(query):

    for token in query.split():

        clean = token.strip(".,;:!?()[]\"").lower()

        if clean in _WEEKDAY_MAP:
            return True

    return False


def contains_weekday(
    query: str,
    weekday_name: str,
) -> bool:

    for token in query.split():

        clean = token.strip(".,;:!?()[]\"").lower()

        if clean == weekday_name:
            return True

    return False


def parse_day_token(
    token: str,
):

    clean = token.strip(".,;:!?()[]\"")

    for suffix in ORDINAL_SUFFIXES:

        if (
            clean.lower().endswith(suffix)
            and
            clean[:-len(suffix)].isdigit()
        ):
            clean = clean[:-len(suffix)]
            break

    if not clean.isdigit():
        return None

    day = int(clean)

    if not (1 <= day <= 31):
        return None

    return day


def extract_day_month(
    query: str,
):

    tokens = query.split()

    month_index = None

    month = None

    for index, token in enumerate(tokens):

        candidate = month_number(token)

        if candidate is not None:

            month_index = index
            month = candidate
            break

    if month_index is None:
        return None

    year = None

    for token in tokens:

        clean = token.strip(".,;:!?()[]\"")

        if (
            len(clean) == 4
            and
            clean.isdigit()
            and
            1900 <= int(clean) <= 2099
        ):

            year = int(clean)
            break

    if year is None:
        year = academic_year_for(ist_today())

    days = []

    for offset in range(-3, 4):

        position = month_index + offset

        if position < 0 or position >= len(tokens):
            continue

        if position == month_index:
            continue

        day = parse_day_token(
            tokens[position]
        )

        if day is not None:
            days.append(day)

    if not days:
        return None

    days = sorted(
        set(days)
    )

    max_day = calendar.monthrange(
        year,
        month,
    )[1]

    days = [
        day
        for day in days
        if day <= max_day
    ]

    if not days:
        return None

    start = date(
        year,
        month,
        days[0],
    )

    end = date(
        year,
        month,
        days[-1],
    )

    return (start, end)


def extract_month_range(
    query: str,
):

    tokens = query.split()

    months = []

    for token in tokens:

        month = month_number(token)

        if month is not None:
            months.append(month)

    unique_months = set(months)

    if len(unique_months) != 1:
        return None

    month = unique_months.pop()

    year = None

    for token in tokens:

        clean = token.strip(".,;:!?()[]\"")

        if (
            len(clean) == 4
            and
            clean.isdigit()
            and
            1900 <= int(clean) <= 2099
        ):

            year = int(clean)
            break

    if year is None:
        year = academic_year_for(ist_today())

    first = date(
        year,
        month,
        1,
    )

    last = date(
        year,
        month,
        calendar.monthrange(
            year,
            month,
        )[1],
    )

    return (first, last)


def past_or_last_days_count(
    query: str,
):

    tokens = query.split()

    for index, token in enumerate(tokens):

        if token not in ("past", "last"):
            continue

        if index + 2 >= len(tokens):
            continue

        count_token = tokens[index + 1]

        day_token = tokens[index + 2]

        if not count_token.isdigit():
            continue

        if not day_token.startswith("day"):
            continue

        return int(count_token)

    return None


def next_days_count(
    query: str,
):

    tokens = query.split()

    for index, token in enumerate(tokens):

        if token != "next":
            continue

        if index + 2 >= len(tokens):
            continue

        count_token = tokens[index + 1]

        day_token = tokens[index + 2]

        if not count_token.isdigit():
            continue

        if not day_token.startswith("day"):
            continue

        return int(count_token)

    return None


def has_explicit_year(query: str) -> bool:

    for token in query.split():

        clean = token.strip(".,;:!?()[]\"")

        if (
            len(clean) == 4
            and
            clean.isdigit()
            and
            1900 <= int(clean) <= 2099
        ):
            return True

    return False


def force_current_academic_year(
    parsed: dict,
    query: str,
) -> dict:

    if has_explicit_year(query):
        return parsed

    target_year = academic_year_for(ist_today())

    for field in ("start_date", "end_date"):

        value = parsed.get(field)

        if isinstance(value, date):

            parsed[field] = value.replace(
                year=target_year,
            )

    return parsed


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
    # Deterministic day + month override
    # ------------------------------------------------------
    #
    # If the query clearly names a day and month
    # (e.g. "7 August"), trust that over any date the
    # LLM may have returned (it occasionally returns
    # "today" for a clearly dated question).
    #

    start_value = parsed.get("start_date")
    end_value = parsed.get("end_date")

    llm_start = None
    llm_end = None
    llm_valid = False

    if (
        isinstance(start_value, date)
        and
        isinstance(end_value, date)
    ):

        llm_start = start_value
        llm_end = end_value
        llm_valid = True

    elif (
        isinstance(start_value, str)
        and
        isinstance(end_value, str)
    ):

        try:

            llm_start = date.fromisoformat(
                start_value
            )

            llm_end = date.fromisoformat(
                end_value
            )

            llm_valid = True

        except ValueError:
            pass

    day_month = extract_day_month(query)

    if day_month is not None:

        dstart, dend = day_month

        included = (
            llm_valid
            and
            llm_start <= dstart
            and
            dend <= llm_end
        )

        if not included:

            parsed["start_date"] = dstart
            parsed["end_date"] = dend

            return parsed

    month_range = extract_month_range(query)

    if (
        month_range is not None
        and
        day_month is None
    ):

        mstart, mend = month_range

        included = (
            llm_valid
            and
            mstart >= llm_start
            and
            mend <= llm_end
        )

        if not included:

            parsed["start_date"] = mstart
            parsed["end_date"] = mend

            return parsed

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
        return force_current_academic_year(
            parsed,
            query,
        )

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

            return force_current_academic_year(
                parsed,
                query,
            )

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

    days = past_or_last_days_count(query)

    if days:

        parsed["start_date"] = (
            today - timedelta(days=days)
        )

        parsed["end_date"] = today

        return parsed

    # ------------------------------------------------------
    # Next X days
    # ------------------------------------------------------

    days = next_days_count(query)

    if days:

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

        if contains_weekday(query, weekday_name):

            intent = parsed.get("intent")

            if intent == "attendance_summary":

                delta = (
                    today.weekday() - weekday
                ) % 7

                target = (
                    today - timedelta(days=delta)
                )

            else:

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

    # ------------------------------------------------------
    # Deterministic day + month fallback
    # ------------------------------------------------------

    if not parsed.get("start_date") and not parsed.get("end_date"):

        dates = extract_day_month(query)

        if dates:

            parsed["start_date"] = dates[0]
            parsed["end_date"] = dates[1]

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