from services.event_extractor import (
    EventExtractor
)


class PersonalEventCreateTool:

    async def run(
        self,
        context,
        parsed_intent
    ):

        extractor = (
            EventExtractor()
        )

        event = await extractor.extract(
            parsed_intent.original_query
        )

        if not event:

            return {

                "module":
                    "personal_event",

                "action_required":
                    False,

                "direct_answer":
                    (
                        "I could not determine "
                        "the event details."
                    )
            }

        return {

            "module":
                "personal_event",

            "action_required":
                True,

            "confirmation_required":
                True,

            "action_type":
                "create_personal_event",

            "payload":
                event,

            "confirmation_message":
                (
                    f"Create event:\n\n"
                    f"Title: "
                    f"{event['title']}\n"
                    f"Type: "
                    f"{event['event_type']}\n"
                    f"Start: "
                    f"{event['start_datetime']}\n\n"
                    f"Reply YES to confirm."
                )
        }