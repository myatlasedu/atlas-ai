import logging

from sqlalchemy import text


logger = logging.getLogger(__name__)


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

    async def search_planner_entries(
        self,
        user_id: int,
        start_date=None,
        end_date=None,
        keyword=None,
        limit: int = 20,
    ):

        # Planner entries live in the journal table; they are the
        # rows without a subject offering.

        where = [
            "user_id = :user_id",
            "subject_offering_id IS NULL",
            "is_active = TRUE",
        ]

        params = {
            "user_id": user_id,
            "limit": limit,
        }

        if start_date:

            where.append(
                "journal_date >= :start_date"
            )

            params["start_date"] = start_date

        if end_date:

            where.append(
                "journal_date <= :end_date"
            )

            params["end_date"] = end_date

        if keyword:

            where.append(
                "LOWER(content) LIKE LOWER(:keyword)"
            )

            params["keyword"] = f"%{keyword.strip()}%"

        query = text(
            f"""
            SELECT

                id,
                content,
                tag,
                journal_date

            FROM students_journal

            WHERE {" AND ".join(where)}

            ORDER BY journal_date DESC, id DESC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            params,
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]

    async def create_entry(
        self,
        user_id: int,
        content: str,
        tag: str = "Academic",
        journal_date=None,
    ):

        try:

            query = text(
                """
                INSERT INTO students_journal (

                    user_id,
                    content,
                    journal_date,
                    tag,
                    is_active,
                    created_at,
                    updated_at

                )

                VALUES (

                    :user_id,
                    :content,
                    COALESCE(:journal_date, CURRENT_DATE),
                    :tag,
                    TRUE,
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
                    "journal_date": journal_date,
                    "tag": tag or "Academic",
                },
            )

            await self.db.commit()

            return result.scalar_one()

        except Exception as e:

            await self.db.rollback()

            logger.warning(
                "Journal insert failed (%s);",
                e,
            )

            return None