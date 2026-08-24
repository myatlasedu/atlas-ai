from datetime import date
from datetime import timedelta

from sqlalchemy import text
import time
from utils import ist_today
class HomeworkRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_pending_homework(
        self,
        enrollment_id: int
    ):

        query = text(
            """
            SELECT

                h.id,
                h.title,
                h.due_date,
                h.total_marks

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            WHERE

                hm.enrollment_id = :enrollment_id

            AND NOT EXISTS (

                SELECT 1

                FROM students_homeworksubmission hs

                WHERE
                    hs.homework_id = h.id
                AND
                    hs.enrollment_id = :enrollment_id
            )

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        
        )
        print(
            f"get_pending_homework: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        return [
            dict(row)
            for row in result.mappings()
        ]

    async def get_overdue_homework(
        self,
        enrollment_id: int
    ):

        query = text(
            """
            SELECT

                h.id,
                h.title,
                h.due_date

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            WHERE

                hm.enrollment_id = :enrollment_id

            AND h.due_date < NOW()

            AND NOT EXISTS (

                SELECT 1

                FROM students_homeworksubmission hs

                WHERE
                    hs.homework_id = h.id
                AND
                    hs.enrollment_id = :enrollment_id
            )

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )
        print(
            f"get_overdue_homework: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        return [
            dict(row)
            for row in result.mappings()
        ]

    async def get_due_today(
        self,
        enrollment_id: int
    ):

        today = ist_today()

        query = text(
            """
            SELECT

                h.id,
                h.title,
                h.due_date

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            WHERE

                hm.enrollment_id = :enrollment_id

            AND DATE(h.due_date) = :today

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "today": today
            }
        )
        print(
            f"get_due_today: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        return [
            dict(row)
            for row in result.mappings()
        ]

    async def get_due_tomorrow(
        self,
        enrollment_id: int
    ):

        tomorrow = (
            ist_today()
            + timedelta(days=1)
        )

        query = text(
            """
            SELECT

                h.id,
                h.title,
                h.due_date

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            WHERE

                hm.enrollment_id = :enrollment_id

            AND DATE(h.due_date) = :tomorrow

            ORDER BY h.due_date ASC
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id,
                "tomorrow": tomorrow
            }
        )

        return [
            dict(row)
            for row in result.mappings()
        ]

    async def get_recent_feedback(
        self,
        enrollment_id: int
    ):

        query = text(
            """
            SELECT

                h.title,

                hs.teacher_note,

                hs.marks_obtained,

                hs.reviewed_at

            FROM students_homeworksubmission hs

            INNER JOIN
                students_homework h
            ON
                h.id = hs.homework_id

            WHERE

                hs.enrollment_id = :enrollment_id

            AND hs.teacher_note IS NOT NULL

            ORDER BY hs.reviewed_at DESC

            LIMIT 5
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )
        print(
            f"get_recent_feedback: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        return [
            dict(row)
            for row in result.mappings()
        ]