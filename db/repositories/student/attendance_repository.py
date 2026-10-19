from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AttendanceRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    # =====================================================
    # DAILY ATTENDANCE
    # =====================================================

    async def get_daily_attendance(
        self,
        enrollment_id: int,
        target_date,
    ):
        """Return individual period attendance records for a date."""
        query = text(
            """
            SELECT
                spa.id,
                ps.date,
                spa.period_session_id,
                ps.subject_offering_id,
                spa.enrollment_id,
                spa.status,
                spa.marked_by_id,
                spa.marked_at,
                ps.started_at,
                ps.ended_at
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            WHERE spa.enrollment_id = :enrollment_id
              AND ps.date = :target_date
              AND ps.is_cancelled = FALSE
            ORDER BY ps.started_at NULLS LAST, ps.id
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "target_date": target_date,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # =====================================================
    # ATTENDANCE RANGE
    # =====================================================

    async def get_attendance_range(
        self,
        enrollment_id: int,
        start_date,
        end_date,
    ):
        """Return individual period attendance records in a date range."""
        query = text(
            """
            SELECT
                spa.id,
                ps.date,
                spa.period_session_id,
                ps.subject_offering_id,
                spa.enrollment_id,
                spa.status,
                spa.marked_by_id,
                spa.marked_at,
                ps.started_at,
                ps.ended_at
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            WHERE spa.enrollment_id = :enrollment_id
              AND ps.date BETWEEN :start_date AND :end_date
              AND ps.is_cancelled = FALSE
            ORDER BY ps.date, ps.started_at NULLS LAST, ps.id
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # =====================================================
    # ATTENDANCE SUMMARY
    # =====================================================

    async def get_attendance_summary(
        self,
        enrollment_id: int,
        start_date,
        end_date,
    ):
        """
        Return period-level totals plus daily and monthly aggregates.

        Status rules:
          1 = present
          2 = absent
          3 = late
          4 = excused
          5 = healthroom

        Attendance rate = (present + late) / (present + absent + late).
        Excused and healthroom periods are excluded from the denominator.
        Monthly rows are generated for every calendar month in the requested
        range; months without returned attendance records have data_available
        set to False and a null percentage.
        """

        params = {
            "enrollment_id": enrollment_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        # -------------------------------------------------
        # PERIOD-LEVEL TOTALS
        # -------------------------------------------------

        summary_query = text(
            """
            SELECT
                COUNT(*) AS total_periods,
                COUNT(*) FILTER (WHERE spa.status = 1) AS present_periods,
                COUNT(*) FILTER (WHERE spa.status = 2) AS missed_periods,
                COUNT(*) FILTER (WHERE spa.status = 3) AS late_periods,
                COUNT(*) FILTER (WHERE spa.status = 4) AS excused_periods,
                COUNT(*) FILTER (WHERE spa.status = 5) AS healthroom_periods,
                COUNT(*) FILTER (WHERE spa.status IN (1, 3)) AS attended_periods,
                COUNT(*) FILTER (WHERE spa.status IN (1, 2, 3)) AS eligible_periods
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            WHERE spa.enrollment_id = :enrollment_id
              AND ps.date BETWEEN :start_date AND :end_date
              AND ps.is_cancelled = FALSE
            """
        )

        result = await self.db.execute(summary_query, params)
        row = result.mappings().one()

        total_periods = row["total_periods"] or 0
        present_periods = row["present_periods"] or 0
        missed_periods = row["missed_periods"] or 0
        late_periods = row["late_periods"] or 0
        excused_periods = row["excused_periods"] or 0
        healthroom_periods = row["healthroom_periods"] or 0
        attended_periods = row["attended_periods"] or 0
        eligible_periods = row["eligible_periods"] or 0

        attendance_percentage = (
            round(attended_periods / eligible_periods * 100, 2)
            if eligible_periods
            else 0
        )

        # -------------------------------------------------
        # DAILY AGGREGATES
        # -------------------------------------------------

        daily_query = text(
            """
            SELECT
                ps.date,
                COUNT(*) AS total_periods,
                COUNT(*) FILTER (WHERE spa.status = 1) AS present_periods,
                COUNT(*) FILTER (WHERE spa.status = 2) AS absent_periods,
                COUNT(*) FILTER (WHERE spa.status = 3) AS late_periods,
                COUNT(*) FILTER (WHERE spa.status = 4) AS excused_periods,
                COUNT(*) FILTER (WHERE spa.status = 5) AS healthroom_periods,
                COUNT(*) FILTER (WHERE spa.status IN (1, 3)) AS attended_periods,
                COUNT(*) FILTER (WHERE spa.status IN (1, 2, 3)) AS eligible_periods
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            WHERE spa.enrollment_id = :enrollment_id
              AND ps.date BETWEEN :start_date AND :end_date
              AND ps.is_cancelled = FALSE
            GROUP BY ps.date
            ORDER BY ps.date
            """
        )

        daily_result = await self.db.execute(daily_query, params)
        daily_attendance = []

        for daily_row in daily_result.mappings().all():
            daily_total = daily_row["total_periods"] or 0
            daily_present = daily_row["present_periods"] or 0
            daily_absent = daily_row["absent_periods"] or 0
            daily_late = daily_row["late_periods"] or 0
            daily_excused = daily_row["excused_periods"] or 0
            daily_healthroom = daily_row["healthroom_periods"] or 0
            daily_attended = daily_row["attended_periods"] or 0
            daily_eligible = daily_row["eligible_periods"] or 0

            daily_attendance.append(
                {
                    "date": daily_row["date"].isoformat()
                    if daily_row["date"] else None,
                    "total_periods": daily_total,
                    "present_periods": daily_present,
                    "absent_periods": daily_absent,
                    "missed_periods": daily_absent,
                    "late_periods": daily_late,
                    "excused_periods": daily_excused,
                    "healthroom_periods": daily_healthroom,
                    "attended_periods": daily_attended,
                    "eligible_periods": daily_eligible,
                    "attendance_percentage": (
                        round(daily_attended / daily_eligible * 100, 2)
                        if daily_eligible
                        else None
                    ),
                    "data_available": daily_total > 0,
                }
            )

        # -------------------------------------------------
        # MONTHLY AGGREGATES
        # -------------------------------------------------
        # Generate each calendar month in the requested range, then LEFT JOIN
        # the actual aggregates. This makes missing months explicit without
        # misrepresenting them as 0% attendance.
        monthly_query = text(
            """
            WITH months AS (
                SELECT generate_series(
                    date_trunc('month', CAST(:start_date AS date)),
                    date_trunc('month', CAST(:end_date AS date)),
                    interval '1 month'
                )::date AS month_start
            ),
            monthly_counts AS (
                SELECT
                    date_trunc('month', ps.date)::date AS month_start,
                    COUNT(*) AS total_periods,
                    COUNT(*) FILTER (WHERE spa.status = 1) AS present_periods,
                    COUNT(*) FILTER (WHERE spa.status = 2) AS absent_periods,
                    COUNT(*) FILTER (WHERE spa.status = 3) AS late_periods,
                    COUNT(*) FILTER (WHERE spa.status = 4) AS excused_periods,
                    COUNT(*) FILTER (WHERE spa.status = 5) AS healthroom_periods,
                    COUNT(*) FILTER (WHERE spa.status IN (1, 3)) AS attended_periods,
                    COUNT(*) FILTER (WHERE spa.status IN (1, 2, 3)) AS eligible_periods
                FROM students_studentperiodattendance spa
                INNER JOIN schools_periodsession ps
                    ON ps.id = spa.period_session_id
                WHERE spa.enrollment_id = :enrollment_id
                  AND ps.date BETWEEN :start_date AND :end_date
                  AND ps.is_cancelled = FALSE
                GROUP BY date_trunc('month', ps.date)::date
            )
            SELECT
                months.month_start,
                COALESCE(mc.total_periods, 0) AS total_periods,
                COALESCE(mc.present_periods, 0) AS present_periods,
                COALESCE(mc.absent_periods, 0) AS absent_periods,
                COALESCE(mc.late_periods, 0) AS late_periods,
                COALESCE(mc.excused_periods, 0) AS excused_periods,
                COALESCE(mc.healthroom_periods, 0) AS healthroom_periods,
                COALESCE(mc.attended_periods, 0) AS attended_periods,
                COALESCE(mc.eligible_periods, 0) AS eligible_periods,
                (mc.month_start IS NOT NULL) AS data_available
            FROM months
            LEFT JOIN monthly_counts mc
                ON mc.month_start = months.month_start
            ORDER BY months.month_start
            """
        )

        monthly_result = await self.db.execute(monthly_query, params)
        monthly_attendance = []

        for monthly_row in monthly_result.mappings().all():
            month_start = monthly_row["month_start"]
            month_total = monthly_row["total_periods"] or 0
            month_present = monthly_row["present_periods"] or 0
            month_absent = monthly_row["absent_periods"] or 0
            month_late = monthly_row["late_periods"] or 0
            month_excused = monthly_row["excused_periods"] or 0
            month_healthroom = monthly_row["healthroom_periods"] or 0
            month_attended = monthly_row["attended_periods"] or 0
            month_eligible = monthly_row["eligible_periods"] or 0
            data_available = bool(monthly_row["data_available"])

            monthly_attendance.append(
                {
                    "month": month_start.strftime("%Y-%m"),
                    "month_label": month_start.strftime("%B %Y"),
                    "month_start": month_start.isoformat(),
                    "total_periods": month_total,
                    "present_periods": month_present,
                    "absent_periods": month_absent,
                    "missed_periods": month_absent,
                    "late_periods": month_late,
                    "excused_periods": month_excused,
                    "healthroom_periods": month_healthroom,
                    "attended_periods": month_attended,
                    "eligible_periods": month_eligible,
                    "attendance_percentage": (
                        round(month_attended / month_eligible * 100, 2)
                        if data_available and month_eligible
                        else None
                    ),
                    "data_available": data_available,
                }
            )

        # -------------------------------------------------
        # WEEKLY AGGREGATES (Monday-Sunday calendar weeks)
        # -------------------------------------------------
        # Empty weeks are explicit but remain unavailable (percentage=None).
        weekly_query = text(
            """
            WITH weeks AS (
                SELECT generate_series(
                    date_trunc('week', CAST(:start_date AS date)),
                    date_trunc('week', CAST(:end_date AS date)),
                    interval '1 week'
                )::date AS week_start
            ),
            weekly_counts AS (
                SELECT
                    date_trunc('week', ps.date)::date AS week_start,
                    COUNT(*) AS total_periods,
                    COUNT(*) FILTER (WHERE spa.status = 1) AS present_periods,
                    COUNT(*) FILTER (WHERE spa.status = 2) AS absent_periods,
                    COUNT(*) FILTER (WHERE spa.status = 3) AS late_periods,
                    COUNT(*) FILTER (WHERE spa.status = 4) AS excused_periods,
                    COUNT(*) FILTER (WHERE spa.status = 5) AS healthroom_periods,
                    COUNT(*) FILTER (WHERE spa.status IN (1, 3)) AS attended_periods,
                    COUNT(*) FILTER (WHERE spa.status IN (1, 2, 3)) AS eligible_periods
                FROM students_studentperiodattendance spa
                INNER JOIN schools_periodsession ps ON ps.id = spa.period_session_id
                WHERE spa.enrollment_id = :enrollment_id
                  AND ps.date BETWEEN :start_date AND :end_date
                  AND ps.is_cancelled = FALSE
                GROUP BY date_trunc('week', ps.date)::date
            )
            SELECT
                weeks.week_start,
                COALESCE(wc.total_periods, 0) AS total_periods,
                COALESCE(wc.present_periods, 0) AS present_periods,
                COALESCE(wc.absent_periods, 0) AS absent_periods,
                COALESCE(wc.late_periods, 0) AS late_periods,
                COALESCE(wc.excused_periods, 0) AS excused_periods,
                COALESCE(wc.healthroom_periods, 0) AS healthroom_periods,
                COALESCE(wc.attended_periods, 0) AS attended_periods,
                COALESCE(wc.eligible_periods, 0) AS eligible_periods,
                (wc.week_start IS NOT NULL) AS data_available
            FROM weeks
            LEFT JOIN weekly_counts wc ON wc.week_start = weeks.week_start
            ORDER BY weeks.week_start
            """
        )
        weekly_result = await self.db.execute(weekly_query, params)
        weekly_attendance = []
        for weekly_row in weekly_result.mappings().all():
            week_start = weekly_row["week_start"]
            week_end = week_start + timedelta(days=6)
            week_total = weekly_row["total_periods"] or 0
            week_present = weekly_row["present_periods"] or 0
            week_absent = weekly_row["absent_periods"] or 0
            week_late = weekly_row["late_periods"] or 0
            week_excused = weekly_row["excused_periods"] or 0
            week_healthroom = weekly_row["healthroom_periods"] or 0
            week_attended = weekly_row["attended_periods"] or 0
            week_eligible = weekly_row["eligible_periods"] or 0
            available = bool(weekly_row["data_available"])
            weekly_attendance.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "week_label": f"{max(week_start, start_date).strftime('%d %b')}–{min(week_end, end_date).strftime('%d %b %Y')}",
                "total_periods": week_total,
                "present_periods": week_present,
                "absent_periods": week_absent,
                "missed_periods": week_absent,
                "late_periods": week_late,
                "excused_periods": week_excused,
                "healthroom_periods": week_healthroom,
                "attended_periods": week_attended,
                "eligible_periods": week_eligible,
                "attendance_percentage": round(week_attended / week_eligible * 100, 2) if available and week_eligible else None,
                "data_available": available,
            })

        return {
            # Requested range metadata
            "requested_start_date": (
                start_date.isoformat()
                if hasattr(start_date, "isoformat")
                else str(start_date) if start_date is not None else None
            ),
            "requested_end_date": (
                end_date.isoformat()
                if hasattr(end_date, "isoformat")
                else str(end_date) if end_date is not None else None
            ),

            # Period-level summary
            "total_periods": total_periods,
            "present_periods": present_periods,
            "missed_periods": missed_periods,
            "late_periods": late_periods,
            "excused_periods": excused_periods,
            "healthroom_periods": healthroom_periods,
            "attended_periods": attended_periods,
            "eligible_periods": eligible_periods,
            "attendance_percentage": attendance_percentage,

            # Explicit aggregate series
            "daily_attendance": daily_attendance,
            "monthly_attendance": monthly_attendance,
            "weekly_attendance": weekly_attendance,
            "weekly_data_available": any(week["data_available"] for week in weekly_attendance),
            "weeks_requested": len(weekly_attendance),
            "monthly_data_available": any(
                month["data_available"] for month in monthly_attendance
            ),
            "monthly_records_returned": sum(
                1 for month in monthly_attendance if month["data_available"]
            ),
            "months_requested": len(monthly_attendance),
        }

    # =====================================================
    # ATTENDANCE PERCENTAGE
    # =====================================================

    async def get_attendance_percentage(
        self,
        enrollment_id: int,
    ):
        """Calculate attendance percentage from all recorded periods."""

        query = text(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE spa.status IN (1, 2, 3)
                ) AS total_eligible_periods,
                COUNT(*) FILTER (
                    WHERE spa.status IN (1, 3)
                ) AS attended_periods,
                COUNT(*) FILTER (
                    WHERE spa.status = 1
                ) AS present_periods,
                COUNT(*) FILTER (
                    WHERE spa.status = 2
                ) AS absent_periods,
                COUNT(*) FILTER (
                    WHERE spa.status = 3
                ) AS late_periods,
                COUNT(*) FILTER (
                    WHERE spa.status = 4
                ) AS excused_periods,
                COUNT(*) FILTER (
                    WHERE spa.status = 5
                ) AS healthroom_periods
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            WHERE spa.enrollment_id = :enrollment_id
              AND ps.is_cancelled = FALSE
            """
        )

        result = await self.db.execute(
            query,
            {"enrollment_id": enrollment_id},
        )
        row = result.mappings().one()

        total_eligible_periods = row["total_eligible_periods"] or 0
        attended_periods = row["attended_periods"] or 0

        attendance_percentage = (
            round(attended_periods / total_eligible_periods * 100, 2)
            if total_eligible_periods
            else 0
        )

        return {
            "total_marked_days": total_eligible_periods,
            "present_days": row["present_periods"] or 0,
            "absent_days": row["absent_periods"] or 0,
            "late_days": row["late_periods"] or 0,
            "excused_periods": row["excused_periods"] or 0,
            "healthroom_periods": row["healthroom_periods"] or 0,
            "total_eligible_periods": total_eligible_periods,
            "attended_periods": attended_periods,
            "attendance_percentage": attendance_percentage,
        }
