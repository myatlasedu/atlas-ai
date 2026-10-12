from datetime import datetime

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.timetable_repository import (
    TimetableRepository,
)

from tools.student.timetable_answer import (
    build_timetable_answer,
    find_current_entry,
    find_next_entry,
)

from utils import (
    IST,
    ist_today,
)


class TimetableTool:

    async def run(
        self,
        parsed_intent,
        context,
    ):

        target_date = (
            parsed_intent.start_date
            or
            ist_today()
        )

        async with AsyncSessionLocal() as session:

            repo = TimetableRepository(
                session,
            )

            structure = await repo.get_structure_of_day(
                enrollment_id=context.enrollment_id,
                target_date=target_date,
            )

        now = datetime.now(IST)

        entries = structure["entries"]

        current_entry = None

        next_entry = None

        if structure["date"] == now.date() and entries:

            current_entry = find_current_entry(
                entries,
                now.time(),
            )

            next_entry = find_next_entry(
                entries,
                now.time(),
            )


        return {

            "module":
                "timetable",

            "date":
                structure["date"],

            "weekday":
                structure["weekday"],

            "lesson_count":
                structure["lesson_count"],

            "activity_count":
                structure["activity_count"],

            "holiday":
                structure["holiday"],

            "current_entry":
                current_entry,

            "next_entry":
                next_entry,

            "entries":
                entries,

            "direct_answer":
                build_timetable_answer(
                    structure,
                    role=getattr(
                        context,
                        "role",
                        "student",
                    ),
                    now=now,
                ),
        }
