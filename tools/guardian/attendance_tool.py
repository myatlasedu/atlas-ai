from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository
)

from llm.builders.attendance_builder import (
    build_attendance_llm_context,
)


class AttendanceTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        if not context.enrollment_id:

            return {

                "module":
                    "attendance",

                "error":
                    "Enrollment ID missing"
            }

        async with AsyncSessionLocal() as db:

            repo = AttendanceRepository(
                db
            )

            payload = {

                "module":
                    "attendance",

                **await repo.get_attendance_summary(
                    enrollment_id=context.enrollment_id,
                    start_date=parsed_intent.start_date,
                    end_date=parsed_intent.end_date,
                )
            }

            payload["llm_context"] = (
                build_attendance_llm_context(
                    payload
                )
            )

            return payload