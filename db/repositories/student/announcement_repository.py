from sqlalchemy import text


class AnnouncementRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_recent_announcements(
        self,
        academic_class_id: int,
        limit: int = 5
    ):

        query = text(
            """
            SELECT
                a.id,
                a.title,
                a.message,
                a.created_at
            FROM students_announcement a
            INNER JOIN students_announcementclassmap acm
                ON acm.announcement_id = a.id
            WHERE
                acm.academic_class_id = :academic_class_id
                AND a.is_active = TRUE
            ORDER BY a.created_at DESC
            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            {
                "academic_class_id":
                    academic_class_id,
                "limit":
                    limit
            }
        )

        rows = result.mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    async def get_latest_announcement(
        self,
        academic_class_id: int
    ):

        announcements = (
            await self.get_recent_announcements(
                academic_class_id=academic_class_id,
                limit=1
            )
        )

        if announcements:
            return announcements[0]

        return None