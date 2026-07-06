from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository
)


class AttendanceTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        if not context.enrollment_id:

            return {
                "error":
                    "Enrollment ID missing"
            }

        async with AsyncSessionLocal() as db:

            repo = AttendanceRepository(
                db
            )

            attendance = (
                await repo.get_attendance_percentage(
                    context.enrollment_id
                )
            )

            return {

                "module":
                    "attendance",

                **attendance
            }