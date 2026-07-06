from sqlalchemy import text


class JournalRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_recent_entries(
        self,
        student_id: int,
        limit: int = 20
    ):

        query = text(
            """
            SELECT

                id,
                content,
                created_at,
                updated_at

            FROM students_journal

            WHERE student_id = :student_id

            ORDER BY created_at DESC

            LIMIT :limit
            """
        )

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "limit": limit
            }
        )

        return [

            dict(row)

            for row

            in result.mappings().all()
        ]
    
    async def create_entry(
        self,
        student_id: int,
        content: str
    ):

        query = text(
            """
            INSERT INTO students_journal (

                student_id,
                content,
                created_at,
                updated_at

            )

            VALUES (

                :student_id,
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
                "student_id": student_id,
                "content": content
            }
        )

        await self.db.commit()

        return result.scalar_one()