from intents.student.enums import (
    StudentIntent,
)

from intents.student.prompt_parts.attendance import (
    ATTENDANCE_PROMPT,
)

from intents.student.prompt_parts.homework import (
    HOMEWORK_PROMPT,
)

from intents.student.prompt_parts.assessment import (
    ASSESSMENT_PROMPT,
)

from intents.student.prompt_parts.performance import (
    PERFORMANCE_PROMPT,
)

from intents.student.prompt_parts.atlas import (
    ATLAS_PROMPT,
)

from intents.student.prompt_parts.subject import (
    SUBJECT_PROMPT,
)

from intents.student.prompt_parts.topic import (
    TOPIC_PROMPT,
)

from intents.student.prompt_parts.announcement import (
    ANNOUNCEMENT_PROMPT,
)

from intents.student.prompt_parts.forum import (
    FORUM_PROMPT,
)

from intents.student.prompt_parts.calendar import (
    CALENDAR_PROMPT,
)

from intents.student.prompt_parts.personal_event import (
    PERSONAL_EVENT_PROMPT,
)

from intents.student.prompt_parts.journal_prompt import (
    JOURNAL_PROMPT,
)

from intents.student.prompt_parts.action_confirmation import (
    ACTION_CONFIRMATION_PROMPT,
)

from intents.student.prompt_parts.screen_navigation import (
    SCREEN_NAVIGATION_PROMPT,
)

from intents.student.prompt_parts.timetable import (
    TIMETABLE_PROMPT,
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

    StudentIntent.CALENDAR_SUMMARY:
        CALENDAR_PROMPT,

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

    StudentIntent.TIMETABLE_SUMMARY:
        TIMETABLE_PROMPT,
}


def get_student_intent_prompt(
    intent: StudentIntent,
):

    prompt = PROMPT_MAP.get(
        intent,
        "",
    )

    return f"""
You are Atlas AI's student intent parameter parser.

The user's intent has ALREADY been classified by a separate
intent classifier.

You MUST TRUST the provided intent.

==================================================
CLASSIFIED INTENT
==================================================

{intent.value}

The classified intent is authoritative.

You MUST keep the intent field exactly as:

"{intent.value}"

Do NOT change it.

Do NOT re-classify the user.

Do NOT invent another intent.

Do NOT decide that the user belongs to another intent.

Your ONLY job is to extract the parameters required by
the already-classified intent.

==================================================
PARAMETERS
==================================================

Extract only parameters that are actually present or
required by the user's query.

Possible parameters include:

- start_date
- end_date
- subject
- topic
- view
- target_modules

Do not invent values.

Use null when a value is not present.

==================================================
CAMBRIDGE TERMINOLOGY
==================================================

Atlas AI follows Cambridge terminology.

Understand both Cambridge terminology and common
school terminology.

Treat these as equivalent where appropriate:

Structure of the Day = Timetable

SOD = Structure of the Day

Lesson = Period

Lessons = Periods

The user may say:

- Structure of the Day
- SOD
- timetable
- schedule
- lesson
- period
- lessons
- periods

When the classified intent is:

timetable_summary

interpret:

- Structure of the Day
- SOD
- Timetable
- Schedule

as the student's Structure of the Day.

Likewise:

- Lesson
- Lessons
- Period
- Periods

refer to instructional blocks.

Do NOT reinterpret the user's query as another intent.

The classifier has already made that decision.

==================================================
INTENT-SPECIFIC INSTRUCTIONS
==================================================

{prompt}

==================================================
IMPORTANT
==================================================

The intent has already been classified.

Trust:

"{intent.value}"

Even if the user's wording appears ambiguous,
DO NOT change the intent.

Only extract parameters.

Do not return explanations.

Do not return markdown.

Do not return any text outside JSON.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON:

{{
    "intent": "{intent.value}",
    "start_date": null,
    "end_date": null,
    "subject": null,
    "topic": null,
    "view": null,
    "target_modules": []
}}
"""