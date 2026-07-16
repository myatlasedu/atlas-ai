from sqlalchemy import text


class JournalRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def search_entries(
        self,
        user_id: int,
        start_date=None,
        end_date=None,
        keyword=None,
        limit: int = 20,
    ):

        where = [
            "user_id = :user_id"
        ]

        params = {
            "user_id": user_id,
            "limit": limit,
        }

        if start_date:

            where.append(
                "DATE(created_at) >= :start_date"
            )

            params["start_date"] = start_date

        if end_date:

            where.append(
                "DATE(created_at) <= :end_date"
            )

            params["end_date"] = end_date

        if keyword:

            keyword = keyword.strip()

            where.append(
                """
                (
                    LOWER(content) LIKE LOWER(:keyword)
                    OR
                    LOWER(content) LIKE LOWER(:keyword_prefix)
                    OR
                    LOWER(content) LIKE LOWER(:keyword_suffix)
                )
                """
            )

            params["keyword"] = f"%{keyword}%"
            params["keyword_prefix"] = f"{keyword}%"
            params["keyword_suffix"] = f"% {keyword}%"

        query = text(
            f"""
            SELECT

                id,
                content,
                created_at,
                updated_at

            FROM students_journal

            WHERE {" AND ".join(where)}

            ORDER BY created_at DESC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            params,
        )

        rows = []

        for row in result.mappings().all():

            item = dict(row)

            item["created_at"] = (
                item["created_at"].isoformat()
                if item["created_at"]
                else None
            )

            item["updated_at"] = (
                item["updated_at"].isoformat()
                if item["updated_at"]
                else None
            )

            rows.append(item)

        return rows

    async def get_latest_entry(
        self,
        user_id: int,
    ):

        query = text(
            """
            SELECT

                id,
                content,
                created_at,
                updated_at

            FROM students_journal

            WHERE user_id = :user_id

            ORDER BY created_at DESC

            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "user_id": user_id,
            }
        )

        row = result.mappings().first()

        return dict(row) if row else None

    async def get_oldest_entry(
        self,
        user_id: int,
    ):

        query = text(
            """
            SELECT

                id,
                content,
                created_at,
                updated_at

            FROM students_journal

            WHERE user_id = :user_id

            ORDER BY created_at ASC

            LIMIT 1
            """
        )

        result = await self.db.execute(
            query,
            {
                "user_id": user_id,
            }
        )

        row = result.mappings().first()

        return dict(row) if row else None

    async def create_entry(
        self,
        user_id: int,
        content: str,
    ):

        query = text(
            """
            INSERT INTO students_journal (

                user_id,
                content,
                created_at,
                updated_at

            )

            VALUES (

                :user_id,
                :content,
                NOW(),
                NOW()

            )

            RETURNING id
            """
        )

        result = await self.db.execute(
            query,
            {
                "user_id": user_id,
                "content": content,
            }
        )

        await self.db.commit()

        return result.scalar_one()