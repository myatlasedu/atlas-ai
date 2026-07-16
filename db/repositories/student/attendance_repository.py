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
    ):

        # -------------------------------------------------
        # RFID attendance is the source of truth
        # -------------------------------------------------

        attendance_query = text(
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

              AND date BETWEEN :start_date
                          AND :end_date
            """
        )

        attendance_result = await self.db.execute(
            attendance_query,
            {
                "enrollment_id": enrollment_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        attendance = attendance_result.mappings().first()

        total_marked_days = (
            attendance["total_marked_days"]
            or 0
        )

        present_days = (
            attendance["present_days"]
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

        # -------------------------------------------------
        # Classroom attendance only for RFID present days
        # -------------------------------------------------

        period_query = text(
            """
            SELECT

            COUNT(*) AS total_periods,

            SUM(
                CASE
                    WHEN spa.status = 1
                    THEN 1
                    ELSE 0
                END
            ) AS present_periods,

            SUM(
                CASE
                    WHEN spa.status = 2
                    THEN 1
                    ELSE 0
                END
            ) AS missed_periods,

            SUM(
                CASE
                    WHEN spa.status = 3
                    THEN 1
                    ELSE 0
                END
            ) AS late_periods,

            SUM(
                CASE
                    WHEN spa.status = 4
                    THEN 1
                    ELSE 0
                END
            ) AS excused_periods,

            SUM(
                CASE
                    WHEN spa.status = 5
                    THEN 1
                    ELSE 0
                END
            ) AS healthroom_periods

        FROM students_studentperiodattendance spa

        INNER JOIN schools_periodsession ps

            ON ps.id = spa.period_session_id

        INNER JOIN students_studentattendance sa

            ON sa.enrollment_id = spa.enrollment_id
        AND sa.date = ps.date

        WHERE spa.enrollment_id = :enrollment_id

        AND ps.date BETWEEN :start_date
                        AND :end_date

        AND sa.status = 1
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

        periods = period_result.mappings().first()

        return {

            # -------------------------------------------------
            # RFID Attendance
            # -------------------------------------------------

            "total_marked_days":
                total_marked_days,

            "present_days":
                present_days,

            "attendance_percentage":
                attendance_percentage,

            # -------------------------------------------------
            # Classroom Attendance
            # -------------------------------------------------

            "total_periods":
                periods["total_periods"] or 0,

            "present_periods":
                periods["present_periods"] or 0,

            "missed_periods":
                periods["missed_periods"] or 0,

            "late_periods":
                periods["late_periods"] or 0,

            "excused_periods":
                periods["excused_periods"] or 0,

            "healthroom_periods":
                periods["healthroom_periods"] or 0,
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