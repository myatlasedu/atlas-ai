from db.session import (
    AsyncSessionLocal
)

from db.repositories.personal_event_repository import (
    PersonalEventRepository
)

from utils import format_datetime

class PersonalEventTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        query = (
            getattr(
                parsed_intent,
                "original_query",
                ""
            )
            .lower()
        )

        async with AsyncSessionLocal() as db:

            repo = (
                PersonalEventRepository(
                    db
                )
            )

            #
            # Upcoming events should not depend
            # on parser-generated dates.
            #

            if any(
                phrase in query
                for phrase in [
                    "upcoming",
                    "calendar",
                    "schedule",
                    "events",
                    "reminders"
                ]
            ):

                events = (
                    await repo.get_upcoming_events(
                        context.student_id
                    )
                )

            else:

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

            if not events:

                payload[
                    "direct_answer"
                ] = (
                    "You have no "
                    "events scheduled."
                )

                return payload


            return payload