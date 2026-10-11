from datetime import date

from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.attendance_repository import (
    AttendanceRepository
)

from llm.builders.attendance_builder import (
    build_attendance_llm_context,
)


def _as_date(value):

    if isinstance(value, str):

        return date.fromisoformat(value)

    return value


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
                    "Enrollment ID missing",

                "direct_answer":
                    "Unable to load your child's attendance information.",
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
                    start_date=_as_date(parsed_intent.start_date),
                    end_date=_as_date(parsed_intent.end_date),
                )
            }

            total_marked_days = payload["total_marked_days"]

            total_periods = payload["total_periods"]

            missed_periods = payload["missed_periods"]

            late_periods = payload["late_periods"]

            late_days = payload["late_days"]

            attended_periods = (
                payload["present_periods"]
                + late_periods
            )

            expected_periods = (
                total_periods
                - payload["excused_periods"]
                - payload["healthroom_periods"]
            )

            # =====================================
            # INSIGHTS
            # =====================================

            insights = []

            if total_marked_days == 0:

                insights.append(
                    "No attendance records are available for your child yet."
                )

            else:

                insights.append(
                    f"Your child attended school on {payload['present_days']} "
                    f"of {total_marked_days} recorded day(s)."
                )

                # Only what actually happened: a zero count is not news.

                for count, sentence in (
                    (late_days, "Your child arrived late at school on {} day(s)."),
                    (payload["half_days"], "{} day(s) were half days."),
                    (payload["absent_days"], "Your child was marked absent on {} day(s)."),
                    (missed_periods, "Your child missed {} class period(s)."),
                    (late_periods, "Your child was late for {} class period(s)."),
                    (payload["excused_periods"], "{} class period(s) were excused."),
                    (payload["healthroom_periods"], "Your child visited the health room during {} class period(s)."),
                ):

                    if count:

                        insights.append(
                            sentence.format(count)
                        )

                if total_periods:

                    insights.insert(
                        1,
                        f"Your child attended {attended_periods} of "
                        f"{total_periods} recorded class periods.",
                    )

            # =====================================
            # RECOMMENDED ACTIONS
            # =====================================

            recommended_actions = []

            if missed_periods:

                recommended_actions.append(
                    "Check with your child about the missed class periods."
                )

            if late_days or late_periods:

                recommended_actions.append(
                    "Help your child arrive on time."
                )

            if (
                expected_periods > 0
                and
                (
                    attended_periods / expected_periods
                ) < 0.9
            ):

                recommended_actions.append(
                    "Encourage consistent attendance across all scheduled classes."
                )

            payload["insights"] = insights

            payload["recommended_actions"] = (
                recommended_actions
            )

            payload["llm_context"] = (
                build_attendance_llm_context(
                    payload
                )
            )

            return payload
