from sqlalchemy import text


class ResourceRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_resources(
        self,
        enrollment_id: int,
        subject: str | None = None,
        topic: str | None = None,
    ):

        base = """
            FROM staff_learningresource lr
            INNER JOIN schools_topicoffering toff
                ON toff.id = lr.topic_offering_id
            INNER JOIN schools_subjectversiontopic svt
                ON svt.id = toff.subject_version_topic_id
            INNER JOIN schools_topic t
                ON t.id = svt.topic_id
            INNER JOIN schools_subjectversion sv
                ON sv.id = svt.subject_version_id
            INNER JOIN schools_subject s
                ON s.id = sv.subject_id
            INNER JOIN students_learningresourceaccess la
                ON la.resource_id = lr.id
            WHERE
                la.enrollment_id = :enrollment_id
            AND lr.is_published = TRUE
        """

        where = ""

        params = {
            "enrollment_id": enrollment_id,
        }

        if subject:

            where += (
                "\nAND LOWER(s.name) = LOWER(:subject)\n"
            )

            params["subject"] = subject

        if topic:

            where += (
                "\nAND LOWER(t.name) = LOWER(:topic)\n"
            )

            params["topic"] = topic

        query = text(
            f"""
            SELECT
                lr.id,
                lr.name,
                lr.media_type,
                lr.file,
                lr.external_url,
                lr.note,
                s.name AS subject_name,
                t.name AS topic_name
            {base}
            {where}
            """
        )

        result = await self.db.execute(
            query,
            params,
        )

        return [
            dict(row)
            for row in result.mappings()
        ]
