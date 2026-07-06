from intents.student.enums import StudentIntent

from intents.student.prompt_parts.attendance import (
    ATTENDANCE_PROMPT
)

from intents.student.prompt_parts.homework import (
    HOMEWORK_PROMPT
)

from intents.student.prompt_parts.assessment import (
    ASSESSMENT_PROMPT
)

from intents.student.prompt_parts.performance import (
    PERFORMANCE_PROMPT
)

from intents.student.prompt_parts.atlas import (
    ATLAS_PROMPT
)

from intents.student.prompt_parts.subject import (
    SUBJECT_PROMPT
)

from intents.student.prompt_parts.topic import (
    TOPIC_PROMPT
)

from intents.student.prompt_parts.announcement import (
    ANNOUNCEMENT_PROMPT
)

from intents.student.prompt_parts.forum import (
    FORUM_PROMPT
)

from intents.student.prompt_parts.personal_event import (
    PERSONAL_EVENT_PROMPT
)

from intents.student.prompt_parts.journal_prompt import (
    JOURNAL_PROMPT
)

from intents.student.prompt_parts.action_confirmation import (
    ACTION_CONFIRMATION_PROMPT
)

from intents.student.prompt_parts.screen_navigation import (
    SCREEN_NAVIGATION_PROMPT
)


PROMPT_MAP = {

    StudentIntent.ATTENDANCE_SUMMARY:
        ATTENDANCE_PROMPT,

    StudentIntent.HOMEWORK_SUMMARY:
        HOMEWORK_PROMPT,

    StudentIntent.ASSESSMENT_SUMMARY:
        ASSESSMENT_PROMPT,

    StudentIntent.ATLAS_SCORE_SUMMARY:
        ATLAS_PROMPT,

    StudentIntent.STUDENT_PERFORMANCE:
        PERFORMANCE_PROMPT,

    StudentIntent.SUBJECT_SUMMARY:
        SUBJECT_PROMPT,

    StudentIntent.TOPIC_SUMMARY:
        TOPIC_PROMPT,

    StudentIntent.ANNOUNCEMENT_SUMMARY:
        ANNOUNCEMENT_PROMPT,

    StudentIntent.FORUM_SUMMARY:
        FORUM_PROMPT,

    StudentIntent.PERSONAL_EVENT_SUMMARY:
        PERSONAL_EVENT_PROMPT,

    StudentIntent.PERSONAL_EVENT_CREATE:
        PERSONAL_EVENT_PROMPT,

    StudentIntent.JOURNAL_SUMMARY:
        JOURNAL_PROMPT,

    StudentIntent.JOURNAL_CREATE:
        JOURNAL_PROMPT,

    StudentIntent.ACTION_CONFIRMATION:
        ACTION_CONFIRMATION_PROMPT,

    StudentIntent.SCREEN_NAVIGATION:
        SCREEN_NAVIGATION_PROMPT,
}

def get_student_intent_prompt(
    intent: StudentIntent
):

    prompt = PROMPT_MAP.get(
        intent,
        ""
    )

    return f"""
You are Atlas AI's student intent parser.

The user's intent has ALREADY been classified.

Intent:

{intent.value}

You MUST keep the intent field exactly as:

"{intent.value}"

Do NOT change it.

Do NOT invent another intent.

Your only job is to extract:

- dates
- subject
- topic
- view
- any other parameters relevant to this intent

{prompt}

Return:

{{
    "intent": "{intent.value}",
    "start_date": null,
    "end_date": null,
    "subject": null,
    "topic": null,
    "view": null,
    "target_modules": [],
    "confidence": 0.95
}}
"""