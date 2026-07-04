from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PeriodAttendanceRepository:

    def __init__(
        self,
        db: AsyncSession
    ):
        self.db = db

    async def get_daily_period_attendance(
        self,
        enrollment_id: int,
        target_date
    ):

        query = text(
            """
            SELECT

                ps.date,

                spa.status,

                sp.id AS period_id,
                sp.name AS period_name,
                sp.start_time,
                sp.end_time,

                subj.name AS subject_name,

                ps.started_at,
                ps.ended_at,

                ps.is_cancelled

            FROM students_studentperiodattendance spa

            INNER JOIN schools_periodsession ps
                ON spa.period_session_id = ps.id

            INNER JOIN schools_timetableslot ts
                ON ps.timetable_slot_id = ts.id

            INNER JOIN schools_structureperiod sp
                ON ts.period_id = sp.id

            INNER JOIN schools_timetableassignment ta
                ON ta.slot_id = ts.id

            INNER JOIN schools_subjectoffering so
                ON ta.subject_offering_id = so.id

            INNER JOIN schools_subject subj
                ON so.subject_id = subj.id

            WHERE
                spa.enrollment_id = :enrollment_id
                AND ps.date = :target_date

            ORDER BY
                sp.start_time
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "target_date": target_date
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]