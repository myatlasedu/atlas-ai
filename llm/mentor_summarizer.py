import json
import logging

from llm.client import (
    chat_completion
)

from intents.mentor.enums import (
    MentorIntent
)

logger = logging.getLogger(__name__)


def build_prompt(
    query: str,
    data: dict,
    intent
):

    common = f"""
USER QUERY:

{query}

DATA:

{json.dumps(data, indent=2, default=str)}

====================================

You are Atlas Mentor AI.

Use ONLY supplied data.

Never invent information.

Never assume missing information.

Never create attendance records.

Never create homework.

Never create assessments.

Keep the response concise.

Maximum 120 words.
"""

    if intent == MentorIntent.ATTENDANCE_SUMMARY:

        return f"""
You are Atlas Mentor AI.

You are assisting a teacher.

Use ONLY attendance data.

Summarize:

- attendance percentage
- absent students
- late students
- half day students

If student names are available,
mention them.

Do not invent students.

{common}
"""

    if intent == MentorIntent.HOMEWORK_SUMMARY:

        return f"""
You are Atlas Mentor AI.

Summarize homework information only.

Use only supplied homework data.

{common}
"""

    if intent == MentorIntent.ASSESSMENT_SUMMARY:

        return f"""
You are Atlas Mentor AI.

Summarize assessment information only.

Use only supplied assessment data.

{common}
"""

    return common


async def summarize_response(
    query: str,
    data: dict,
    context,
    intent
):

    prompt = build_prompt(
        query=query,
        data=data,
        intent=intent
    )

    response = await chat_completion(
        [
            {
                "role": "system",
                "content": """
You are Atlas Mentor AI.

Only use supplied data.

Never invent information.

Answer like an experienced teacher assistant.

Maximum 120 words.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    logger.info(
        "Mentor summarizer: %s",
        response
    )

    return response["message"]["content"]