from sqlalchemy import text


class TopicRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    def _get_where_subject(
        self,
        alias: str,
        subject_offering_id,
    ):

        if subject_offering_id is None:
            return ""

        return f"""

            AND {alias}.subject_offering_id = :subject_offering_id

        """
    
    async def _get_completed_topics(
        self,
        enrollment_id,
        subject_offering_id=None,
    ):
        
        
        where_subject = ""

        if subject_offering_id is not None:

            where_subject = """

                AND sv.subject_id = (

                    SELECT sv2.subject_id

                    FROM schools_subjectoffering so

                    INNER JOIN schools_subjectversion sv2

                        ON sv2.id = so.subject_version_id

                    WHERE so.id = :subject_offering_id

                )

            """

        query = text(
        f"""
        SELECT

            t.id AS topic_id,

            t.name AS topic_name,

            s.id AS subject_id,

            s.name AS subject_name,

            COUNT(DISTINCT ps.id) AS times_taught,

            MAX(ps.date) AS last_taught

        FROM students_studentenrollment se

        INNER JOIN schools_timetableslot ts

            ON ts.academic_class_id = se.academic_class_id

        INNER JOIN schools_periodsession ps

            ON ps.timetable_slot_id = ts.id

        INNER JOIN schools_periodtopiclog ptl

            ON ptl.period_session_id = ps.id

        INNER JOIN schools_periodtopiclog_topics ptlt

            ON ptlt.period_topic_log_id = ptl.id

        INNER JOIN schools_topicoffering tp

            ON tp.id = ptlt.topic_offering_id

        INNER JOIN schools_subjectversiontopic svt

            ON svt.id = tp.subject_version_topic_id

        INNER JOIN schools_subjectversion sv

            ON sv.id = svt.subject_version_id

        INNER JOIN schools_subject s

            ON s.id = sv.subject_id

        INNER JOIN schools_topic t

            ON t.id = svt.topic_id

        WHERE

            se.id = :enrollment_id

            AND tp.academic_class_id = se.academic_class_id

            {where_subject}

        GROUP BY

            t.id,
            t.name,
            s.id,
            s.name

        ORDER BY

            s.name,
            t.name
        """
    )

        result = await self.db.execute(

            query,

            {

                "enrollment_id": enrollment_id,

                "subject_offering_id": subject_offering_id,
            }
        )

        return [
            dict(row)
            for row
            in result.mappings().all()
        ]
    
    async def _get_assessment_topic_scores(
        self,
        enrollment_id,
        subject_offering_id=None,
    ):
        
        where_subject = self._get_where_subject(
            "a",
            subject_offering_id,
        )

        query = text(
            f"""
            SELECT

                t.id AS topic_id,
                t.name AS topic_name,

                s.id AS subject_id,
                s.name AS subject_name,

                AVG(
                    (
                        asr.marks_obtained::numeric
                        /
                        NULLIF(a.total_marks,0)
                    ) * 100
                ) AS assessment_average,

                COUNT(*) AS assessment_attempts

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

                {where_subject}

                AND asr.status = 3

                AND asr.marks_obtained IS NOT NULL

                AND a.total_marks > 0

            GROUP BY

                t.id,
                t.name,
                s.id,
                s.name

            ORDER BY

                s.name,
                t.name
            """
        )

        result = await self.db.execute(

            query,

            {
                "enrollment_id": enrollment_id,
                "subject_offering_id": subject_offering_id,
            }
        )

        return [
            dict(row)
            for row
            in result.mappings().all()
        ]
    
    async def _get_homework_topic_scores(
        self,
        enrollment_id,
        subject_offering_id=None,
    ):
        where_subject = self._get_where_subject(
            "h",
            subject_offering_id,
        )

        query = text(
            f"""
            SELECT

                t.id AS topic_id,
                t.name AS topic_name,

                s.id AS subject_id,
                s.name AS subject_name,

                AVG(
                    (
                        hs.marks_obtained::numeric
                        /
                        NULLIF(h.total_marks,0)
                    ) * 100
                ) AS homework_average,

                COUNT(*) AS homework_attempts

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

                {where_subject}

                AND hs.reviewed_at IS NOT NULL

                AND hs.marks_obtained IS NOT NULL

                AND h.total_marks > 0

            GROUP BY

                t.id,
                t.name,
                s.id,
                s.name

            ORDER BY

                s.name,
                t.name
            """
        )

        result = await self.db.execute(

            query,

            {
                "enrollment_id": enrollment_id,
                "subject_offering_id": subject_offering_id,
            }
        )

        return [
            dict(row)
            for row
            in result.mappings().all()
        ]
    
    async def _resolve_subject_offering(
        self,
        enrollment_id: int,
        subject_name: str | None = None,
    ):

        if not subject_name:

            return None

        query = text(
            """
            SELECT

                so.id

            FROM students_studentenrollment se

            INNER JOIN schools_subjectoffering so

                ON so.academic_class_id = se.academic_class_id

            INNER JOIN schools_subjectversion sv

                ON sv.id = so.subject_version_id

            INNER JOIN schools_subject s

                ON s.id = sv.subject_id

            WHERE

                se.id = :enrollment_id

                AND so.is_active = TRUE

                AND LOWER(s.name) = LOWER(:subject_name)

            LIMIT 1
            """
        )

        result = await self.db.execute(

            query,

            {

                "enrollment_id": enrollment_id,

                "subject_name": subject_name,
            }
        )

        return result.scalar_one_or_none()
    
    async def get_topic_statistics(
        self,
        enrollment_id,
        subject_name=None,
    ):
        
        subject_offering_id = await self._resolve_subject_offering(
            enrollment_id,
            subject_name,
        )

        completed_topics = await self._get_completed_topics(
            enrollment_id,
            subject_offering_id,
        )

        assessment_topics = await self._get_assessment_topic_scores(
            enrollment_id,
            subject_offering_id,
        )

        homework_topics = await self._get_homework_topic_scores(
            enrollment_id,
            subject_offering_id,
        )

        topics = {}

        # ==========================================
        # COMPLETED TOPICS
        # ==========================================

        for topic in completed_topics:

            topics[
                topic["topic_id"]
            ] = {

                "topic_id":
                    topic["topic_id"],

                "topic_name":
                    topic["topic_name"],

                "subject_id":
                    topic["subject_id"],

                "subject_name":
                    topic["subject_name"],

                "completed":
                    True,

                "assessment_average":
                    None,

                "assessment_attempts":
                    0,

                "homework_average":
                    None,

                "homework_attempts":
                    0,
            }

        # ==========================================
        # ASSESSMENT DATA
        # ==========================================

        for topic in assessment_topics:

            item = topics.setdefault(

                topic["topic_id"],

                {

                    "topic_id":
                        topic["topic_id"],

                    "topic_name":
                        topic["topic_name"],

                    "subject_id":
                        topic["subject_id"],

                    "subject_name":
                        topic["subject_name"],

                    "completed":
                        False,

                    "assessment_average":
                        None,

                    "assessment_attempts":
                        0,

                    "homework_average":
                        None,

                    "homework_attempts":
                        0,
                }
            )

            item["assessment_average"] = float(
                topic["assessment_average"]
            )

            item["assessment_attempts"] = int(
                topic["assessment_attempts"]
            )

        # ==========================================
        # HOMEWORK DATA
        # ==========================================

        for topic in homework_topics:

            item = topics.setdefault(

                topic["topic_id"],

                {

                    "topic_id":
                        topic["topic_id"],

                    "topic_name":
                        topic["topic_name"],

                    "subject_id":
                        topic["subject_id"],

                    "subject_name":
                        topic["subject_name"],

                    "completed":
                        False,

                    "assessment_average":
                        None,

                    "assessment_attempts":
                        0,

                    "homework_average":
                        None,

                    "homework_attempts":
                        0,
                }
            )

            item["homework_average"] = float(
                topic["homework_average"]
            )

            item["homework_attempts"] = int(
                topic["homework_attempts"]
            )

        # ==========================================
        # FINAL SCORE
        # ==========================================

        completed = []
        pending = []
        weak = []

        for topic in topics.values():

            scores = []

            if topic["assessment_average"] is not None:
                scores.append(topic["assessment_average"])

            if topic["homework_average"] is not None:
                scores.append(topic["homework_average"])

            topic["average_score"] = (
                round(sum(scores) / len(scores), 1)
                if scores
                else None
            )

            if topic["completed"]:
                completed.append(topic)
            else:
                pending.append(topic)

            if (
                topic["average_score"] is not None
                and topic["average_score"] < 60
            ):
                weak.append(topic)

        completed.sort(
            key=lambda x: (
                x["subject_name"],
                x["topic_name"],
            )
        )

        pending.sort(
            key=lambda x: (
                x["subject_name"],
                x["topic_name"],
            )
        )

        weak.sort(
            key=lambda x: (
                x["subject_name"],
                x["topic_name"],
            )
        )

        return {

            "completed_topics":
                completed,

            "pending_topics":
                pending,

            "weak_topics":
                weak,

            "all_topics":
                completed + pending,
        }
        