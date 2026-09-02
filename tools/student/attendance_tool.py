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

            insights = []

            recommended_focus = []

            recommended_actions = []

            present_days = payload.get(
                "present_days",
                0,
            )

            total_marked_days = payload.get(
                "total_marked_days",
                0,
            )

            total_periods = payload.get(
                "total_periods",
                0,
            )

            present_periods = payload.get(
                "present_periods",
                0,
            )

            missed_periods = payload.get(
                "missed_periods",
                0,
            )

            late_periods = payload.get(
                "late_periods",
                0,
            )

            excused_periods = payload.get(
                "excused_periods",
                0,
            )

            healthroom_periods = payload.get(
                "healthroom_periods",
                0,
            )

            attendance_percentage = payload.get(
                "attendance_percentage",
                0,
            )

            # =====================================
            # INSIGHTS
            # =====================================

            if total_marked_days == 0:

                insights.append(
                    "No attendance records are available yet."
                )

            else:

                insights.append(
                    f"You attended school on {present_days} of {total_marked_days} recorded day(s)."
                )

                if total_periods:

                    insights.append(
                        f"You attended {present_periods} of {total_periods} recorded class periods."
                    )

                if missed_periods:

                    insights.append(
                        f"You missed {missed_periods} class period(s)."
                    )

                if late_periods:

                    insights.append(
                        f"You were late for {late_periods} class period(s)."
                    )

                if excused_periods:

                    insights.append(
                        f"{excused_periods} class period(s) were excused."
                    )

                if healthroom_periods:

                    insights.append(
                        f"You visited the health room during {healthroom_periods} class period(s)."
                    )

            # =====================================
            # RECOMMENDED FOCUS
            # =====================================

            if missed_periods:

                recommended_focus.append(
                    "Attend every scheduled class period."
                )

            # =====================================
            # RECOMMENDED ACTIONS
            # =====================================

            if missed_periods:

                recommended_actions.append(
                    "Reduce missed class periods."
                )

            if late_periods:

                recommended_actions.append(
                    "Arrive on time for every class."
                )

            if (
                total_periods > 0
                and
                (
                    present_periods / total_periods
                ) < 0.9
            ):

                recommended_actions.append(
                    "Improve consistency across all scheduled classes."
                )

            payload["insights"] = insights

            payload["recommended_focus"] = (
                recommended_focus
            )

            payload["recommended_actions"] = (
                recommended_actions
            )

            payload["llm_context"] = (
                build_attendance_llm_context(
                    payload,
                )
            )

            return payload