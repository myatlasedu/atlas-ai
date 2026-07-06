from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AttendanceRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db

    # =====================================================
    # DAILY ATTENDANCE
    # =====================================================

    async def get_daily_attendance(
        self,
        enrollment_id: int,
        target_date: str
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
                "target_date": target_date
            }
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
        end_date: str
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
                "end_date": end_date
            }
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
        end_date: str
    ):

        query = text(
            """
            SELECT

                COUNT(*) AS total_days,

                SUM(
                    CASE
                        WHEN status = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS present_days,

                SUM(
                    CASE
                        WHEN status = 2
                        THEN 1
                        ELSE 0
                    END
                ) AS absent_days,

                SUM(
                    CASE
                        WHEN status = 3
                        THEN 1
                        ELSE 0
                    END
                ) AS late_days,

                SUM(
                    CASE
                        WHEN status = 4
                        THEN 1
                        ELSE 0
                    END
                ) AS half_days

            FROM students_studentattendance

            WHERE enrollment_id = :enrollment_id

            AND date BETWEEN :start_date
            AND :end_date
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        row = result.mappings().first()

        return {
            "total_days": row["total_days"] or 0,
            "present_days": row["present_days"] or 0,
            "absent_days": row["absent_days"] or 0,
            "late_days": row["late_days"] or 0,
            "half_days": row["half_days"] or 0
        }

    # =====================================================
    # ATTENDANCE PERCENTAGE
    # =====================================================

    async def get_attendance_percentage(
        self,
        enrollment_id: int
    ):

        query = text(
            """
            SELECT

                COUNT(*) AS total_days,

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
                "enrollment_id": enrollment_id
            }
        )

        row = result.mappings().first()

        total_days = (
            row["total_days"] or 0
        )

        present_days = (
            row["present_days"] or 0
        )

        attendance_percentage = 0

        if total_days:

            attendance_percentage = round(
                (
                    present_days
                    /
                    total_days
                ) * 100,
                2
            )

        return {
            "total_days": total_days,
            "present_days": present_days,
            "attendance_percentage": attendance_percentage
        }