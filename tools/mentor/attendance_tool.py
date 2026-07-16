from db.session import (
    AsyncSessionLocal,
)

from db.repositories.mentor.attendance_repository import (
    MentorAttendanceRepository,
)


class AttendanceTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        async with AsyncSessionLocal() as db:

            repo = MentorAttendanceRepository(
                db
            )

            handlers = {

                "summary":
                    repo.get_summary,

                "absent_students":
                    repo.get_absent_students,

                "present_students":
                    repo.get_present_students,

                "late_students":
                    repo.get_late_students,

                "half_day_students":
                    repo.get_half_day_students,

                "attendance_percentage":
                    repo.get_attendance_percentage,

                "low_attendance":
                    repo.get_low_attendance_students,

                "attendance_trend":
                    repo.get_attendance_trend,

                "subject_summary":
                    repo.get_subject_summary,
            }

            handler = handlers.get(
                parsed_intent.view or "summary",
                repo.get_summary,
            )

            return await handler(
                context=context,
                parsed_intent=parsed_intent,
            )