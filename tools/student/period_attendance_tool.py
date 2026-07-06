from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.period_attendance_repository import (
    PeriodAttendanceRepository
)

from intents.student.enums import (
    StudentIntent
)


class PeriodAttendanceTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        if not context.enrollment_id:

            return {
                "error": "Enrollment ID missing"
            }

        async with AsyncSessionLocal() as db:

            repo = (
                PeriodAttendanceRepository(
                    db
                )
            )

            if (
                parsed_intent.intent
                ==
                StudentIntent.DAILY_SUMMARY
            ):

                return await repo.get_daily_period_attendance(
                    enrollment_id=context.enrollment_id,
                    target_date=parsed_intent.start_date
                )

            return {}