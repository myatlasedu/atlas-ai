from sqlalchemy import text


class SubjectRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_subject_performance(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT
                subject_name,
                score,
                final_grade,
                attendance_percentage,
                homework_percentage,
                overall_comment
            FROM students_reportcardsubjectsnapshot
            WHERE enrollment_id = :enrollment_id
            ORDER BY score DESC
            """
        )

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

    async def get_strongest_subject(
        self,
        enrollment_id
    ):

        subjects = await self.get_subject_performance(
            enrollment_id
        )

        return (
            subjects[0]
            if subjects
            else None
        )

    async def get_weakest_subject(
        self,
        enrollment_id
    ):

        subjects = await self.get_subject_performance(
            enrollment_id
        )

        return (
            subjects[-1]
            if subjects
            else None
        )