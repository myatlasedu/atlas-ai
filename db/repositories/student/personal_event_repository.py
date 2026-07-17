from sqlalchemy import text
from datetime import datetime

class PersonalEventRepository:

    def __init__(
        self,
        db
    ):
        self.db = db

    async def get_events(
        self,
        student_id: int,
        start_date: str,
        end_date: str
    ):


        query = text(
            """
            SELECT

                id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                description

            FROM students_personalevent

            WHERE student_id = :student_id

            AND DATE(start_datetime)
                BETWEEN :start_date
                AND :end_date

            ORDER BY start_datetime ASC
            """
        )

        result = await self.db.execute(
            query,
            {
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        rows = result.mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    async def create_event(
        self,
        student_id: int,
        title: str,
        event_type: int,
        start_datetime,
        end_datetime=None,
        description=None
    ):

        if isinstance(
            start_datetime,
            str
        ):

            start_datetime = (
                datetime.fromisoformat(
                    start_datetime
                )
            )

        if (
            end_datetime
            and
            isinstance(
                end_datetime,
                str
            )
        ):

            end_datetime = (
                datetime.fromisoformat(
                    end_datetime
                )
            )

        query = text(
            """
            INSERT INTO students_personalevent (

                student_id,
                title,
                description,
                event_type,
                start_datetime,
                end_datetime,
                is_all_day,
                created_at,
                updated_at

            )

            VALUES (

                :student_id,
                :title,
                :description,
                :event_type,
                :start_datetime,
                :end_datetime,
                false,
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
                "title": title,
                "description": description,
                "event_type": event_type,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime
            }
        )

        await self.db.commit()

        row = result.mappings().first()

        return dict(row)
    
    async def get_upcoming_events(
        self,
        student_id
    ):

        query = text(
            """
            SELECT

                id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                description

            FROM students_personalevent

            WHERE

                student_id = :student_id

                AND start_datetime >= NOW()

            ORDER BY
                start_datetime ASC
            """
        )

        result = await self.db.execute(
            query,
            {
                "student_id": student_id
            }
        )

        return [
            dict(row)
            for row in result.mappings().all()
        ]