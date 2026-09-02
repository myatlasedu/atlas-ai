from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository,
)

from intents.student.enums import (
    StudentIntent,
)

from llm.builders.attendance_builder import (
    build_attendance_llm_context,
    build_attendance_insights,
)


class AttendanceTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {

                "module":
                    "attendance",

                "error":
                    "Enrollment ID missing",

                "direct_answer":
                    "Unable to load attendance information.",
            }

        async with AsyncSessionLocal() as db:

            repo = AttendanceRepository(
                db
            )

            payload = {

                "module": "attendance",

                **await repo.get_attendance_summary(
                    enrollment_id=context.enrollment_id,
                    start_date=parsed_intent.start_date,
                    end_date=parsed_intent.end_date,
                    campus_id=context.campus_id,
                ),
            }

            # =====================================
            # DAILY SUMMARY
            # =====================================

            if (
                parsed_intent.intent
                ==
                StudentIntent.DAILY_SUMMARY
            ):

                attendance = await repo.get_daily_attendance(
                    enrollment_id=context.enrollment_id,
                    target_date=parsed_intent.start_date,
                )

                payload["date"] = (
                    parsed_intent.start_date.isoformat()
                    if parsed_intent.start_date
                    else None
                )

                payload["attendance"] = attendance

            # =====================================
            # INSIGHTS
            # =====================================

            build_attendance_insights(
                payload
            )           

            payload["llm_context"] = (
                build_attendance_llm_context(
                    payload,
                )
            )

            payload.pop(
                "period_rows",
                None,
            )

            return payload