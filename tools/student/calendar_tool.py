from db.session import (
    AsyncSessionLocal
)

from db.repositories.student.calendar_repository import (
    CalendarRepository
)


class CalendarTool:

    EVENT_KEYWORDS = {
        "holiday": (
            "holiday",
            "holidays",
        ),
        "exam": (
            "exam",
            "exams",
            "test",
            "tests",
        ),
        "activity": (
            "activity",
            "activities",
        ),
        "event": (
            "event",
            "events",
        ),
    }

    def _resolve_keyword(
        self,
        parsed_intent,
    ):

        #
        # Prefer LLM extracted topic if available.
        # Example:
        # "Science Exhibition"
        #

        topic = getattr(
            parsed_intent,
            "topic",
            None,
        )

        if topic:

            return topic

        query = (
            getattr(
                parsed_intent,
                "original_query",
                "",
            )
            .lower()
            .strip()
        )

        for keyword, aliases in self.EVENT_KEYWORDS.items():

            if any(
                alias in query
                for alias in aliases
            ):
                return keyword

        return None

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

        keyword = self._resolve_keyword(
            parsed_intent
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

            if not start_date and not end_date:

                events = await repo.get_upcoming_events(

                    academic_class_id=context.academic_class_id,

                    keyword=keyword,

                    limit=5,
                )

            #
            # Search events
            #

            else:

                events = await repo.search_events(

                    academic_class_id=context.academic_class_id,

                    start_date=start_date,

                    end_date=end_date,

                    keyword=keyword,
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

                    f"Found {len(events)} "
                    f"calendar event{'s' if len(events) != 1 else ''}. "
                    f"The next event is "
                    f"{next_event['title']}."
                )

            else:

                if keyword:

                    payload["direct_answer"] = (
                        f"No calendar events were found matching '{keyword}'."
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