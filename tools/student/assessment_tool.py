from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.assessment_repository import (
    AssessmentRepository
)

from llm.builders.assessment_builder import (
    build_assessment_llm_context,
)

class AssessmentTool:

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
            .replace("?", "")
            .replace(".", "")
            .strip()
        )

        async with AsyncSessionLocal() as db:

            repo = AssessmentRepository(
                db
            )

            upcoming = (
                await repo.get_upcoming_assessments(
                    context.enrollment_id
                )
            )

            pending = (
                await repo.get_pending_assessments(
                    context.enrollment_id
                )
            )

            latest_result = (
                await repo.get_latest_result(
                    context.enrollment_id
                )
            )

            performance = (
                await repo.get_performance_summary(
                    context.enrollment_id
                )
            )

            highest_assessment = (
                await repo.get_highest_scoring_assessment(
                    context.enrollment_id
                )
            )

            lowest_assessment = (
                await repo.get_lowest_scoring_assessment(
                    context.enrollment_id
                )
            )

            recent_feedback = (
                await repo.get_recent_feedback(
                    context.enrollment_id
                )
            )

            trend_history = (
                await repo.get_assessment_trend(
                    context.enrollment_id
                )
            )

            consistency = (
                await repo.get_consistency_metrics(
                    context.enrollment_id
                )
            )

            risk_assessments = (
                await repo.get_risk_assessments(
                    context.enrollment_id
                )
            )

            trend = {

                "valid": False,

                "direction": None,

                "previous_average": 0,

                "recent_average": 0
            }

            if len(trend_history) >= 5:

                midpoint = (
                    len(trend_history)
                    //
                    2
                )

                first_half = [
                    row["percentage"]
                    for row in trend_history[:midpoint]
                ]

                second_half = [
                    row["percentage"]
                    for row in trend_history[midpoint:]
                ]

                previous_average = round(
                    sum(first_half)
                    /
                    len(first_half),
                    2
                )

                recent_average = round(
                    sum(second_half)
                    /
                    len(second_half),
                    2
                )

                direction = "stable"

                if (
                    recent_average
                    >
                    previous_average + 5
                ):

                    direction = "improving"

                elif (
                    recent_average
                    <
                    previous_average - 5
                ):

                    direction = "declining"

                trend = {

                    "valid": True,

                    "direction":
                        direction,

                    "previous_average":
                        previous_average,

                    "recent_average":
                        recent_average
                }

            insights = []

            recommended_focus = []

            if len(pending) > 0:

                insights.append(
                    "There are upcoming assessments to prepare for."
                )

            if (
                performance.get(
                    "average_percentage",
                    0
                ) < 60
            ):

                insights.append(
                    "Assessment average is below target."
                )

            if (
                performance.get(
                    "lowest_percentage",
                    0
                ) < 40
            ):

                insights.append(
                    "One assessment score is below 40%."
                )
            if trend["direction"] == "declining":

                insights.append(
                    "Recent assessment performance is declining."
                )

            elif trend["direction"] == "improving":

                insights.append(
                    "Recent assessment performance is improving."
                )

            assessment_flags = {

                "below_target_average":
                    performance.get(
                        "average_percentage",
                        0
                    ) < 60,

                "has_low_score":
                    performance.get(
                        "lowest_percentage",
                        0
                    ) < 40,

                "has_pending":
                    len(pending) > 0,

                "has_risk_assessments":
                    len(risk_assessments) > 0,

                "trend":
                    trend["direction"]
            }

            if lowest_assessment:

                recommended_focus.append(
                    lowest_assessment[
                        "title"
                    ]
                )
            
            if risk_assessments:

                insights.append(
                    f"{len(risk_assessments)} "
                    f"assessment(s) are below 50%."
                )

            improvement_opportunities = []

            if len(pending) > 0:

                improvement_opportunities.append(
                    "Prepare for upcoming assessments.",
                )

            if risk_assessments:

                improvement_opportunities.append(
                    "Focus on improving performance in lower-scoring assessments."
                )

            if (
                    consistency.get("rating")
                    in ["Moderate", "Poor"]
            ):

                improvement_opportunities.append(
                     "Aim for more consistent performance across assessments."
                )

            performance_summary = {

                "average_percentage":
                    performance.get(
                        "average_percentage",
                        0
                    ),

                "consistency_rating":
                    consistency.get(
                        "rating"
                    ),

                "best_assessment":
                    (
                        highest_assessment[
                            "title"
                        ]
                        if highest_assessment
                        else None
                    ),

                "weakest_assessment":
                    (
                        lowest_assessment[
                            "title"
                        ]
                        if lowest_assessment
                        else None
                    ),

                "pending_count":
                    len(pending),

                "focus":
                    recommended_focus,

                "insights":
                    insights,
                
                "improvement_opportunities": improvement_opportunities
            }

            payload = {

                "module":
                    "assessment",

                "upcoming_count":
                    len(upcoming),

                "pending_count":
                    len(pending),

                "upcoming":
                    upcoming,

                "pending":
                    pending,

                "latest_result":
                    latest_result,

                "highest_assessment":
                    highest_assessment,

                "lowest_assessment":
                    lowest_assessment,

                "recent_feedback":
                    recent_feedback,

                "performance":
                    performance,

                "assessment_trend": trend,

                "risk_assessments": risk_assessments,

                "improvement_opportunities": improvement_opportunities,
                
                "trend":
                    trend,

                "consistency":
                    consistency,

                "trend_history":
                    trend_history,

                "insights":
                    insights,

                "recommended_focus":
                    recommended_focus,

                "performance_summary":
                    performance_summary,

                "assessment_flags": assessment_flags,
            }

            # =====================================
            # UPCOMING ASSESSMENTS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "upcoming",
                    "coming up",
                    "scheduled",
                    "next assessment",
                    "next test",
                    "next exam",
                    "this week"
                ]
            ):

                if upcoming:

                    first = upcoming[0]

                    payload[
                        "direct_answer"
                    ] = (
                        f"You have "
                        f"{len(upcoming)} upcoming "
                        f"assessment(s). "
                        f"The next one is "
                        f"{first['title']} on "
                        f"{first['assessment_date']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "You currently have no "
                        "upcoming assessments."
                    )

                return payload

            # =====================================
            # PENDING ASSESSMENTS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "pending",
                    "not completed",
                    "unfinished",
                    "missed",
                    "require action",
                    "pending assessment",
                    "pending assessments"
                ]
            ):

                if pending:

                    first = pending[0]

                    payload[
                        "direct_answer"
                    ] = (
                        f"You have "
                        f"{len(pending)} pending "
                        f"assessment(s). "
                        f"The next pending assessment is "
                        f"{first['title']}."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "You currently have no "
                        "pending assessments."
                    )

                return payload

            # =====================================
            # TREND
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "scores improving",
                    "getting better",
                    "assessment trend",
                    "score trend",
                    "performance trend",
                    "improving in assessments",
                    "am i improving",
                    "are my scores improving",
                    "how have my scores changed",
                    "improvement trend",
                    "am i getting better",
                    "are my grades improving",
                    "are my marks improving",
                    "how are my scores changing"
                ]
            ):

                if not trend["valid"]:

                    payload[
                        "direct_answer"
                    ] = (
                        "There is not enough "
                        "assessment history "
                        "to determine a trend."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your recent assessment "
                        f"average is "
                        f"{trend['recent_average']}%, "
                        f"compared with "
                        f"{trend['previous_average']}%. "
                        f"Your assessment performance "
                        f"is currently "
                        f"{trend['direction']}."
                    )

                return payload

            # =====================================
            # CONSISTENCY
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "consistent",
                    "consistency",
                    "stable performance"
                ]
            ):

                payload[
                    "direct_answer"
                ] = (
                    f"You have completed "
                    f"{consistency['count']} graded "
                    f"assessment(s). "
                    f"Consistency rating: "
                    f"{consistency['rating']}. "
                    f"Average score: "
                    f"{consistency['average']}%."
                )

                return payload

            # =====================================
            # HIGHEST SCORE
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "highest",
                    "best assessment",
                    "top assessment",
                    "highest score",
                    "highest scoring"
                ]
            ):

                if highest_assessment:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your highest scoring "
                        f"assessment was "
                        f"{highest_assessment['title']} "
                        f"with "
                        f"{highest_assessment['percentage']}%."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No graded assessments "
                        "found."
                    )

                return payload

            # =====================================
            # LOWEST SCORE
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "lowest",
                    "worst assessment",
                    "lowest score",
                    "lowest scoring",
                    "needs attention"
                ]
            ):

                if lowest_assessment:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your lowest scoring "
                        f"assessment was "
                        f"{lowest_assessment['title']} "
                        f"with "
                        f"{lowest_assessment['percentage']}%."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No graded assessments "
                        "found."
                    )

                return payload

            # =====================================
            # LATEST RESULT
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "latest result",
                    "latest assessment",
                    "latest test",
                    "what was my score",
                    "what marks did i get",
                    "show my grades",
                    "latest grade"
                ]
            ):

                if latest_result:

                    payload[
                        "direct_answer"
                    ] = (
                        f"Your latest assessment "
                        f"was "
                        f"{latest_result['title']}. "
                        f"You scored "
                        f"{latest_result['marks_obtained']}/"
                        f"{latest_result['total_marks']} "
                        f"({latest_result['percentage']}%)."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No assessment results "
                        "available."
                    )

                return payload

            # =====================================
            # FEEDBACK
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "feedback",
                    "teacher comment",
                    "teacher comments",
                    "teacher feedback"
                ]
            ):

                if recent_feedback:

                    latest = recent_feedback[0]

                    payload[
                        "direct_answer"
                    ] = (
                        f"Latest teacher feedback "
                        f"was on "
                        f"{latest['title']}: "
                        f"{latest['teacher_comment']}"
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No assessment feedback "
                        "available."
                    )

                return payload
            
            # =====================================
            # RISK ASSESSMENTS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "risk assessments",
                    "at risk",
                    "weak assessments",
                    "low scoring assessments",
                    "high risk assessments"
                ]
            ):

                if risk_assessments:

                    names = [

                        item["title"]

                        for item in risk_assessments[:3]
                    ]

                    payload[
                        "direct_answer"
                    ] = (
                        "Assessments needing "
                        "attention: "
                        +
                        ", ".join(names)
                        +
                        "."
                    )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "No high-risk assessments "
                        "were identified."
                    )

                return payload

            # =====================================
            # TREND ANALYSIS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "why are my grades dropping",
                    "analyze my assessment trend",
                    "analyse my assessment trend",
                    "what concerns do you see",
                    "what does my assessment trend indicate",
                    "why is my performance declining"
                ]
            ):

                payload[
                    "assessment_trend_analysis"
                ] = True

                return payload

            # =====================================
            # ASSESSMENT ANALYSIS
            # =====================================

            if any(
                phrase in query
                for phrase in [
                    "performing",
                    "performance",
                    "assessment performance",
                    "assessment analysis",
                    "analyze my assessments",
                    "analyze my performance",
                    "how am i doing",
                    "average score",
                    "assessment summary",
                    "assessment review",
                    "improve my assessments"
                ]
            ):

                payload[
                    "assessment_analysis"
                ] = True

                return payload
            
            payload["llm_context"] = (
                    build_assessment_llm_context(
                        payload
                    )
                )

            return payload