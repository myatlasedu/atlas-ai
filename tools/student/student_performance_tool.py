from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.student_performance_repository import (
    StudentPerformanceRepository
)


class StudentPerformanceTool:

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

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
            .strip()
        )

        async with AsyncSessionLocal() as db:

            repo = (
                StudentPerformanceRepository(
                    db
                )
            )

            data = (
                await repo.get_performance_data(
                    context.enrollment_id
                )
            )

            print("PERFORMANCE DATA:", data)

            if not data:

                return {
                    "module": "student_performance",
                    "status": "building",
                    "message": (
                        "We're still building your performance insights. "
                        "As more attendance, homework, assessments, and Atlas "
                        "data become available, you'll start seeing a complete analysis."
                    )
                }


            payload = {

                "module":
                    "student_performance",

                **data,

                "cross_analysis":
                    True
            }

            

            payload = {

                "module":
                    "student_performance",

                **data,

                "cross_analysis":
                    True
            }

            # ==========================
            # STRENGTHS
            # ==========================

            if any(
                phrase in query
                for phrase in [
                    "strength",
                    "strengths",
                    "what am i good at"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    "Your key strengths are: "
                    +
                    ", ".join(
                        data["strengths"]
                    )
                )

                return payload

            # ==========================
            # WEAKNESSES
            # ==========================

            if any(
                phrase in query
                for phrase in [
                    "weakness",
                    "weaknesses",
                    "what am i bad at",
                    "weak areas"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    "Areas needing attention: "
                    +
                    ", ".join(
                        data["weaknesses"]
                    )
                )

                return payload

            # ==========================
            # FOCUS
            # ==========================

            if any(
                phrase in query
                for phrase in [
                    "focus",
                    "focus on",
                    "what should i improve",
                    "what should i work on",
                    "what should i focus on"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    "Recommended focus areas: "
                    +
                    ", ".join(
                        data[
                            "recommended_focus"
                        ]
                    )
                )

                return payload

            # ==========================
            # RISK
            # ==========================

            if any(
                phrase in query
                for phrase in [
                    "risk",
                    "at risk",
                    "academic risk"
                ]
            ):

                risk_count = sum(
                    1
                    for value
                    in data[
                        "signals"
                    ].values()
                    if value is True
                )

                if risk_count:

                    payload[
                        "direct_answer"
                    ] = (
                        f"{risk_count} academic "
                        f"risk indicator(s) "
                        f"were identified."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No significant academic "
                        "risk indicators found."
                    )

                return payload

            return payload