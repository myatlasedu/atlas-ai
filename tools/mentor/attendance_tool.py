from db.session import (
    AsyncSessionLocal
)

from db.repositories.mentor.attendance_repository import (
    MentorAttendanceRepository
)


class AttendanceTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            repo = MentorAttendanceRepository(
                db
            )

            view = (
                parsed_intent.view
                or "summary"
            )

            if view == "summary":

                return await repo.get_summary(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "absent_students":

                return await repo.get_absent_students(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "present_students":

                return await repo.get_present_students(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "late_students":

                return await repo.get_late_students(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "half_day_students":

                return await repo.get_half_day_students(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "attendance_percentage":

                return await repo.get_attendance_percentage(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "low_attendance":

                return await repo.get_low_attendance_students(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "attendance_trend":

                return await repo.get_attendance_trend(
                    context=context,
                    parsed_intent=parsed_intent
                )

            if view == "subject_summary":

                return await repo.get_subject_summary(
                    context=context,
                    parsed_intent=parsed_intent
                )

            return await repo.get_summary(
                context=context,
                parsed_intent=parsed_intent
            )