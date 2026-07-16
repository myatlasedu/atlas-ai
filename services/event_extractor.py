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
    "end_datetime": null,
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

Examples:

User:
Remind me to study maths tomorrow at 6pm

Output:
{{
    "title": "Study Maths",
    "event_type": "STUDY",
    "start_datetime": "2026-06-11T18:00:00",
    "end_datetime": null,
    "description": null
}}

User:
Schedule football practice on Saturday at 5pm

Output:
{{
    "title": "Football Practice",
    "event_type": "ACTIVITY",
    "start_datetime": "2026-06-13T17:00:00",
    "end_datetime": null,
    "description": null
}}

User:
Remind me about my chemistry exam next Monday

Output:
{{
    "title": "Chemistry Exam",
    "event_type": "EXAM",
    "start_datetime": "2026-06-15T09:00:00",
    "end_datetime": null,
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