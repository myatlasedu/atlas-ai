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

    if (
        parsed.get("start_date")
        is not None
    ):
        return parsed

    # ------------------------------------------------------
    # Today / Yesterday / Tomorrow
    # ------------------------------------------------------

    if "today" in query:

        parsed["start_date"] = today
        parsed["end_date"] = today

        return parsed

    if "yesterday" in query:

        target = (
            today - timedelta(days=1)
        )

        parsed["start_date"] = target
        parsed["end_date"] = target

        return parsed

    if "tomorrow" in query:

        target = (
            today + timedelta(days=1)
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
    # Last week
    # ------------------------------------------------------

    if "last week" in query:

        start = (
            today
            - timedelta(
                days=today.weekday() + 7
            )
        )

        end = (
            start + timedelta(days=6)
        )

        parsed["start_date"] = start
        parsed["end_date"] = end

        return parsed

    # ------------------------------------------------------
    # Next week
    # ------------------------------------------------------

    if "next week" in query:

        start = (
            today
            - timedelta(days=today.weekday())
            + timedelta(days=7)
        )

        end = (
            start + timedelta(days=6)
        )

        parsed["start_date"] = start
        parsed["end_date"] = end

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

    # ------------------------------------------------------
    # Last month
    # ------------------------------------------------------

    if "last month" in query:

        if today.month == 1:

            year = today.year - 1
            month = 12

        else:

            year = today.year
            month = today.month - 1

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

        parsed["start_date"] = first
        parsed["end_date"] = last

        return parsed

    # ------------------------------------------------------
    # Next month
    # ------------------------------------------------------

    if "next month" in query:

        if today.month == 12:

            year = today.year + 1
            month = 1

        else:

            year = today.year
            month = today.month + 1

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

        parsed["start_date"] = first
        parsed["end_date"] = last

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