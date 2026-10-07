from db.session import (
    AsyncSessionLocal,
)

from db.repositories.student.student_performance_repository import (
    StudentPerformanceRepository,
)

from db.repositories.student.assessment_repository import (
    AssessmentRepository,
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

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
            .replace("?", "")
            .replace(".", "")
            .strip()
        )

        role = getattr(context, "role", "student")

        if any(w in query for w in ["mark", "marks", "scorecard", "score card"]):
            async with AsyncSessionLocal() as db:
                asm_repo = AssessmentRepository(db)
                latest = await asm_repo.get_latest_result(context.enrollment_id)
                if latest and (latest.get("isGrade") or latest.get("isGraded") or latest.get("is_graded")):
                    if role == "guardian":
                        direct = "Your child's assessment has been graded. The grade will be available on the report card."
                    else:
                        direct = "Your assessment has been graded. Your grade will be available on the report card."
                else:
                    if role == "guardian":
                        direct = "Your child's grade will be available on the report card once declared."
                    else:
                        direct = "Your grade will be available on the report card once declared."
                return {
                    "module": "student_performance",
                    "direct_answer": direct,
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

                    "direct_answer":
                        (
                            "We're still building your child's overall "
                            "performance insights. A complete analysis will "
                            "appear as more attendance, homework, assessment, "
                            "subject and Atlas data become available."
                            if role == "guardian"
                            else
                            "We're still building your overall performance "
                            "insights. A complete analysis will appear as more "
                            "attendance, homework, assessment, subject and "
                            "Atlas data become available."
                        ),
                }

            return {

                "module":
                    "student_performance",

                **data,

                "cross_analysis":
                    True,

                "llm_context": {
                    "llm_summary":
                        data.get("llm_summary")
                        or {},
                },
            }