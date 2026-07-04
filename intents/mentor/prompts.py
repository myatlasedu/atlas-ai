from intents.mentor.enums import MentorIntent

from intents.mentor.prompt_parts.attendance import (
    ATTENDANCE_PROMPT
)

# from intents.mentor.prompt_parts.homework import (
#     HOMEWORK_PROMPT
# )

# from intents.mentor.prompt_parts.assessment import (
#     ASSESSMENT_PROMPT
# )

PROMPT_MAP = {

    MentorIntent.ATTENDANCE_SUMMARY:
        ATTENDANCE_PROMPT,

    # MentorIntent.HOMEWORK_SUMMARY:
    #     HOMEWORK_PROMPT,

    # MentorIntent.ASSESSMENT_SUMMARY:
    #     ASSESSMENT_PROMPT,
}


def get_mentor_intent_prompt(
    intent: MentorIntent
):

    prompt = PROMPT_MAP.get(
        intent,
        ""
    )

    return f"""
You are Atlas AI's mentor intent parser.

Return VALID JSON ONLY.

Never explain.

Never return markdown.

Never return text outside JSON.

{prompt}

Return:

{{
    "intent": "...",
    "start_date": null,
    "end_date": null,
    "academic_year": null,
    "grade": null,
    "section": null,
    "subject": null,
    "enrichment": null,
    "view": null,
    "target_modules": [],
    "confidence": 0.95
}}
"""