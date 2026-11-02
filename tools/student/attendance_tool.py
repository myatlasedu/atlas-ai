from datetime import date
import re

from utils import ist_today

from sqlalchemy import text

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
                "module": "attendance",
                "error": "Enrollment ID missing",
                "direct_answer": (
                    "Unable to load attendance information."
                ),
            }

        start_date = parsed_intent.start_date
        end_date = parsed_intent.end_date
        intent = parsed_intent.intent

        query = self._query_text(parsed_intent)
        comparison_granularity = self._get_comparison_granularity(
            intent=intent,
            start_date=start_date,
            end_date=end_date,
            query=query,
        )
        weekly_comparison = comparison_granularity == "weekly"
        monthly_comparison = comparison_granularity == "monthly"
        explicit_daily = self._is_explicit_daily_request(query)
        daily_comparison = (
            comparison_granularity == "daily"
            and explicit_daily
        )

        async with AsyncSessionLocal() as db:
            today = ist_today()

            # Comparison requests use a consistent backend-defined window.
            # Explicit day-wise requests keep their parser-resolved dates.
            if daily_comparison:
                # "Daily comparison" means compare individual attendance
                # days across the current month, not just the parser's
                # default single-day date range.
                start_date = today.replace(day=1)
                end_date = today
            elif weekly_comparison and not explicit_daily:
                start_date = today.replace(day=1)
                end_date = today
            elif monthly_comparison and not explicit_daily:
                academic_year_range = await self._get_active_academic_year_range(
                    db=db,
                    enrollment_id=context.enrollment_id,
                    today=today,
                )
                if academic_year_range is None:
                    return {
                        "module": "attendance",
                        "error": "No active academic year was found for this enrollment.",
                        "direct_answer": (
                            "Unable to load the monthly attendance comparison "
                            "because no active academic year was found."
                        ),
                    }
                start_date, end_date = academic_year_range

            start_date_str = (
                start_date.isoformat()
                if start_date
                else None
            )

            end_date_str = (
                end_date.isoformat()
                if end_date
                else None
            )

            # =====================================
            # FETCH ATTENDANCE
            # =====================================

            repo = AttendanceRepository(db)

            summary = await repo.get_attendance_summary(
                enrollment_id=context.enrollment_id,
                start_date=start_date,
                end_date=end_date,
            )

            payload = {
                "module": "attendance",
                **summary,
            }

            # =====================================
            # REQUESTED RANGE METADATA
            # =====================================

            payload["requested_start_date"] = (
                start_date_str
            )

            payload["requested_end_date"] = (
                end_date_str
            )

            payload["comparison_granularity"] = comparison_granularity
            payload["chart_allowed"] = False
            payload["chart_policy"] = "single_day_no_chart"
            if comparison_granularity == "weekly":
                buckets = payload.get("weekly_attendance") or []
                comparable = sum(1 for item in buckets if item.get("data_available"))
                payload["chart_allowed"] = comparable > 1
                payload["chart_policy"] = "weekly_comparison" if comparable > 1 else "insufficient_comparison_buckets"
            elif comparison_granularity == "monthly":
                buckets = payload.get("monthly_attendance") or []
                comparable = sum(1 for item in buckets if item.get("data_available"))
                payload["chart_allowed"] = comparable > 1
                payload["chart_policy"] = "monthly_comparison" if comparable > 1 else "insufficient_comparison_buckets"
            elif comparison_granularity == "daily":
                # A range-level day-by-day request may be charted only when it
                # contains more than one date; a single-day request never is.
                buckets = payload.get("daily_attendance") or []
                payload["chart_allowed"] = len([x for x in buckets if x.get("data_available", True)]) > 1 and self._is_explicit_daily_request(query)
                payload["chart_policy"] = "daily_comparison" if payload["chart_allowed"] else "single_day_no_chart"

            # Preserve repository-provided aggregates.
            # Never reconstruct monthly totals from daily rows.
            payload["monthly_attendance"] = (
                payload.get("monthly_attendance") or []
            )

            payload["daily_attendance"] = (
                payload.get("daily_attendance") or []
            )

            payload["weekly_attendance"] = (
                payload.get("weekly_attendance") or []
            )

            # =====================================
            # DAILY SUMMARY
            # =====================================

            if intent == StudentIntent.DAILY_SUMMARY:

                attendance = await repo.get_daily_attendance(
                    enrollment_id=context.enrollment_id,
                    target_date=start_date,
                )

                payload["date"] = start_date_str
                payload["attendance"] = attendance

            # =====================================
            # INSIGHTS
            # =====================================

            insights = []
            recommended_focus = []
            recommended_actions = []

            total_periods = (
                payload.get("total_periods", 0) or 0
            )

            present_periods = (
                payload.get("present_periods", 0) or 0
            )

            missed_periods = (
                payload.get("missed_periods", 0) or 0
            )

            late_periods = (
                payload.get("late_periods", 0) or 0
            )

            excused_periods = (
                payload.get("excused_periods", 0) or 0
            )

            healthroom_periods = (
                payload.get("healthroom_periods", 0) or 0
            )

            attended_periods = payload.get(
                "attended_periods",
                present_periods + late_periods,
            ) or 0

            eligible_periods = payload.get(
                "eligible_periods",
                present_periods
                + missed_periods
                + late_periods,
            ) or 0

            attendance_percentage = (
                payload.get("attendance_percentage", 0) or 0
            )

            if total_periods == 0:

                insights.append(
                    "No attendance records are available "
                    "for the requested date range."
                )

            else:

                insights.append(
                    f"You attended {attended_periods} of "
                    f"{eligible_periods} eligible class period(s)."
                )

                insights.append(
                    f"Your attendance percentage is "
                    f"{attendance_percentage}%."
                )

                if present_periods:
                    insights.append(
                        f"You were marked present for "
                        f"{present_periods} class period(s)."
                    )

                if missed_periods:
                    insights.append(
                        f"You were marked absent for "
                        f"{missed_periods} class period(s)."
                    )

                if late_periods:
                    insights.append(
                        f"You were late for "
                        f"{late_periods} class period(s)."
                    )

                if excused_periods:
                    insights.append(
                        f"{excused_periods} class period(s) "
                        "were excused."
                    )

                if healthroom_periods:
                    insights.append(
                        "You visited the health room during "
                        f"{healthroom_periods} class period(s)."
                    )

            # =====================================
            # RECOMMENDED FOCUS
            # =====================================

            if missed_periods:
                recommended_focus.append(
                    "Attend every scheduled class period."
                )

            if late_periods:
                recommended_focus.append(
                    "Arrive on time for every class."
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
                    "Improve punctuality in class."
                )

            if (
                eligible_periods > 0
                and attendance_percentage < 90
            ):
                recommended_actions.append(
                    "Improve consistency across scheduled classes."
                )

            payload["insights"] = insights

            payload["recommended_focus"] = (
                recommended_focus
            )

            payload["recommended_actions"] = (
                recommended_actions
            )

            # =====================================
            # LLM CONTEXT
            # =====================================

            payload["llm_context"] = (
                build_attendance_llm_context(
                    payload,
                )
            )

            # Keep these removed from the LLM context
            # to avoid repeating the same metrics.
            # The original payload retains its own fields.
            for key in (
                "metrics",
                "period_breakdown",
            ):
                payload["llm_context"].pop(
                    key,
                    None,
                )

            return payload

    @staticmethod
    def _query_text(parsed_intent) -> str:
        return str(
            getattr(parsed_intent, "original_query", None)
            or getattr(parsed_intent, "raw_query", None)
            or getattr(parsed_intent, "query", None)
            or ""
        ).strip().lower()

    @staticmethod
    def _is_explicit_daily_request(query: str) -> bool:
        """Recognize day-level comparisons even when words intervene.

        Examples: "daily attendance comparison", "daily comparison",
        "attendance day-wise", and "attendance broken down per day".
        "Daily attendance" by itself is not necessarily a comparison.
        """
        normalized = re.sub(r"\s+", " ", (query or "").strip().lower())
        exact_phrases = (
            "day wise", "day-wise", "day by day", "daily comparison",
            "daily breakdown", "date-wise", "date wise", "per day", "each day",
        )
        if any(phrase in normalized for phrase in exact_phrases):
            return True
        # Allow qualifiers between "daily" and "comparison", e.g.
        # "daily attendance comparison?".
        return bool(re.search(r"\bdaily\b.*\bcomparison\b", normalized))

    @staticmethod
    def _get_comparison_granularity(intent, start_date, end_date, query=""):
        """Choose the requested series from the user's wording first."""
        query = (query or "").lower()
        if AttendanceTool._is_explicit_daily_request(query):
            return "daily"
        if re.search(r"\b(weekly|week by week|week-by-week|each week|every week|week wise|week-wise)\b", query):
            return "weekly"
        if re.search(r"\b(monthly|month by month|month-by-month|each month|every month|all months|last 6 months|last six months|last 12 months|last twelve months)\b", query):
            return "monthly"

        intent_name = getattr(intent, "name", str(intent)).lower()
        if intent == StudentIntent.DAILY_SUMMARY or "daily" in intent_name:
            return "daily"
        if "monthly" in intent_name:
            return "monthly"
        if start_date and end_date:
            if start_date == end_date:
                return "daily"
            if start_date.year != end_date.year or start_date.month != end_date.month:
                return "monthly"
            return "summary"
        return "summary"

    @staticmethod
    async def _get_active_academic_year_range(
        db,
        enrollment_id,
        today: date,
    ):
        """
        Read the academic year linked to the enrollment.

        No database writes or Django model imports are used.
        """

        query = text(
            """
            SELECT
                ay.from_date,
                ay.to_date
            FROM schools_academicyear AS ay
            INNER JOIN students_studentenrollment AS se
                ON se.academic_year_id = ay.id
            WHERE se.id = :enrollment_id
              AND ay.from_date <= :today
              AND ay.to_date >= :today
            ORDER BY ay.from_date DESC
            LIMIT 1
            """
        )

        result = await db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "today": today,
            },
        )

        row = result.mappings().first()

        if row is None:
            return None

        academic_year_start = row["from_date"]

        start_date = academic_year_start.replace(
            day=1,
        )

        # Include records up to today. The repository's
        # monthly aggregation should still include the
        # current month as a bucket.
        end_date = today

        return start_date, end_date
