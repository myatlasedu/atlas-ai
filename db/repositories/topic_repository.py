from sqlalchemy import text


class TopicRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_completed_topics(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT
                t.name AS topic_name,
                s.name AS subject_name,
                stc.completed_at
            FROM students_studenttopiccompletion stc
            INNER JOIN schools_topicoffering tp
                ON tp.id = stc.topic_offering_id
            INNER JOIN schools_curriculumtopicmap ctm
                ON ctm.id = tp.curriculum_topic_id
            INNER JOIN schools_topic t
                ON t.id = ctm.topic_id
            INNER JOIN schools_subject s
                ON s.id = t.subject_id
            WHERE
                stc.enrollment_id = :enrollment_id
                AND stc.is_completed = TRUE
            ORDER BY stc.completed_at DESC
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

    async def get_pending_topics(
        self,
        enrollment_id,
        academic_class_id
    ):

        query = text(
            """
            SELECT
                t.name AS topic_name,
                s.name AS subject_name
            FROM schools_topicoffering tp
            INNER JOIN schools_curriculumtopicmap ctm
                ON ctm.id = tp.curriculum_topic_id
            INNER JOIN schools_topic t
                ON t.id = ctm.topic_id
            INNER JOIN schools_subject s
                ON s.id = t.subject_id

            WHERE tp.academic_class_id = :academic_class_id

            AND tp.id NOT IN (

                SELECT
                    topic_offering_id
                FROM students_studenttopiccompletion
                WHERE enrollment_id = :enrollment_id
            )

            ORDER BY
                s.name,
                t.name
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id,
                "academic_class_id":
                    academic_class_id
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    async def get_assessment_topics(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT DISTINCT

                t.name AS topic_name,

                s.name AS subject_name

            FROM students_assessmentstudentrecord asr

            INNER JOIN students_assessment a
                ON a.id = asr.assessment_id

            INNER JOIN students_assessmenttopicmap atm
                ON atm.assessment_id = a.id

            INNER JOIN schools_topicoffering tp
                ON tp.id = atm.topic_offering_id

            INNER JOIN schools_curriculumtopicmap ctm
                ON ctm.id = tp.curriculum_topic_id

            INNER JOIN schools_topic t
                ON t.id = ctm.topic_id

            INNER JOIN schools_subject s
                ON s.id = t.subject_id

            WHERE asr.enrollment_id = :enrollment_id
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