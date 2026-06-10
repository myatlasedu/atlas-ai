import json
import logging

from llm.client import (
    chat_completion
)

logger = logging.getLogger(__name__)


class JournalExtractor:

    async def extract(
        self,
        query: str
    ):

        prompt = f"""
Extract a journal entry.

User message:

{query}

Return ONLY JSON.

Schema:

{{
    "content": ""
}}

Rules:

- Extract only the journal content.
- Remove phrases like:
  - save this in my journal
  - journal this
  - add this to my journal
  - save this
- Preserve the student's actual text.
- Return JSON only.
"""

        response = await chat_completion(
            [
                {
                    "role": "system",
                    "content":
                        "Extract journal content. Return JSON only."
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
            "Journal extractor response: %s",
            content
        )

        return json.loads(
            content
        )