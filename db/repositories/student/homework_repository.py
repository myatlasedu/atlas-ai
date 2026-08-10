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

    def _normalize_title(
        self,
        value: str,
    ) -> str:

        import re

        return re.sub(
            r"[^a-z0-9]",
            "",
            value.lower(),
        )

    async def get_homework_mark_state(
        self,
        enrollment_id: int,
        title: str
    ):

        # --------------------------------------------------
        # 1. Find all homework by fuzzy normalized-title match
        #    GLOBALLY (no enrollment filter), most recent first.
        # --------------------------------------------------

        normalized = self._normalize_title(title)

        if not normalized:

            return {
                "state": "not_found",
                "title": title,
            }

        query = text(
            """
            SELECT
                h.id,
                h.title,
                h.total_marks,
                h.due_date
            FROM students_homework h
            WHERE
                REGEXP_REPLACE(
                    LOWER(h.title),
                    '[^a-z0-9]',
                    '',
                    'g'
                )
                LIKE
                '%' || REGEXP_REPLACE(
                    LOWER(:title),
                    '[^a-z0-9]',
                    '',
                    'g'
                ) || '%'
            ORDER BY h.due_date DESC NULLS LAST
            """
        )

        result = await self.db.execute(
            query,
            {
                "title": normalized
            }
        )
        matching = [
            dict(row)
            for row in result.mappings()
        ]

        if not matching:
            return {
                "state": "not_found",
                "title": title,
            }

        matching_ids = [
            hw["id"]
            for hw in matching
        ]

        # --------------------------------------------------
        # 2. Across ALL matching homeworks, find this student's
        #    latest graded mark; otherwise, whether any was
        #    assigned but not submitted. Single query.
        # --------------------------------------------------

        # --------------------------------------------------
        # PREVIOUS TWO-QUERY VERSION (commented out)
        # --------------------------------------------------

        # result = await self.db.execute(
        #     text(
        #         """
        #         SELECT
        #             h.id,
        #             h.title,
        #             h.total_marks,
        #             hs.marks_obtained,
        #             hs.reviewed_at,
        #             hs.attempt_number,
        #             hs.status
        #         FROM students_homework h
        #         INNER JOIN
        #             students_homeworksubmission hs
        #         ON
        #             hs.homework_id = h.id
        #         WHERE
        #             h.id = ANY(:homework_ids)
        #         AND
        #             hs.enrollment_id = :enrollment_id
        #         AND
        #             hs.marks_obtained IS NOT NULL
        #         ORDER BY hs.reviewed_at DESC NULLS LAST
        #         LIMIT 1
        #         """
        #     ),
        #     {
        #         "homework_ids": matching_ids,
        #         "enrollment_id": enrollment_id,
        #     }
        # )
        # row = result.mappings().first()

        # if row:

        #     row = dict(row)

        #     if row.get("total_marks"):
        #         row["percentage"] = round(
        #             (
        #                 row["marks_obtained"]
        #                 / row["total_marks"]
        #             ) * 100,
        #             2
        #         )
        #     else:
        #         row["percentage"] = 0

        #     row["state"] = "marks"

        #     return row

        # result = await self.db.execute(
        #     text(
        #         """
        #         SELECT h.id, h.title, h.total_marks
        #         FROM students_homework h
        #         INNER JOIN
        #             students_homeworkstudentmap hm
        #         ON
        #             hm.homework_id = h.id
        #         WHERE
        #             h.id = ANY(:homework_ids)
        #         AND
        #             hm.enrollment_id = :enrollment_id
        #         ORDER BY h.due_date DESC NULLS LAST
        #         LIMIT 1
        #         """
        #     ),
        #     {
        #         "homework_ids": matching_ids,
        #         "enrollment_id": enrollment_id,
        #     }
        # )
        # assigned = result.mappings().first()

        # if assigned:

        #     assigned = dict(assigned)

        #     return {
        #         "state": "assigned_not_submitted",
        #         "id": assigned["id"],
        #         "title": assigned["title"],
        #     }

        # return {
        #     "state": "not_assigned",
        #     "id": matching[0]["id"],
        #     "title": matching[0]["title"],
        # }

        result = await self.db.execute(
            text(
                """
                SELECT
                    h.id,
                    h.title,
                    h.total_marks,
                    hs.marks_obtained,
                    hs.reviewed_at,
                    hs.attempt_number,
                    hs.status,
                    CASE
                        WHEN hm.enrollment_id IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS is_assigned
                FROM students_homework h
                LEFT JOIN students_homeworksubmission hs
                    ON hs.homework_id = h.id
                    AND hs.enrollment_id = :enrollment_id
                    AND hs.marks_obtained IS NOT NULL
                LEFT JOIN students_homeworkstudentmap hm
                    ON hm.homework_id = h.id
                    AND hm.enrollment_id = :enrollment_id
                WHERE
                    h.id = ANY(:homework_ids)
                ORDER BY
                    (hs.reviewed_at IS NOT NULL) DESC,
                    hs.reviewed_at DESC NULLS LAST
                LIMIT 1
                """
            ),
            {
                "homework_ids": matching_ids,
                "enrollment_id": enrollment_id,
            }
        )
        row = result.mappings().first()

        if not row:
            return {
                "state": "not_found",
                "title": title,
            }

        row = dict(row)

        if row["marks_obtained"] is not None:

            if row["total_marks"]:
                row["percentage"] = round(
                    (
                        row["marks_obtained"]
                        / row["total_marks"]
                    ) * 100,
                    2
                )
            else:
                row["percentage"] = 0

            row["state"] = "marks"

            return row

        if row["is_assigned"]:

            return {
                "state": "assigned_not_submitted",
                "id": row["id"],
                "title": row["title"],
            }

        return {
            "state": "not_assigned",
            "id": row["id"],
            "title": row["title"],
        }


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