from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def _serialize_entry(
    entry: dict | None,
) -> dict | None:

    if entry is None:
        return None

    entry = dict(entry)

    if entry.get("start_time") is not None:

        entry["start_time"] = (
            entry["start_time"]
            .strftime("%H:%M:%S")
        )

    if entry.get("end_time") is not None:

        entry["end_time"] = (
            entry["end_time"]
            .strftime("%H:%M:%S")
        )

    return entry


def build_timetable_llm_context(
    structure: dict,
) -> dict:

    entries = structure.get(
        "entries",
        [],
    )

    current_lesson = None
    next_lesson = None

    if structure.get("date") == datetime.now(IST).date():

        now = datetime.now(IST).time()

        for entry in entries:

            if (
                entry["start_time"]
                <= now
                <
                entry["end_time"]
            ):

                current_lesson = entry

                continue

            if (
                entry["start_time"]
                >
                now
            ):

                next_lesson = entry

                break

    return {

        "date":
            structure.get(
                "date"
            ),

        "weekday":
            structure.get(
                "weekday"
            ),

        "lesson_count":
            structure.get(
                "lesson_count",
                0,
            ),

        "activity_count":
            structure.get(
                "activity_count",
                0,
            ),

        "current_lesson":
            _serialize_entry(
                current_lesson,
            ),

        "next_lesson":
            _serialize_entry(
                next_lesson,
            ),

        "structure_of_day": [

            _serialize_entry(
                entry,
            )

            for entry in entries

        ],
    }