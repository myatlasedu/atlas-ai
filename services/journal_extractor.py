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

        prompt = prompt = f"""
Extract the journal entry from the student's message.

Student message

{query}

Return ONLY valid JSON.

Schema

{{
    "content": ""
}}

Rules

1. Extract ONLY the journal content.

2. Remove commands such as

- save this in my journal
- add this to my journal
- journal this
- save this
- remember this
- log this
- create a journal entry
- make a journal entry
- write this in my journal
- note this down

3. Preserve the student's exact wording.

4. Preserve punctuation.

5. Preserve line breaks.

6. Preserve paragraphs.

7. Do NOT rewrite.

8. Do NOT summarize.

9. Do NOT improve grammar.

10. Do NOT add any extra text.

11. Do NOT include quotation marks unless they are part of the student's message.

12. If nothing remains after removing the command phrases, return

{{
    "content": ""
}}

Return ONLY valid JSON.
"""

        response = await chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You extract journal entries. "
                        "Never rewrite, summarize, correct, or improve the student's writing. "
                        "Return only valid JSON."
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
            "Journal extractor response: %s",
            content
        )

        return json.loads(
            content
        )