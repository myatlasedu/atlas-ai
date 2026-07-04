from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository
)

from intents.student.enums import (
    StudentIntent
)


class AttendanceTool:

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

            repo = AttendanceRepository(
                db
            )

            # =====================================
            # DAILY SUMMARY
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.DAILY_SUMMARY
            ):

                attendance = (
                    await repo.get_daily_attendance(
                        enrollment_id=context.enrollment_id,
                        target_date=parsed_intent.start_date
                    )
                )

                return {
                    "date": (
                        parsed_intent.start_date.isoformat()
                        if parsed_intent.start_date
                        else None
                    ),
                    "attendance": attendance
                }

            # =====================================
            # ATTENDANCE SUMMARY
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.ATTENDANCE_SUMMARY
            ):

                return await repo.get_attendance_summary(
                    enrollment_id=context.enrollment_id,
                    start_date=parsed_intent.start_date,
                    end_date=parsed_intent.end_date
                )

            # =====================================
            # PERFORMANCE
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.STUDENT_PERFORMANCE
            ):

                return await repo.get_attendance_summary(
                    enrollment_id=context.enrollment_id,
                    start_date=parsed_intent.start_date,
                    end_date=parsed_intent.end_date
                )

            # =====================================
            # REPORT
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.STUDENT_REPORT
            ):

                return await repo.get_attendance_summary(
                    enrollment_id=context.enrollment_id,
                    start_date=parsed_intent.start_date,
                    end_date=parsed_intent.end_date
                )

            return {}