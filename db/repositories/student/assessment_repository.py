from sqlalchemy import text
import statistics


class AssessmentRepository:

    def __init__(self, db):

        self.db = db

    # =====================================================
    # UPCOMING ASSESSMENTS
    # =====================================================

    async def get_upcoming_assessments(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.type,

                r.status

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND a.assessment_date >= CURRENT_DATE

            ORDER BY a.assessment_date ASC

            LIMIT 20
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # =====================================================
    # PENDING ASSESSMENTS
    # =====================================================

    async def get_pending_assessments(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.type,

                r.status

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND a.assessment_date >= CURRENT_DATE

            AND r.status IN (1, 2)

            ORDER BY a.assessment_date ASC
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    # =====================================================
    # LATEST RESULT
    # =====================================================

    async def get_latest_result(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.type,

                CASE
                    WHEN r.status = 3 OR r.marks_obtained IS NOT NULL OR (r.grade IS NOT NULL AND r.grade != '') THEN TRUE
                    ELSE FALSE
                END AS is_graded,
                r.status,
                r.teacher_comment,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            ORDER BY r.graded_at DESC

            LIMIT 1
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        row = result.mappings().first()

        if not row:
            return None

        row = dict(row)
        is_graded = bool(row.get("is_graded", False))
        row["is_graded"] = is_graded
        row["isGrade"] = is_graded
        row["isGraded"] = is_graded

        return row

    # =====================================================
    # PERFORMANCE SUMMARY
    # =====================================================

    async def get_performance_summary(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                COUNT(*) AS graded_count

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        row = result.mappings().first()

        if not row:

            return {
                "graded_count": 0,
                "isGrade": False,
                "isGraded": False,
                "is_graded": False,
            }

        graded_count = row["graded_count"] or 0

        return {
            "graded_count": graded_count,
            "isGrade": graded_count > 0,
            "isGraded": graded_count > 0,
            "is_graded": graded_count > 0,
        }

    # =====================================================
    # HIGHEST SCORING ASSESSMENT
    # =====================================================

    async def get_highest_scoring_assessment(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.type,

                TRUE AS is_graded,
                r.status,
                r.teacher_comment,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

            AND r.marks_obtained IS NOT NULL

            ORDER BY
                (
                    r.marks_obtained
                    /
                    a.total_marks
                ) DESC

            LIMIT 1
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        row = result.mappings().first()

        if not row:
            return None

        row = dict(row)
        row["is_graded"] = True
        row["isGrade"] = True
        row["isGraded"] = True

        return row

    # =====================================================
    # LOWEST SCORING ASSESSMENT
    # =====================================================

    async def get_lowest_scoring_assessment(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.type,

                TRUE AS is_graded,
                r.status,
                r.teacher_comment,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

            AND r.marks_obtained IS NOT NULL

            ORDER BY
                (
                    r.marks_obtained
                    /
                    a.total_marks
                ) ASC

            LIMIT 1
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        row = result.mappings().first()

        if not row:
            return None

        row = dict(row)
        row["is_graded"] = True
        row["isGrade"] = True
        row["isGraded"] = True

        return row

    # =====================================================
    # RECENT FEEDBACK
    # =====================================================

    async def get_recent_feedback(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,

                r.teacher_comment,
                CASE
                    WHEN r.status = 3 OR r.marks_obtained IS NOT NULL OR (r.grade IS NOT NULL AND r.grade != '') THEN TRUE
                    ELSE FALSE
                END AS is_graded,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.teacher_comment IS NOT NULL

            AND TRIM(r.teacher_comment) <> ''

            ORDER BY r.graded_at DESC

            LIMIT 5
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        rows = result.mappings().all()

        feedbacks = []
        for r in rows:
            d = dict(r)
            is_graded = bool(d.get("is_graded", False))
            d["is_graded"] = is_graded
            d["isGrade"] = is_graded
            d["isGraded"] = is_graded
            feedbacks.append(d)

        return feedbacks

    # =====================================================
    # ASSESSMENT TREND
    # =====================================================

    async def get_assessment_trend(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                TRUE AS is_graded,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            ORDER BY r.graded_at ASC
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        rows = []
        for r in result.mappings().all():
            d = dict(r)
            d["is_graded"] = True
            d["isGrade"] = True
            d["isGraded"] = True
            rows.append(d)

        return rows

    async def get_consistency_metrics(
        self,
        enrollment_id: int
    ):

        trend_data = await self.get_assessment_trend(
            enrollment_id
        )

        if not trend_data:

            return {

                "count": 0,

                "isGrade": False,
                "isGraded": False,
                "is_graded": False,

                "rating": "Insufficient Data"
            }

        return {

            "count":
                len(trend_data),

            "isGrade": True,
            "isGraded": True,
            "is_graded": True,

            "rating":
                "Good"
        }
    
    async def get_risk_assessments(
        self,
        enrollment_id: int
    ):

        return []

    # =====================================================
    # ALL STUDENT ASSESSMENTS (GRADED & UNGRADED)
    # =====================================================

    async def get_all_student_assessments(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT
                a.id,
                a.title,
                a.assessment_date,
                a.type,
                CASE
                    WHEN r.status = 3 OR r.marks_obtained IS NOT NULL OR (r.grade IS NOT NULL AND r.grade != '') THEN TRUE
                    ELSE FALSE
                END AS is_graded,
                r.status,
                r.teacher_comment,
                r.graded_at
            FROM students_assessmentstudentrecord r
            INNER JOIN students_assessment a
                ON a.id = r.assessment_id
            WHERE r.enrollment_id = :enrollment_id
            ORDER BY a.assessment_date DESC, r.graded_at DESC
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        assessments = []
        for r in result.mappings().all():
            d = dict(r)
            is_graded = bool(d.get("is_graded", False))
            d["is_graded"] = is_graded
            d["isGrade"] = is_graded
            d["isGraded"] = is_graded
            assessments.append(d)

        return assessments