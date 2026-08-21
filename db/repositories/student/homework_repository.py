from datetime import date
from datetime import timedelta

from sqlalchemy import text
import time
from utils import ist_today

RELATIVE_HOMEWORK_TITLES = {
    "latesthomework",
    "lasthomework",
    "recenthomework",
    "pasthomework",
    "previoushomework",
}


class HomeworkRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    def normalize_title(
        self,
        value: str,
    ) -> str:

        return "".join(
            character
            for character
            in value.lower()
            if character.isalnum()
        )

    def build_title_pattern(
        self,
        value: str,
    ) -> str:

        pattern_chars = []

        for character in value.lower():

            if character == "\\":

                pattern_chars.append("\\\\")

            elif character == "%":

                pattern_chars.append("\\%")

            elif character in (
                "_",
                " ",
                "-",
                ".",
                ",",
                "'",
            ):

                pattern_chars.append("%")

            else:

                pattern_chars.append(character)

        return "".join(pattern_chars)

    async def get_homework_mark_state(
        self,
        enrollment_id: int,
        title: str
    ):

        # --------------------------------------------------
        # 1. Guard: a punctuation-only topic normalizes to
        #    nothing. Never match all homework in that case.
        # --------------------------------------------------

        normalized = self.normalize_title(title)

        if not normalized:

            return {
                "state": "not_found",
                "title": title,
            }

        # --------------------------------------------------
        # 2. Single query: candidate homework rows joined
        #    with this enrollment's graded submissions and
        #    assignment map. Exact titles outrank fuzzy ILIKE
        #    matches; graded rows outrank ungraded ones.
        # --------------------------------------------------

        is_relative = normalized in RELATIVE_HOMEWORK_TITLES

        title_pattern = self.build_title_pattern(title)

        result = await self.db.execute(
            text(
                """
                SELECT
                    h.id,
                    h.title,
                    h.total_marks,
                    h.due_date,
                    hs.marks_obtained,
                    hs.reviewed_at,
                    hs.attempt_number,
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
                    (:is_relative OR h.title ILIKE :title_pattern)
                ORDER BY
                    (h.title ILIKE :exact_title) DESC,
                    (hs.reviewed_at IS NOT NULL) DESC,
                    hs.reviewed_at DESC NULLS LAST
                """
            ),
            {
                "is_relative": is_relative,
                "title_pattern": title_pattern,
                "exact_title": title,
                "enrollment_id": enrollment_id,
            }
        )

        rows = [
            dict(row)
            for row in result.mappings()
        ]

        if not rows:

            return {
                "state": "not_found",
                "title": title,
            }

        # --------------------------------------------------
        # 3. Extract the answer from the joined rows.
        # --------------------------------------------------

        mark_row = None

        assigned_row = None

        for row in rows:

            if (
                mark_row is None
                and
                row["marks_obtained"] is not None
            ):

                mark_row = row

            if (
                assigned_row is None
                and
                row["is_assigned"]
            ):

                assigned_row = row

            if (
                mark_row is not None
                and
                assigned_row is not None
            ):

                break

        if mark_row:

            mark_row["percentage"] = round(
                (
                    mark_row["marks_obtained"]
                    / mark_row["total_marks"]
                ) * 100,
                2
            ) if mark_row["total_marks"] else 0

            mark_row["state"] = "marks"

            return mark_row

        if assigned_row and not is_relative:

            return {
                "state": "assigned_not_submitted",
                "id": assigned_row["id"],
                "title": assigned_row["title"],
            }

        if not is_relative:

            return {
                "state": "not_assigned",
                "id": rows[0]["id"],
                "title": rows[0]["title"],
            }

        return {
            "state": "not_found",
            "title": title,
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