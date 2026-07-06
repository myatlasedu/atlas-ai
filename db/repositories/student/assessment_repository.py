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
                a.total_marks,
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
                a.total_marks,
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
                a.total_marks,
                a.assessment_date,
                a.type,

                r.marks_obtained,
                r.grade,
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

        total_marks = (
            row.get("total_marks")
            or 0
        )

        obtained = (
            row.get("marks_obtained")
            or 0
        )

        percentage = 0

        if total_marks:

            percentage = round(
                (
                    obtained
                    /
                    total_marks
                ) * 100,
                2
            )

        row["percentage"] = percentage

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

                COUNT(*) AS graded_count,

                AVG(
                    CASE
                        WHEN a.total_marks > 0
                        THEN (
                            r.marks_obtained
                            /
                            a.total_marks
                        ) * 100
                    END
                ) AS average_percentage,

                MAX(
                    CASE
                        WHEN a.total_marks > 0
                        THEN (
                            r.marks_obtained
                            /
                            a.total_marks
                        ) * 100
                    END
                ) AS highest_percentage,

                MIN(
                    CASE
                        WHEN a.total_marks > 0
                        THEN (
                            r.marks_obtained
                            /
                            a.total_marks
                        ) * 100
                    END
                ) AS lowest_percentage

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
                "average_percentage": 0,
                "highest_percentage": 0,
                "lowest_percentage": 0
            }

        return {

            "graded_count":
                row["graded_count"] or 0,

            "average_percentage":
                round(
                    row["average_percentage"] or 0,
                    2
                ),

            "highest_percentage":
                round(
                    row["highest_percentage"] or 0,
                    2
                ),

            "lowest_percentage":
                round(
                    row["lowest_percentage"] or 0,
                    2
                )
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
                a.total_marks,
                a.assessment_date,
                a.type,

                r.marks_obtained,
                r.grade,
                r.teacher_comment,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

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

        row["percentage"] = round(
            (
                row["marks_obtained"]
                /
                row["total_marks"]
            ) * 100,
            2
        )

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
                a.total_marks,
                a.assessment_date,
                a.type,

                r.marks_obtained,
                r.grade,
                r.teacher_comment,
                r.graded_at

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

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

        row["percentage"] = round(
            (
                row["marks_obtained"]
                /
                row["total_marks"]
            ) * 100,
            2
        )

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
                r.marks_obtained,
                r.grade,
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

        return [
            dict(row)
            for row in rows
        ]
    



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

                r.marks_obtained,
                a.total_marks,

                ROUND(
                        (
                            r.marks_obtained
                            /
                            a.total_marks
                        ) * 100
                    ) AS percentage

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

            ORDER BY r.graded_at ASC
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

                "average": 0,

                "highest": 0,

                "lowest": 0,

                "range": 0,

                "std_dev": 0,

                "rating": "Insufficient Data"
            }

        scores = [

            row["percentage"]

            for row in trend_data
        ]

        highest = max(scores)

        lowest = min(scores)

        average = round(
            sum(scores)
            /
            len(scores),
            2
        )

        std_dev = 0

        if len(scores) > 1:

            std_dev = round(
                statistics.stdev(scores),
                2
            )

        if std_dev < 5:

            rating = "Excellent"

        elif std_dev < 10:

            rating = "Good"

        elif std_dev < 20:

            rating = "Moderate"

        else:

            rating = "Poor"

        return {

            "count":
                len(scores),

            "average":
                average,

            "highest":
                highest,

            "lowest":
                lowest,

            "range":
                round(
                    highest - lowest,
                    2
                ),

            "std_dev":
                std_dev,

            "rating":
                rating
        }
    
    async def get_risk_assessments(
        self,
        enrollment_id: int
    ):

        query = text("""
            SELECT

                a.id,
                a.title,
                a.assessment_date,
                a.total_marks,
                a.type,

                r.marks_obtained,
                r.grade,
                r.teacher_comment

            FROM students_assessmentstudentrecord r

            INNER JOIN students_assessment a
                ON a.id = r.assessment_id

            WHERE r.enrollment_id = :enrollment_id

            AND r.status = 3

            AND a.total_marks > 0

            ORDER BY a.assessment_date DESC
        """)

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        rows = result.mappings().all()

        risks = []

        for row in rows:

            row = dict(row)

            percentage = round(
                (
                    row["marks_obtained"]
                    /
                    row["total_marks"]
                ) * 100,
                2
            )

            if percentage < 50:

                if percentage < 30:

                    risk_level = "critical"

                elif percentage < 50:

                    risk_level = "high"

                else:

                    risk_level = "medium"

                row["percentage"] = percentage

                row["risk_level"] = risk_level

                risks.append(
                    row
                )

        risks.sort(
            key=lambda x: x["percentage"]
        )

        return risks