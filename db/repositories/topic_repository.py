from sqlalchemy import text


class TopicRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_assessment_topics(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT DISTINCT

                t.id AS topic_id,
                t.name AS topic_name,
                s.name AS subject_name

            FROM students_assessmentstudentrecord asr

            INNER JOIN students_assessment a
                ON a.id = asr.assessment_id

            INNER JOIN students_assessmenttopicmap atm
                ON atm.assessment_id = a.id

            INNER JOIN schools_topicoffering tp
                ON tp.id = atm.topic_offering_id

            INNER JOIN schools_subjectversiontopic svt
                ON svt.id = tp.subject_version_topic_id

            INNER JOIN schools_topic t
                ON t.id = svt.topic_id

            INNER JOIN schools_subject s
                ON s.id = t.subject_id

            WHERE
                asr.enrollment_id = :enrollment_id

            ORDER BY
                s.name,
                t.name
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id": enrollment_id
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    async def get_weak_topics(
        self,
        enrollment_id
    ):

        assessment_query = text(
            """
            SELECT DISTINCT

                t.id AS topic_id,
                t.name AS topic_name,
                s.name AS subject_name,
                'assessment' AS source

            FROM students_assessmentstudentrecord asr

            INNER JOIN students_assessment a
                ON a.id = asr.assessment_id

            INNER JOIN students_assessmenttopicmap atm
                ON atm.assessment_id = a.id

            INNER JOIN schools_topicoffering tp
                ON tp.id = atm.topic_offering_id

            INNER JOIN schools_subjectversiontopic svt
                ON svt.id = tp.subject_version_topic_id

            INNER JOIN schools_topic t
                ON t.id = svt.topic_id

            INNER JOIN schools_subject s
                ON s.id = t.subject_id

            WHERE

                asr.enrollment_id = :enrollment_id

                AND asr.status = 3

                AND asr.marks_obtained IS NOT NULL

                AND a.assessment_date >= (
                    CURRENT_DATE - INTERVAL '30 days'
                )

                AND a.total_marks > 0

                AND (
                    (
                        asr.marks_obtained::numeric
                        /
                        a.total_marks
                    ) * 100
                ) < 60
            """
        )

        homework_query = text(
            """
            SELECT DISTINCT

                t.id AS topic_id,
                t.name AS topic_name,
                s.name AS subject_name,
                'homework' AS source

            FROM students_homeworksubmission hs

            INNER JOIN students_homework h
                ON h.id = hs.homework_id

            INNER JOIN students_homeworktopicmap htm
                ON htm.homework_id = h.id

            INNER JOIN schools_topicoffering tp
                ON tp.id = htm.topic_offering_id

            INNER JOIN schools_subjectversiontopic svt
                ON svt.id = tp.subject_version_topic_id

            INNER JOIN schools_topic t
                ON t.id = svt.topic_id

            INNER JOIN schools_subject s
                ON s.id = t.subject_id

            WHERE

                hs.enrollment_id = :enrollment_id

                AND hs.marks_obtained IS NOT NULL

                AND hs.reviewed_at IS NOT NULL

                AND hs.reviewed_at >= (
                    NOW() - INTERVAL '30 days'
                )

                AND h.total_marks > 0

                AND (
                    (
                        hs.marks_obtained::numeric
                        /
                        h.total_marks
                    ) * 100
                ) < 60
            """
        )

        assessment_result = await self.db.execute(
            assessment_query,
            {
                "enrollment_id": enrollment_id
            }
        )

        homework_result = await self.db.execute(
            homework_query,
            {
                "enrollment_id": enrollment_id
            }
        )

        weak_topics = {}

        for row in assessment_result.mappings().all():

            weak_topics[
                row["topic_id"]
            ] = dict(row)

        for row in homework_result.mappings().all():

            if row["topic_id"] not in weak_topics:

                weak_topics[
                    row["topic_id"]
                ] = dict(row)

        return sorted(
            weak_topics.values(),
            key=lambda x: (
                x["subject_name"],
                x["topic_name"]
            )
        )