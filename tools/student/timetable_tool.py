from datetime import date

from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.timetable_repository import (
    TimetableRepository,
)
from llm.builders.timetable_builder import (
    build_timetable_llm_context,
)
from utils import ist_today


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
                academic_class_id=context.academic_class_id,
                target_date=target_date,
            )

        lesson_count = structure.get(
            "lesson_count",
            0,
        )

        activity_count = structure.get(
            "activity_count",
            0,
        )

        if (
            lesson_count == 0
            and
            activity_count == 0
        ):

            direct_answer = (
                "No Structure of the Day is available."
            )

        else:

            direct_answer = (
                f"Found {lesson_count} lessons and "
                f"{activity_count} activities for the "
                f"Structure of the Day."
            )

        return {

            "module":
                "timetable",

            "date":
                structure["date"],

            "weekday":
                structure["weekday"],

            "lesson_count":
                lesson_count,

            "activity_count":
                activity_count,

            "entries":
                structure["entries"],

            "llm_context":
                build_timetable_llm_context(
                    structure,
                ),

            "direct_answer":
                direct_answer,
        }