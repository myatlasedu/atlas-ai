from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.student_performance_repository import (
    StudentPerformanceRepository,
)


class StudentPerformanceTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.enrollment_id:

            return {
                "module": "student_performance",
                "error": "Enrollment ID missing",
            }

        async with AsyncSessionLocal() as db:

            repo = StudentPerformanceRepository(
                db
            )

            data = await repo.get_performance_data(
                context.enrollment_id
            )

            if not data:

                return {

                    "module":
                        "student_performance",

                    "status":
                        "building",

                    "message":
                        (
                            "We're still building your overall performance insights. "
                            "As more attendance, homework, assessment, subject, "
                            "and Atlas data become available, you'll receive a "
                            "complete performance analysis."
                        ),
                }

            return {

                "module":
                    "student_performance",

                **data,

                "cross_analysis":
                    True,
            }