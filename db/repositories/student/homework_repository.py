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

# ------------------------------------------------------
# Shared SQL fragments. Every list/detail query now joins
# ONLY the latest submission attempt for this enrollment
# (so resubmitted homework can never show stale data from
# an older attempt) and pulls the subject + teacher names
# through the homework -> offering -> subject chain.
# ------------------------------------------------------

LATEST_ATTEMPT_JOIN = """
    LEFT JOIN students_homeworksubmission hs
        ON hs.homework_id = h.id
        AND hs.enrollment_id = :enrollment_id
        AND hs.attempt_number = (
            SELECT MAX(hs2.attempt_number)
            FROM students_homeworksubmission hs2
            WHERE hs2.homework_id = h.id
            AND hs2.enrollment_id = :enrollment_id
        )
"""

SUBJECT_TEACHER_JOIN = """
    LEFT JOIN schools_subjectoffering so
        ON so.id = h.subject_offering_id
    LEFT JOIN schools_subjectversion sv
        ON sv.id = so.subject_version_id
    LEFT JOIN schools_subject sub
        ON sub.id = sv.subject_id
    LEFT JOIN staff_staff t
        ON t.id = so.teacher_id
"""

SUBJECT_TEACHER_COLUMNS = """
    sub.name AS subject_name,
    TRIM(BOTH FROM COALESCE(t.first_name, '') || ' ' || COALESCE(t.last_name, '')) AS teacher_name,
"""

NOT_SUBMITTED_CONDITION = (
    "(hs.status IS NULL OR hs.status NOT IN (1, 2))"
)

NOT_SUBMITTED_EXCLUDING_RESUBMIT = (
    "(hs.status IS NULL OR hs.status NOT IN (1, 2, 3))"
)


def filter_homework_rows(rows, teacher=None, subject=None):
    if teacher:
        rows = [
            r for r in rows
            if (r.get("teacher_name") or "").strip().lower()
            == teacher.lower()
        ]
    if subject:
        rows = [
            r for r in rows
            if (r.get("subject_name") or "").strip().lower()
            == subject.lower()
        ]
    return rows


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

    async def list_enrollment_homework_titles(self, enrollment_id: int):
        result = await self.db.execute(
            text("""
                SELECT DISTINCT h.id, h.title
                FROM students_homeworkstudentmap hm
                JOIN students_homework h ON h.id = hm.homework_id
                WHERE hm.enrollment_id = :enrollment_id
                ORDER BY h.title
            """),
            {"enrollment_id": enrollment_id}
        )
        return [dict(row) for row in result.mappings()]


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
        # 2. Single query: candidate homework rows joined to
        #    the LATEST submission attempt and assignment map.
        #    Exact titles outrank fuzzy ILIKE matches; graded
        #    rows outrank ungraded ones. Subject and teacher
        #    ride along for detail answers.
        # --------------------------------------------------

        is_relative = normalized in RELATIVE_HOMEWORK_TITLES

        result = await self.db.execute(
            text(
                f"""
                SELECT
                    h.id,
                    h.title,
                    h.total_marks,
                    h.due_date,
                    hs.status AS latest_status,
                    hs.marks_obtained,
                    hs.submitted_at,
                    hs.reviewed_at,
                    hs.teacher_note,
                    hs.attempt_number,
                    {SUBJECT_TEACHER_COLUMNS}
                    CASE
                        WHEN hm.enrollment_id IS NOT NULL THEN TRUE
                        ELSE FALSE
                    END AS is_assigned
                FROM students_homework h
                {LATEST_ATTEMPT_JOIN}
                LEFT JOIN students_homeworkstudentmap hm
                    ON hm.homework_id = h.id
                    AND hm.enrollment_id = :enrollment_id
                {SUBJECT_TEACHER_JOIN}
                WHERE
                    (
                        NOT :is_relative
                        OR hm.enrollment_id IS NOT NULL
                    )
                AND
                    (:is_relative OR h.title = :title)
                ORDER BY
                    (hm.enrollment_id IS NOT NULL) DESC,
                    ((hs.status = 2) IS TRUE) DESC,
                    hs.reviewed_at DESC NULLS LAST,
                    h.id ASC
                """
            ),
            {
                "is_relative": is_relative,
                "title": title,
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
        # 2. Decide the state from the LATEST attempt only:
        #    graded -> real marks, submitted -> awaiting
        #    review, resubmit -> teacher asked for a redo,
        #    otherwise assigned / not-assigned.
        # --------------------------------------------------

        def build_marks(row):

            percentage = round(
                (
                    row["marks_obtained"]
                    / row["total_marks"]
                ) * 100,
                2
            ) if row["total_marks"] else 0

            return {
                "state": "marks",
                "id": row["id"],
                "title": row["title"],
                "total_marks": row["total_marks"],
                "due_date": row["due_date"],
                "subject_name": row["subject_name"],
                "teacher_name": row["teacher_name"],
                "marks_obtained": row["marks_obtained"],
                "percentage": percentage,
                "submitted_at": row["submitted_at"],
                "reviewed_at": row["reviewed_at"],
                "teacher_note": row["teacher_note"],
                "attempt_number": row["attempt_number"],
            }

        if is_relative:

            for row in rows:

                if (
                    row["latest_status"] == 2
                    and
                    row["marks_obtained"] is not None
                ):

                    return build_marks(row)

            return {
                "state": "not_found",
                "title": title,
            }

        row = rows[0]

        #
        # Duplicate titles: the same normalized title can
        # exist as several real homework rows. Carry every
        # match so the reply can count them instead of
        # silently showing only one.
        #

        matches_meta = None

        if len(rows) > 1:

            matches_meta = [
                {
                    "id": duplicate_row["id"],
                    "due_date": (
                        str(duplicate_row["due_date"])[:10]
                        if duplicate_row.get("due_date")
                        else None
                    ),
                    "submitted": bool(duplicate_row.get("latest_status")),
                    "graded": duplicate_row.get("latest_status") == 2,
                }
                for duplicate_row in rows
            ]

        latest_status = row["latest_status"]

        if (
            latest_status == 2
            and
            row["marks_obtained"] is not None
        ):

            marks_state = build_marks(row)

            if matches_meta:

                marks_state["matches"] = matches_meta

            return marks_state

        if latest_status == 1:

            return {
                "state": "submitted_not_graded",
                "id": row["id"],
                "title": row["title"],
                "due_date": row["due_date"],
                "subject_name": row["subject_name"],
                "teacher_name": row["teacher_name"],
                "teacher_note": row["teacher_note"],
                "matches": matches_meta,
            }

        if latest_status == 3:

            return {
                "state": "resubmit_requested",
                "id": row["id"],
                "title": row["title"],
                "due_date": row["due_date"],
                "subject_name": row["subject_name"],
                "teacher_name": row["teacher_name"],
                "teacher_note": row["teacher_note"],
                "matches": matches_meta,
            }

        if row["is_assigned"]:

            due_date = row["due_date"]

            is_past_due = bool(
                due_date
                and
                due_date.date() < ist_today()
            )

            return {
                "state": "assigned_not_submitted",
                "id": row["id"],
                "title": row["title"],
                "due_date": due_date,
                "is_past_due": is_past_due,
                "subject_name": row["subject_name"],
                "teacher_name": row["teacher_name"],
                "teacher_note": row["teacher_note"],
                "matches": matches_meta,
            }

        return {
            "state": "not_assigned",
            "id": row["id"],
            "title": row["title"],
            "matches": matches_meta,
        }

    async def get_pending_homework(
        self,
        enrollment_id: int,
        subject=None,
        start=None,
        end=None,
        include_submitted=False,
        teacher=None
    ):

        # Default: every homework not submitted yet (overdue flagged via is_overdue).
        # start/end bound to a due-date window (this week / yesterday / a single day / any range).
        # include_submitted widens to ALL homework with submitted_at, marks_obtained and a
        # status_tag (pending / overdue / submitted / graded / resubmit_requested) for slicing.

        params = {
            "enrollment_id": enrollment_id
        }

        window_filter = ""

        if start and end:

            window_filter = (
                "AND DATE(h.due_date)"
                " BETWEEN :window_start AND :window_end"
            )

            params["window_start"] = start
            params["window_end"] = end

        elif start:

            window_filter = (
                "AND DATE(h.due_date) >= :window_start"
            )

            params["window_start"] = start

        elif end:

            window_filter = (
                "AND DATE(h.due_date) <= :window_end"
            )

            params["window_end"] = end

        status_condition = (
            NOT_SUBMITTED_CONDITION
            if not include_submitted
            else "TRUE"
        )

        query = text(
            f"""
            SELECT

                h.id,

                h.title,

                h.due_date,

                h.total_marks,

                CASE WHEN h.due_date < date_trunc('day', NOW())
                     THEN TRUE ELSE FALSE
                END AS is_overdue,

                {SUBJECT_TEACHER_COLUMNS}

                hs.status AS latest_status,

                hs.marks_obtained,

                hs.submitted_at,

                CASE
                    WHEN hs.status = 2 THEN 'graded'
                    WHEN hs.status = 1 THEN 'submitted'
                    WHEN hs.status = 3 THEN 'resubmit_requested'
                    WHEN h.due_date < date_trunc('day', NOW())
                        THEN 'overdue'
                    ELSE 'pending'
                END AS status_tag

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            {LATEST_ATTEMPT_JOIN}

            {SUBJECT_TEACHER_JOIN}

            WHERE

                hm.enrollment_id = :enrollment_id

            AND {status_condition}

            {window_filter}

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            params

        )
        print(
            f"get_pending_homework: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        rows = [
            dict(row)
            for row in result.mappings()
        ]
        return filter_homework_rows(
            rows,
            teacher,
            subject,
        )

    async def get_overdue_homework(
        self,
        enrollment_id: int,
        subject=None,
        teacher=None,
        start=None,
        end=None
    ):

        # Overdue = not submitted AND past due date.
        # Always a subset of the pending list.

        params = {
            "enrollment_id": enrollment_id
        }

        window_filter = ""

        if start and end:

            window_filter = (
                "AND DATE(h.due_date)"
                " BETWEEN :window_start AND :window_end"
            )

            params["window_start"] = start

            params["window_end"] = end

        elif start:

            window_filter = (
                "AND DATE(h.due_date) >= :window_start"
            )

            params["window_start"] = start

        elif end:

            window_filter = (
                "AND DATE(h.due_date) <= :window_end"
            )

            params["window_end"] = end

        query = text(
            f"""
            SELECT

                h.id,

                h.title,

                h.due_date,

                h.total_marks,

                TRUE AS is_overdue,

                {SUBJECT_TEACHER_COLUMNS}

                hs.status AS latest_status,

                'overdue' AS status_tag

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            {LATEST_ATTEMPT_JOIN}

            {SUBJECT_TEACHER_JOIN}

            WHERE

                hm.enrollment_id = :enrollment_id

            AND  {NOT_SUBMITTED_EXCLUDING_RESUBMIT}

            AND h.due_date < date_trunc('day', NOW())

            {window_filter}

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            params
        )
        print(
            f"get_overdue_homework: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        rows = [
            dict(row)
            for row in result.mappings()
        ]
        return filter_homework_rows(
            rows,
            teacher,
            subject,
        )

    async def get_due_today(
        self,
        enrollment_id: int,
        subject=None,
        teacher=None
    ):

        today = ist_today()

        params = {
            "enrollment_id": enrollment_id,
            "today": today
        }

        query = text(
            f"""
            SELECT

                h.id,

                h.title,

                h.due_date,

            {SUBJECT_TEACHER_COLUMNS}

                hs.status AS latest_status

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            {LATEST_ATTEMPT_JOIN}

            {SUBJECT_TEACHER_JOIN}

            WHERE

                hm.enrollment_id = :enrollment_id

            AND  {NOT_SUBMITTED_EXCLUDING_RESUBMIT}

            AND DATE(h.due_date) = :today

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            params
        )
        print(
            f"get_due_today: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        rows = [
            dict(row)
            for row in result.mappings()
        ]
        return filter_homework_rows(
            rows,
            teacher,
            subject,
        )

    async def get_due_tomorrow(
        self,
        enrollment_id: int,
        subject=None,
        teacher=None
    ):

        tomorrow = (
            ist_today()
            + timedelta(days=1)
        )

        params = {
            "enrollment_id": enrollment_id,
            "tomorrow": tomorrow
        }

        query = text(
            f"""
            SELECT

                h.id,

                h.title,

                h.due_date,

            {SUBJECT_TEACHER_COLUMNS}

                hs.status AS latest_status

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id

            {LATEST_ATTEMPT_JOIN}

            {SUBJECT_TEACHER_JOIN}

            WHERE

                hm.enrollment_id = :enrollment_id

            AND  {NOT_SUBMITTED_EXCLUDING_RESUBMIT}

            AND DATE(h.due_date) = :tomorrow

            ORDER BY h.due_date ASC
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            params
        )

        rows = [
            dict(row)
            for row in result.mappings()
        ]
        return filter_homework_rows(
            rows,
            teacher,
            subject,
        )

    async def get_recent_feedback(
        self,
        enrollment_id: int,
        subject=None
    ):

        # Latest 5 teacher notes per homework, anchored to the latest attempt (old notes must not resurface).

        params = {
            "enrollment_id": enrollment_id
        }

        query = text(
            f"""
            SELECT

                h.id,

                h.title,

                h.due_date,

            {SUBJECT_TEACHER_COLUMNS}

                hs.teacher_note,

                hs.marks_obtained,

                hs.reviewed_at

            FROM students_homework h

            INNER JOIN
                students_homeworkstudentmap hm
            ON
                hm.homework_id = h.id
            AND
                hm.enrollment_id = :enrollment_id

            {LATEST_ATTEMPT_JOIN}

            {SUBJECT_TEACHER_JOIN}

            WHERE

                hm.enrollment_id = :enrollment_id

            AND hs.teacher_note IS NOT NULL

            ORDER BY hs.reviewed_at DESC NULLS LAST

            LIMIT 5
            """
        )
        start = time.perf_counter()
        result = await self.db.execute(
            query,
            params
        )
        print(
            f"get_recent_feedback: {(time.perf_counter()-start)*1000:.2f} ms"
        )
        rows = [
            dict(row)
            for row in result.mappings()
        ]
        return filter_homework_rows(
            rows,
            subject=subject,
        )