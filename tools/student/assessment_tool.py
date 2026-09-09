from datetime import (
    timedelta,
    date,
)

from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.assessment_repository import (
    AssessmentRepository
)

from llm.builders.assessment_builder import (
    build_assessment_llm_context,
)

from core.marks_privacy import (
    GRADED_LABEL,
    REPORT_CARD_NOTE_PLURAL,
    GUARDIAN_REPORT_CARD_NOTE_PLURAL,
    graded_message,
    has_grade,
    performance_withheld_message,
    redact_tool_payload,
)

class AssessmentTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        # Marks, grades and percentages are computed for internal signals only
        # (trend, consistency, risk) and stripped before the payload leaves.

        return redact_tool_payload(
            await self._build_payload(
                context,
                parsed_intent
            )
        )

    async def _build_payload(
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

            recent_feedback = (
                await repo.get_recent_feedback(
                    context.enrollment_id
                )
            )

            # No performance verdict is ever produced: status, trends,
            # averages, rankings and "needs attention" flags are all derived
            # from marks, so only schedule facts survive.

            insights = []

            recommended_focus = []

            if len(pending) > 0:

                insights.append(
                    "There are upcoming assessments to prepare for."
                )

            assessment_flags = {

                "has_pending":
                    len(pending) > 0,

                "has_upcoming":
                    len(upcoming) > 0,
            }

            improvement_opportunities = []

            if len(pending) > 0:

                improvement_opportunities.append(
                    "Prepare for upcoming assessments.",
                )

            performance_summary = {

                "pending_count":
                    len(pending),

                "upcoming_count":
                    len(upcoming),

                "insights":
                    insights,

                "improvement_opportunities": improvement_opportunities,
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

                "recent_feedback":
                    recent_feedback,

                "improvement_opportunities": improvement_opportunities,

                "insights":
                    insights,

                "performance_summary":
                    performance_summary,

                "assessment_flags": assessment_flags,
            }

            # =====================================
            # INVALID DATE SHORT CIRCUIT
            # =====================================

            if getattr(parsed_intent, "invalid_date", False):

                payload["direct_answer"] = (
                    "That date isn't valid - please check it and try again."
                )

                return payload

            # =====================================
            # DATE RANGE / MONTH ASSESSMENTS
            # =====================================

            start_date = getattr(parsed_intent, "start_date", None)
            end_date = getattr(parsed_intent, "end_date", None)

            if isinstance(start_date, str):
                try:
                    start_date = date.fromisoformat(start_date[:10])
                except ValueError:
                    start_date = None

            if isinstance(end_date, str):
                try:
                    end_date = date.fromisoformat(end_date[:10])
                except ValueError:
                    end_date = None

            if start_date and end_date:

                records = await repo.get_assessments_by_date_range(
                    context.enrollment_id,
                    start_date,
                    end_date,
                )

                if (
                    start_date.day == 1
                    and (end_date + timedelta(days=1)).day == 1
                    and start_date.month == end_date.month
                ):
                    period_label = start_date.strftime("%B")
                else:
                    period_label = (
                        f"{start_date.strftime('%d %b')} to "
                        f"{end_date.strftime('%d %b')}"
                    )

                graded_records = [
                    r for r in records
                    if r.get("status") == 3 or r.get("marks_obtained") is not None
                ]

                pending_records = [
                    r for r in records
                    if r.get("status") in (1, 2)
                ]

                if graded_records:

                    role = getattr(context, "role", "student")

                    report_card_note = (
                        GUARDIAN_REPORT_CARD_NOTE_PLURAL
                        if role == "guardian"
                        else REPORT_CARD_NOTE_PLURAL
                    )

                    if len(graded_records) == 1:

                        msg = graded_message(
                            graded_records[0]["title"],
                            role=role,
                        )

                    else:

                        lines = []

                        for r in graded_records:

                            lines.append(
                                f"• {r['title']} ({r['assessment_date']}): "
                                f"{GRADED_LABEL}"
                            )

                        heading_owner = (
                            "the student's"
                            if role == "guardian"
                            else "your"
                        )

                        msg = (
                            f"Here are {heading_owner} assessments for "
                            f"{period_label}:\n\n"
                            + "\n".join(lines)
                            + f"\n\n{report_card_note}"
                        )

                    if pending_records:

                        msg += (
                            f"\n\nYou also have {len(pending_records)} pending "
                            f"assessment(s) scheduled for this period."
                        )

                    payload["direct_answer"] = msg

                elif pending_records:

                    payload["direct_answer"] = (
                        f"You have no graded assessments for {period_label}. "
                        f"However, you have {len(pending_records)} pending "
                        f"assessment(s) scheduled for this period."
                    )

                else:

                    payload["direct_answer"] = (
                        f"No assessments found for {period_label}."
                    )

                payload["date_range_assessments"] = records

                return payload

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
            # PERFORMANCE QUESTIONS
            # =====================================
            #
            # Trends, consistency, rankings and averages are all read off the
            # student's marks, so every one of them gets the same answer as a
            # direct request for a grade.

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
                        # f"Your recent assessment "
                        # f"average is "
                        # f"{trend['recent_average']}%, "
                        # f"compared with "
                        # f"{trend['previous_average']}%. "

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
                    f"{consistency['rating']}."
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
                    "highest scoring",
                    "lowest",
                    "worst assessment",
                    "lowest score",
                    "lowest scoring",
                    "needs attention",
                    "average",
                    "averages",
                    "status",
                    "rank",
                    "ranking",
                    "position in class",
                    "class position",
                    "topper",
                    "scorecard",
                    "score card",
                    "report card",
                    "result card",
                    "marksheet",
                    "mark sheet",
                    "how is my child doing",
                    "how is my child performing",
                    "how am i performing",
                    "based on marks",
                ]
            ):

                if highest_assessment:

                    role = getattr(context, "role", "student")
                    grade = (highest_assessment.get("grade") or "").strip()

                    if role == "student" and grade:

                        payload[
                            "direct_answer"
                        ] = (
                            f"Your highest scoring "
                            f"assessment was "
                            f"{highest_assessment['title']} "
                            f"with grade {grade}."
                        )
                    
                    elif role == "guardian" and grade:
        
                        payload["direct_answer"] = (
                            f"The student's highest scoring assessment was "
                            f"{highest_assessment['title']} "
                            f"with grade {grade}."
                        )

                    else:

                        payload[
                            "direct_answer"
                        ] = (
                            "Grade will be shown "
                            "once the results are declared."
                        )

                else:

                payload[
                    "direct_answer"
                ] = performance_withheld_message(role)

                return payload

            # =====================================
            # LATEST RESULT / MARKS / GRADES
            # =====================================

            is_marks_query = (
                getattr(parsed_intent, "asks_for_marks", False)
                or any(
                    phrase in query
                    for phrase in [
                        "latest result",
                        "latest assessment",
                        "latest test",
                        "what was my score",
                        "what marks did i get",
                        "show my grades",
                        "latest grade",
                        "marks",
                        "assessment marks",
                        "my marks",
                        "show my marks",
                        "show my assessment marks",
                        "grade",
                        "grades",
                        "my grade",
                        "my grades",
                        "score",
                        "my score",
                        "scores",
                    ]
                )
            )

            if is_marks_query:

                    role = getattr(context, "role", "student")
                    grade = (lowest_assessment.get("grade") or "").strip()

                    if role == "student" and grade:

                        payload[
                            "direct_answer"
                        ] = (
                            f"Your lowest scoring "
                            f"assessment was "
                            f"{lowest_assessment['title']} "
                            f"with grade {grade}."
                        )
                    
                    elif role == "guardian" and grade:
        
                        payload["direct_answer"] = (
                            f"The student's lowest scoring assessment was "
                            f"{lowest_assessment['title']} "
                            f"with grade {grade}."
                        )

                    else:

                        payload[
                            "direct_answer"
                        ] = (
                            "Your grade will be shown "
                            "once the results are declared."
                        )

                owner = (
                    "The student's"
                    if role == "guardian"
                    else "Your"
                )

                if latest_result:

            # =====================================
            # LATEST RESULT / MARKS / GRADES
            # =====================================

            is_marks_query = (
                getattr(parsed_intent, "asks_for_marks", False)
                or any(
                    phrase in query
                    for phrase in [
                        "latest result",
                        "latest assessment",
                        "latest test",
                        "what was my score",
                        "what marks did i get",
                        "show my grades",
                        "latest grade",
                        "marks",
                        "assessment marks",
                        "my marks",
                        "show my marks",
                        "show my assessment marks",
                        "grade",
                        "grades",
                        "my grade",
                        "my grades",
                        "score",
                        "my score",
                        "scores",
                    ]
                )
            )

            if is_marks_query:

                role = getattr(context, "role", "student")

                    else:

                    grade = (latest_result.get("grade") or "").strip()

                    if role == "student" and grade:

                        payload[
                            "direct_answer"
                        ] = (
                            f"Your grade for "
                            f"{latest_result['title']} is {grade}."
                        )
                    
                    elif role == "guardian" and grade:
        
                        payload["direct_answer"] = (
                            f"The student's latest assessment was "
                            f"{latest_result['title']} "
                            f"with grade {grade}."
                        )

                    else:

                        payload[
                            "direct_answer"
                        ] = (
                            "Your grade will be shown "
                            "once the results are declared."
                        )

                else:

                    payload[
                        "direct_answer"
                    ] = (
                        "Your grade will be shown "
                        "once the results are declared."
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
            # RISK / TREND / PERFORMANCE ANALYSIS
            # =====================================
            #
            # Naming the weak assessments, or analysing a trend, discloses the
            # marks behind them just as plainly as printing the numbers.

            if any(
                phrase in query
                for phrase in [
                    "risk assessments",
                    "at risk",
                    "weak assessments",
                    "low scoring assessments",
                    "high risk assessments",
                    "below 50",
                    "why are my grades dropping",
                    "analyze my assessment trend",
                    "analyse my assessment trend",
                    "what concerns do you see",
                    "what does my assessment trend indicate",
                    "why is my performance declining",
                    "performing",
                    "performance",
                    "assessment performance",
                    "assessment analysis",
                    "analyze my assessments",
                    "analyze my performance",
                    "how am i doing",
                    "average score",
                    "assessment review",
                    "improve my assessments",
                ]
            ):

                role = getattr(context, "role", "student")

                payload[
                    "direct_answer"
                ] = performance_withheld_message(role)

                return payload

            payload["llm_context"] = (
                    build_assessment_llm_context(
                        payload
                    )
                )

            return payload