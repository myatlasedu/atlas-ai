from db.session import (
    AsyncSessionLocal
)

from db.repositories.personal_event_repository import (
    PersonalEventRepository
)


class PersonalEventTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        async with AsyncSessionLocal() as db:

            repo = (
                PersonalEventRepository(
                    db
                )
            )

            events = await repo.get_events(

                student_id=
                    context.student_id,

                start_date=
                    parsed_intent.start_date,

                end_date=
                    parsed_intent.end_date
            )

            payload = {

                "module":
                    "personal_event",

                "event_count":
                    len(events),

                "events":
                    events
            }

            query = (
                getattr(
                    parsed_intent,
                    "original_query",
                    ""
                )
                .lower()
            )

            if any(
                phrase in query
                for phrase in [

                    "events",

                    "calendar",

                    "schedule",

                    "tomorrow",

                    "today",

                    "upcoming",

                    "reminders"
                ]
            ):

                if not events:

                    payload[
                        "direct_answer"
                    ] = (
                        "You have no "
                        "events scheduled."
                    )

            return payload