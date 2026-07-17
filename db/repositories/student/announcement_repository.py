from sqlalchemy import text


class AnnouncementRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def search_announcements(
        self,
        academic_class_id: int,
        start_date=None,
        end_date=None,
        keyword=None,
        limit: int = 20,
    ):

        where = [

            "acm.academic_class_id = :academic_class_id",

            "a.is_active = TRUE",
        ]

        params = {

            "academic_class_id": academic_class_id,

            "limit": limit,
        }

        if start_date:

            where.append(
                "DATE(a.created_at) >= :start_date"
            )

            params["start_date"] = start_date

        if end_date:

            where.append(
                "DATE(a.created_at) <= :end_date"
            )

            params["end_date"] = end_date

        if keyword:

            where.append(
                """
                (
                    LOWER(a.title) LIKE LOWER(:keyword)
                    OR
                    LOWER(a.message) LIKE LOWER(:keyword)
                )
                """
            )

            params["keyword"] = f"%{keyword}%"

        query = text(
            f"""
            SELECT

                a.id,
                a.title,
                a.message,
                a.created_at

            FROM students_announcement a

            INNER JOIN students_announcementclassmap acm

                ON acm.announcement_id = a.id

            WHERE {" AND ".join(where)}

            ORDER BY

                a.created_at DESC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            params,
        )

        return [

            dict(row)

            for row

            in result.mappings().all()
        ]
    
    async def get_latest_announcement(
        self,
        academic_class_id: int,
    ):

        announcements = await self.search_announcements(

            academic_class_id=academic_class_id,

            limit=1,
        )

        return announcements[0] if announcements else None
    
    async def get_oldest_announcement(
        self,
        academic_class_id: int,
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

            ORDER BY

                a.created_at ASC

            LIMIT 1
            """
        )

        result = await self.db.execute(

            query,

            {
                "academic_class_id": academic_class_id,
            },
        )

        row = result.mappings().first()

        return dict(row) if row else None
