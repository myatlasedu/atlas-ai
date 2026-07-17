from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.calendar_repository import (
    CalendarRepository
)


class CalendarTool:

    async def run(
        self,
        context,
        parsed_intent,
    ):

        if not context.academic_class_id:

            return {

                "module": "calendar",

                "event_count": 0,

                "events": [],

                "direct_answer":
                    "Academic class information is unavailable."
            }

        topic = getattr(
            parsed_intent,
            "topic",
            None,
        )

        start_date = getattr(
            parsed_intent,
            "start_date",
            None,
        )

        end_date = getattr(
            parsed_intent,
            "end_date",
            None,
        )

        async with AsyncSessionLocal() as db:

            repo = CalendarRepository(
                db
            )

            #
            # Upcoming events
            #

            if not start_date and not end_date and not topic:

                events = await repo.get_upcoming_events(
                    academic_class_id=context.academic_class_id,
                    limit=5,
                )

            else:

                events = await repo.search_events(

                    academic_class_id=context.academic_class_id,

                    start_date=start_date,

                    end_date=end_date,

                    keyword=topic,
                )

            payload = {

                "module":
                    "calendar",

                "event_count":
                    len(events),

                "events":
                    events,

                "llm_context": {

                    "event_count":
                        len(events),

                    "next_event":
                        events[0]
                        if events
                        else None,

                    "events":
                        events,
                },
            }

            if events:

                next_event = events[0]

                payload["direct_answer"] = (

                    f"Found {len(events)} upcoming calendar "
                    f"event{'s' if len(events) != 1 else ''}. "
                    f"The next event is "
                    f"{next_event['title']}."
                )

            else:

                if topic:

                    payload["direct_answer"] = (
                        f"No calendar events were found matching '{topic}'."
                    )

                elif start_date or end_date:

                    payload["direct_answer"] = (
                        "No calendar events were found in that date range."
                    )

                else:

                    payload["direct_answer"] = (
                        "There are no upcoming calendar events."
                    )

            return payload