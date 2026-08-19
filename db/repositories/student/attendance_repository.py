from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from utils import IST, ist_today


class AttendanceRepository:

    STATUS_LABELS = {
        1: "present",
        2: "absent",
        3: "late",
        4: "excused",
        5: "healthroom",
    }

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
        target_date: str,
    ):

        query = text(
            """
            SELECT
                id,
                date,
                status,
                entry_time,
                exit_time
            FROM students_studentattendance
            WHERE enrollment_id = :enrollment_id
              AND date = :target_date
            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "target_date": target_date,
            },
        )

        row = result.mappings().first()

        if not row:
            return None

        return dict(row)

    # =====================================================
    # ATTENDANCE RANGE
    # =====================================================

    async def get_attendance_range(
        self,
        enrollment_id: int,
        start_date: str,
        end_date: str,
    ):

        query = text(
            """
            SELECT
                date,
                status
            FROM students_studentattendance
            WHERE enrollment_id = :enrollment_id
              AND date BETWEEN :start_date AND :end_date
            ORDER BY date
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
        start_date: str,
        end_date: str,
        campus_id: int | None = None,
    ):

        # -------------------------------------------------
        # RFID attendance is the source of truth
        # -------------------------------------------------

        holiday_dates = set()

        if (
            campus_id
            and start_date
            and end_date
        ):

            holiday_query = text(
                """
                SELECT start_datetime, end_datetime
                FROM schools_schoolevent
                WHERE event_type = 1
                  AND campus_id = :campus_id
                  AND start_datetime::date <= :end_date
                  AND end_datetime::date >= :start_date
                """
            )

            holiday_result = await self.db.execute(
                holiday_query,
                {
                    "campus_id": campus_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )

            for row in holiday_result.mappings().all():

                start = (
                    row["start_datetime"]
                    .astimezone(IST)
                    .date()
                )

                end = (
                    row["end_datetime"]
                    .astimezone(IST)
                    .date()
                )

                current = start

                while current <= end:

                    holiday_dates.add(current)
                    current += timedelta(days=1)

        record_query = text(
            """
            SELECT DISTINCT date, status
            FROM students_studentattendance
            WHERE enrollment_id = :enrollment_id
              AND date BETWEEN :start_date AND :end_date
            """
        )

        record_result = await self.db.execute(
            record_query,
            {
                "enrollment_id": enrollment_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        record_rows = record_result.mappings().all()
        
        record_dates = {
            row["date"]
            for row in record_rows
        }

        late_day_dates = sorted(
            row["date"]
            for row in record_rows
            if row["status"] == 3
        )

        total_marked_days = len(record_dates)

        working_days = 0

        present_days = 0

        absent_days = 0

        non_working_days = 0

        absent_day_dates = []

        if (
            start_date
            and end_date
        ):

            current = start_date

            today = ist_today()

            while current <= end_date:

                if current <= today:

                    is_weekend = (
                        current.weekday() >= 5
                    )

                    is_holiday = (
                        current in holiday_dates
                    )

                    if is_weekend or is_holiday:

                        non_working_days += 1

                    else:

                        working_days += 1

                        if current in record_dates:

                            present_days += 1

                        else:

                            absent_days += 1

                            absent_day_dates.append(
                                current
                            )

                current += timedelta(days=1)

        attendance_percentage = 0

        if working_days:

            attendance_percentage = round(
                (
                    present_days
                    /
                    working_days
                ) * 100,
                2,
            )

        # -------------------------------------------------
        # Classroom attendance only for RFID present days
        # -------------------------------------------------

        period_query = text(
            """
            SELECT
                ps.date,
                spa.status,
                sp.id AS period_id,
                sp.name AS period_name,
                sp.start_time,
                sp.end_time,
                s.name AS subject_name,
                ps.started_at,
                ps.ended_at,
                ps.is_cancelled
            FROM students_studentperiodattendance spa
            INNER JOIN schools_periodsession ps
                ON ps.id = spa.period_session_id
            INNER JOIN schools_timetableslot ts
                ON ps.timetable_slot_id = ts.id
            INNER JOIN schools_structureperiod sp
                ON ts.period_id = sp.id
            INNER JOIN students_studentsubjectenrollment sse
                ON sse.enrollment_id = spa.enrollment_id
                AND sse.subject_offering_id = ps.subject_offering_id
            LEFT JOIN schools_subjectoffering so
                ON so.id = ps.subject_offering_id
            LEFT JOIN schools_subjectversion sv
                ON sv.id = so.subject_version_id
            LEFT JOIN schools_subject s
                ON s.id = sv.subject_id
            INNER JOIN students_studentattendance sa
                ON sa.enrollment_id = spa.enrollment_id
                AND sa.date = ps.date
            WHERE
                spa.enrollment_id = :enrollment_id
                AND ps.date BETWEEN :start_date AND :end_date
                AND sa.status IN (1,3,4)
            ORDER BY
                ps.date,
                sp.order
            """
        )

        period_result = await self.db.execute(
            period_query,
            {
                "enrollment_id": enrollment_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        period_rows = [
            dict(row)
            for row in period_result.mappings().all()
        ]

        total_periods = len(period_rows)

        for row in period_rows:
            row["status_label"] = (
                self.STATUS_LABELS.get(
                    row["status"],
                    "unknown",
                )
            )

        present_periods = sum(
            1
            for row in period_rows
            if row["status"] == 1
        )

        missed_periods = sum(
            1
            for row in period_rows
            if row["status"] == 2
        )

        late_periods = sum(
            1
            for row in period_rows
            if row["status"] == 3
        )

        excused_periods = sum(
            1
            for row in period_rows
            if row["status"] == 4
        )

        healthroom_periods = sum(
            1
            for row in period_rows
            if row["status"] == 5
        )



        return {

            "present_days":
                present_days,
            
            "working_days":
                working_days,

            "absent_days":
                absent_days,

            "absent_day_dates":
                [
                    date.isoformat()
                    for date in absent_day_dates
                ],

            "non_working_days":
                non_working_days,

            "late_days":
                len(late_day_dates),

            "late_day_dates":
                [
                    date.isoformat()
                    for date in late_day_dates
                ],

            "attendance_percentage":
                attendance_percentage,

            "total_periods":
                total_periods,

            "present_periods":
                present_periods,

            "missed_periods":
                missed_periods,

            "late_periods":
                late_periods,


            "excused_periods":
                excused_periods,

            "healthroom_periods":
                healthroom_periods,

            "period_rows":
                period_rows,
        }

    # =====================================================
    # ATTENDANCE PERCENTAGE
    # =====================================================

    async def get_attendance_percentage(
        self,
        enrollment_id: int,
    ):

        query = text(
            """
            SELECT

                COUNT(*) AS total_marked_days,

                SUM(
                    CASE
                        WHEN status = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS present_days

            FROM students_studentattendance

            WHERE enrollment_id = :enrollment_id
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
            },
        )

        row = result.mappings().first()

        total_marked_days = (
            row["total_marked_days"]
            or 0
        )

        present_days = (
            row["present_days"]
            or 0
        )

        attendance_percentage = 0

        if total_marked_days:

            attendance_percentage = round(
                (
                    present_days
                    /
                    total_marked_days
                ) * 100,
                2,
            )

        return {

            "total_marked_days":
                total_marked_days,

            "present_days":
                present_days,

            "attendance_percentage":
                attendance_percentage,
        }