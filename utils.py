import pytz
import calendar

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


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def ist_datetime():
    return ist_now()




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