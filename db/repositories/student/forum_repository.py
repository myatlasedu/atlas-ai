from sqlalchemy import text


CATEGORY_MAP = {
    1: "Academic",
    2: "Sports",
    3: "Arts",
    4: "Tech",
    5: "Social",
    6: "Wellbeing",
    7: "Language"
}


class ForumRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_my_forums(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT
                f.id,
                f.title,
                f.description,
                f.category,
                f.location,
                f.meeting_time,
                f.created_at
            FROM students_forummember fm
            INNER JOIN students_forum f
                ON f.id = fm.forum_id
            WHERE
                fm.enrollment_id = :enrollment_id
                AND f.status = 2
            ORDER BY f.created_at DESC
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        forums = [
            dict(row)
            for row in result.mappings().all()
        ]

        for forum in forums:

            forum["category"] = (
                CATEGORY_MAP.get(
                    forum["category"],
                    "Unknown"
                )
            )

        return forums

    async def get_latest_forum_announcement(
        self,
        enrollment_id
    ):

        query = text(
            """
            SELECT
                fa.id,
                f.title AS forum_title,
                fa.message,
                fa.created_at
            FROM students_forumannouncement fa
            INNER JOIN students_forum f
                ON f.id = fa.forum_id
            INNER JOIN students_forummember fm
                ON fm.forum_id = f.id
            WHERE
                fm.enrollment_id = :enrollment_id
                AND f.status = 2
            ORDER BY fa.created_at DESC
            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id
            }
        )

        row = result.mappings().first()

        if not row:
            return None

        return dict(row)

    async def get_recent_forum_announcements(
        self,
        enrollment_id,
        limit=5
    ):

        query = text(
            """
            SELECT
                fa.id,
                f.title AS forum_title,
                fa.message,
                fa.created_at
            FROM students_forumannouncement fa
            INNER JOIN students_forum f
                ON f.id = fa.forum_id
            INNER JOIN students_forummember fm
                ON fm.forum_id = f.id
            WHERE
                fm.enrollment_id = :enrollment_id
                AND f.status = 2
            ORDER BY fa.created_at DESC
            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            {
                "enrollment_id":
                    enrollment_id,
                "limit":
                    limit
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]