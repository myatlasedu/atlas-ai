"""
Plain-text answer for the Structure of the Day.

The timetable answer is built here, not by the summarizer LLM, so
the wording and ordering are deterministic for both roles.
"""

from datetime import (
    date,
    datetime,
    time,
)

from utils import IST


WEEKEND_DAYS = {
    6: "Saturday",
    7: "Sunday",
}


def _owner(
    role: str,
) -> str:

    return (
        "Your child's"
        if role == "guardian"
        else "Your"
    )


def _subject(
    role: str,
) -> str:

    return (
        "Your child has"
        if role == "guardian"
        else "You have"
    )


def _format_time(
    value: time,
) -> str:

    # 09:05 -> "9:05 AM"

    return (
        value
        .strftime("%I:%M %p")
        .lstrip("0")
    )


def _format_date(
    value: date,
) -> str:

    # "Monday, 12 October 2026"

    return (
        f"{value.strftime('%A')}, "
        f"{value.day} {value.strftime('%B %Y')}"
    )


def _span(
    entry: dict,
) -> str:

    return (
        f"{_format_time(entry['start_time'])} - "
        f"{_format_time(entry['end_time'])}"
    )


def _is_break(
    entry: dict,
) -> bool:

    return entry.get("type") == "break"


def _entry_name(
    entry: dict,
) -> str:

    kind = entry.get("type")

    if kind == "enrichment":

        name = (
            entry.get("enrichment_name")
            or entry.get("period_name")
            or "Enrichment"
        )

    elif kind == "activity":

        name = (
            entry.get("activity_name")
            or entry.get("period_name")
            or "Activity"
        )

    elif kind == "break":

        name = (
            entry.get("period_name")
            or (
                "Lunch"
                if entry.get("is_lunch")
                else "Break"
            )
        )

    else:

        name = (
            entry.get("subject_name")
            or entry.get("period_name")
            or "Lesson"
        )

    if entry.get("is_assessment"):

        name = f"{name} (Assessment)"

    return name


def _entry_line(
    entry: dict,
) -> str:

    # "Mathematics (9:00 AM - 9:40 AM) with Priya Sharma, Room 12"

    line = f"{_entry_name(entry)} ({_span(entry)})"

    if _is_break(entry):

        return line

    extras = []

    if entry.get("teacher_name"):

        extras.append(
            f"with {entry['teacher_name']}"
        )

    if entry.get("room_number"):

        extras.append(
            f"Room {entry['room_number']}"
        )

    if extras:

        line = f"{line} {', '.join(extras)}"

    return line


def _kind_label(
    entry: dict,
) -> str:

    return (
        "Break"
        if _is_break(entry)
        else "Lesson"
    )


def find_current_entry(
    entries: list[dict],
    now: time,
) -> dict | None:

    for entry in entries:

        if entry["start_time"] <= now < entry["end_time"]:

            return entry

    return None


def find_next_entry(
    entries: list[dict],
    now: time,
) -> dict | None:

    # Entries are sorted by start time, so the first one that
    # has not started yet is the next one.

    for entry in entries:

        if entry["start_time"] > now:

            return entry

    return None


def _now_lines(
    entries: list[dict],
    now: time,
    role: str,
) -> list[str]:

    owner = _owner(role)

    current = find_current_entry(
        entries,
        now,
    )

    upcoming = find_next_entry(
        entries,
        now,
    )

    lines = []

    if current is not None:

        if _is_break(current):

            lines.append(
                f"Right now it is {_entry_line(current)}."
            )

        else:

            lines.append(
                f"{owner} Current Lesson: {_entry_line(current)}"
            )

    elif now < entries[0]["start_time"]:

        lines.append(
            f"{owner} lessons for today have not started yet."
        )

    elif now >= entries[-1]["end_time"]:

        lines.append(
            f"{owner} lessons for today are over. "
            f"Last {_kind_label(entries[-1])}: "
            f"{_entry_line(entries[-1])}"
        )

        return lines

    else:

        lines.append(
            f"{_subject(role)} no lesson running right now."
        )

    if upcoming is not None:

        lines.append(
            f"Next {_kind_label(upcoming)}: {_entry_line(upcoming)}"
        )

    elif current is not None:

        lines.append(
            "This is the last item of the day."
        )

    return lines


def build_timetable_answer(
    structure: dict,
    role: str,
    now: datetime | None = None,
) -> str:

    now = now or datetime.now(IST)

    target_date = structure["date"]

    day_label = _format_date(
        target_date
    )

    holiday = structure.get(
        "holiday"
    )

    if holiday:

        start = holiday.get("start_date")

        end = holiday.get("end_date")

        if start and end and start != end:

            holiday_label = (
                f"{holiday['title']} "
                f"({start.day} {start.strftime('%B')} - "
                f"{end.day} {end.strftime('%B %Y')})"
            )

        else:

            holiday_label = holiday["title"]

        return (
            f"There are no lessons on {day_label}. "
            f"It is a holiday: {holiday_label}."
        )

    entries = structure.get(
        "entries"
    ) or []

    if not entries:

        weekend_day = WEEKEND_DAYS.get(
            target_date.isoweekday()
        )

        if weekend_day:

            return (
                f"There are no lessons on {weekend_day} "
                f"({target_date.day} {target_date.strftime('%B %Y')})."
            )

        return (
            f"No Structure of the Day is available for {day_label}."
        )

    lines = []

    if target_date == now.date():

        lines.extend(
            _now_lines(
                entries,
                now.time(),
                role,
            )
        )

        lines.append("")

    lines.append(
        f"{_owner(role)} Structure of the Day for {day_label}:"
    )

    for entry in entries:

        lines.append(
            f"• {_entry_line(entry)}"
        )

    return "\n".join(lines)
