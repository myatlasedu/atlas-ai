from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.assessment_repository import (
    AssessmentRepository
)

from llm.builders.assessment_builder import (
    build_assessment_llm_context,
)


def format_graded_response(title: str, role: str) -> str:
    if role == "guardian":
        return f"Your child's {title} assessment has been Graded. The grade will be available on the report card."
    return f"Your {title} assessment has been Graded. Your grade will be available on the report card."


def format_ungraded_response(title: str | None, role: str) -> str:
    if title:
        if role == "guardian":
            return f"Your child's {title} assessment has not been graded yet. The grade will be available on the report card once declared."
        return f"Your {title} assessment has not been graded yet. Your grade will be available on the report card once declared."
    if role == "guardian":
        return "The grade will be available on the report card once declared."
    return "Your grade will be available on the report card once declared."


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

            if len(trend_history) >= 5 and all("percentage" in row for row in trend_history):

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

            if trend["direction"] == "declining":

                insights.append(
                    "Recent assessment performance is declining."
                )

            elif trend["direction"] == "improving":

                insights.append(
                    "Recent assessment performance is improving."
                )

            assessment_flags = {

                "has_pending":
                    len(pending) > 0,

                "trend":
                    trend["direction"]
            }

            if lowest_assessment:

                recommended_focus.append(
                    lowest_assessment[
                        "title"
                    ]
                )
            
            improvement_opportunities = []

            if len(pending) > 0:

                improvement_opportunities.append(
                    "Prepare for upcoming assessments.",
                )

            if (
                    consistency.get("rating")
                    in ["Moderate", "Poor"]
            ):

                improvement_opportunities.append(
                     "Aim for more consistent performance across assessments."
                )

            performance_summary = {

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

            role = getattr(context, "role", "student")

            # =====================================================
            # MARKS / GRADES / STATUS / SCORES / PERCENTAGES /
            # AVERAGES / HIGHEST / LOWEST / RISK / SCORECARD /
            # PERFORMANCE / SUMMARY / EVALUATION
            # =====================================================

            all_assessments = await repo.get_all_student_assessments(
                context.enrollment_id
            )

            # Check if a specific assessment title is referenced in query
            matched_assessment = None
            for asm in all_assessments:
                asm_title = (asm.get("title") or "").lower().strip()
                if asm_title and asm_title in query:
                    matched_assessment = asm
                    break

            if matched_assessment:
                is_graded = bool(
                    matched_assessment.get("isGrade")
                    or matched_assessment.get("isGraded")
                    or matched_assessment.get("is_graded")
                    or matched_assessment.get("status") == 3
                )
                if is_graded:
                    payload["direct_answer"] = format_graded_response(
                        matched_assessment["title"], role
                    )
                else:
                    payload["direct_answer"] = format_ungraded_response(
                        matched_assessment["title"], role
                    )
                return payload

            # Check if date range / month filter is requested
            start_date = getattr(parsed_intent, "start_date", None)
            end_date = getattr(parsed_intent, "end_date", None)
            months = [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ]
            has_month_word = any(m in query for m in months) or "month" in query

            if start_date or end_date or has_month_word:
                start_date_str = str(start_date)[:10] if start_date else None
                end_date_str = str(end_date)[:10] if end_date else None
                range_assessments = []
                for asm in all_assessments:
                    asm_date_str = str(asm.get("assessment_date") or "")[:10]
                    if asm_date_str:
                        if start_date_str and asm_date_str < start_date_str:
                            continue
                        if end_date_str and asm_date_str > end_date_str:
                            continue
                        range_assessments.append(asm)

                graded_in_range = [
                    asm for asm in range_assessments
                    if (
                        asm.get("isGrade")
                        or asm.get("isGraded")
                        or asm.get("is_graded")
                        or asm.get("status") == 3
                    )
                ]
                if graded_in_range:
                    payload["direct_answer"] = format_graded_response(
                        graded_in_range[0]["title"], role
                    )
                elif range_assessments:
                    payload["direct_answer"] = format_ungraded_response(
                        range_assessments[0]["title"], role
                    )
                else:
                    payload["direct_answer"] = format_ungraded_response(
                        None, role
                    )
                return payload

            # Check if asking for highest scoring assessment
            if any(p in query for p in ["highest", "best assessment", "top assessment"]):
                target = highest_assessment or latest_result
                if target:
                    payload["direct_answer"] = format_graded_response(
                        target["title"], role
                    )
                else:
                    payload["direct_answer"] = format_ungraded_response(
                        None, role
                    )
                return payload

            # Check if asking for lowest scoring assessment
            if any(p in query for p in ["lowest", "worst assessment", "weakest assessment"]):
                target = lowest_assessment or latest_result
                if target:
                    payload["direct_answer"] = format_graded_response(
                        target["title"], role
                    )
                else:
                    payload["direct_answer"] = format_ungraded_response(
                        None, role
                    )
                return payload

            # Check if asking for below 50% / risk assessments
            if any(p in query for p in ["below 50", "under 50", "less than 50", "at risk", "risk assessment", "risk assessments"]):
                target = (risk_assessments[0] if risk_assessments else None) or latest_result
                if target:
                    payload["direct_answer"] = format_graded_response(
                        target["title"], role
                    )
                else:
                    payload["direct_answer"] = format_ungraded_response(
                        None, role
                    )
                return payload

            # All other assessment status, result, performance, marks, scorecard, average, percentage, trend, consistency queries
            target = latest_result or highest_assessment or lowest_assessment
            if target:
                payload["direct_answer"] = format_graded_response(
                    target["title"], role
                )
            else:
                payload["direct_answer"] = format_ungraded_response(
                    None, role
                )
            return payload