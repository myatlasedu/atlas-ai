import json
import logging
from utils import ist_now

from llm.client import (
    chat_completion
)

from datetime import datetime


logger = logging.getLogger(__name__)
today = ist_now().date()


class EventExtractor:

    async def extract(
        self,
        query: str
    ):

        prompt = f"""
Extract a personal event from the user request.

Current date:
{today.isoformat()}

User request:

{query}

Return ONLY valid JSON.

Schema:

{{
    "title": "",
    "event_type": "",
    "start_datetime": "",
    "end_datetime": "",
    "description": null
}}

Rules:

event_type must be one of:

PERSONAL
STUDY
EXAM
ACTIVITY
REMINDER

Infer event_type.

For start_datetime and end_datetime:

1. If the user explicitly provides a start and end time/date, use them directly.

2. If the user says "tomorrow", "next day", or specifies a single date such as "05 October"
   without mentioning a time, duration or end date, it is an all-day event:
   - Set start_datetime to that date at 00:00:00.
   - Set end_datetime to the SAME date at 23:59:59.
   - end_datetime must NEVER equal start_datetime.

3. If the user says "for the next two days", "for two days", or similar duration:
   - Set start_datetime to the mentioned date at 00:00:00.
   - Set end_datetime to the last day of the duration at 23:59:59.
   - Example: "Create an event for 05 October for the next two days"
     → start_datetime: 2026-10-05T00:00:00
     → end_datetime: 2026-10-06T23:59:59
4. If the user explicitly mentions an end date/time, use that as end_datetime.

5. If the user gives a start time but no end time or duration, set end_datetime
   to the SAME date as start_datetime at 23:59:59.

6. Never change the explicitly provided start date or start time.

Examples:

User:
Remind me to study maths tomorrow at 6pm

Output:
{{
    "title": "Study Maths",
    "event_type": "STUDY",
    "start_datetime": "2026-06-11T18:00:00",
    "end_datetime": "2026-06-11T23:59:59",
    "description": null
}}

User:
Schedule football practice on Saturday at 5pm

Output:
{{
    "title": "Football Practice",
    "event_type": "ACTIVITY",
    "start_datetime": "2026-06-13T17:00:00",
    "end_datetime": "2026-06-13T23:59:59",
    "description": null
}}

User:
Remind me about my chemistry exam next Monday

Output:
{{
    "title": "Chemistry Exam",
    "event_type": "EXAM",
    "start_datetime": "2026-06-15T00:00:00",
    "end_datetime": "2026-06-15T23:59:59",
    "description": null
}}

User:
Create an event for tomorrow for my school trip

Output:
{{
    "title": "School Trip",
    "event_type": "ACTIVITY",
    "start_datetime": "2026-06-11T00:00:00",
    "end_datetime": "2026-06-11T23:59:59",
    "description": null
}}

User:
Remind me to study english tomorrow from 7pm to 8pm

Output:
{{
    "title": "Study English",
    "event_type": "STUDY",
    "start_datetime": "2026-06-11T19:00:00",
    "end_datetime": "2026-06-11T20:00:00",
    "description": null
}}


User:
Maths revision tomorrow 6pm-7:30pm

Output:
{{
    "title": "Maths Revision",
    "event_type": "STUDY",
    "start_datetime": "2026-06-11T18:00:00",
    "end_datetime": "2026-06-11T19:30:00",
    "description": null
}}

Return JSON only.
"""

        response = await chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You extract calendar events. "
                        "Return JSON only."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = (
            response["message"]["content"]
            .strip()
        )

        logger.info(
            "Event extractor response: %s",
            content
        )

        try:

            return json.loads(
                content
            )

        except Exception:

            logger.exception(
                "Failed to parse event extraction"
            )

            return None