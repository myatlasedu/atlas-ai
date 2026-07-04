import asyncio

from db.session import AsyncSessionLocal

from db.repositories.student.personal_event_repository import (
    PersonalEventRepository
)


async def main():

    async with AsyncSessionLocal() as db:

        repo = PersonalEventRepository(
            db
        )

        result = await repo.create_event(
            student_id=2,
            title="Study Maths",
            event_type=2,
            start_datetime="2026-06-11T18:00:00"
        )

        print(result)


asyncio.run(main())