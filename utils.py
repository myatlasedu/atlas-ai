from datetime import datetime
import pytz

from datetime import (
    date,
    timedelta
)

import calendar


def resolve_dates(
    parsed: dict
):

    today = date.today()

    start = parsed.get("start_date")
    end = parsed.get("end_date")

    query = (
        parsed.get("original_query", "")
        .lower()
    )

    if start:
        return parsed

    if "today" in query:

        parsed["start_date"] = today
        parsed["end_date"] = today

    elif "yesterday" in query:

        yesterday = (
            today - timedelta(days=1)
        )

        parsed["start_date"] = yesterday
        parsed["end_date"] = yesterday

    elif "tomorrow" in query:

        tomorrow = (
            today + timedelta(days=1)
        )

        parsed["start_date"] = tomorrow
        parsed["end_date"] = tomorrow

    elif "this week" in query:

        monday = today - timedelta(
            days=today.weekday()
        )

        sunday = monday + timedelta(
            days=6
        )

        parsed["start_date"] = monday
        parsed["end_date"] = sunday

    elif "last week" in query:

        monday = (
            today
            - timedelta(days=today.weekday() + 7)
        )

        sunday = monday + timedelta(
            days=6
        )

        parsed["start_date"] = monday
        parsed["end_date"] = sunday

    elif "this month" in query:

        parsed["start_date"] = today.replace(
            day=1
        )

        last = calendar.monthrange(
            today.year,
            today.month
        )[1]

        parsed["end_date"] = today.replace(
            day=last
        )

    elif "last month" in query:

        if today.month == 1:

            year = today.year - 1
            month = 12

        else:

            year = today.year
            month = today.month - 1

        first = date(
            year,
            month,
            1
        )

        last = calendar.monthrange(
            year,
            month
        )[1]

        parsed["start_date"] = first

        parsed["end_date"] = date(
            year,
            month,
            last
        )

    return parsed

def format_datetime(value):

    if not isinstance(
        value,
        datetime
    ):
        value = datetime.fromisoformat(
            str(value)
        )

    ist = pytz.timezone(
        "Asia/Kolkata"
    )

    ist_dt = value.astimezone(
        ist
    )

    return ist_dt.strftime(
        "%d %b %Y at %I:%M %p"
    )