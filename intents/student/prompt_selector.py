# intents/student/prompt_selector.py

from intents.student.enums import (
    StudentIntent,
)

from intents.student.prompt_parts.base import (
    BASE_PROMPT,
)

from intents.student.prompt_parts.date_rules import (
    DATE_RULES,
)

from intents.student.prompt_parts.module_rules import (
    MODULE_RULES,
)

from intents.student.prompt_parts.response_format import (
    RESPONSE_FORMAT,
)

from intents.student.prompt_parts.action_confirmation import (
    ACTION_CONFIRMATION_PROMPT,
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

from intents.student.prompt_parts.atlas import (
    ATLAS_PROMPT,
)

from intents.student.prompt_parts.performance import (
    PERFORMANCE_PROMPT,
)

from intents.student.prompt_parts.announcement import (
    ANNOUNCEMENT_PROMPT,
)

from intents.student.prompt_parts.forum import (
    FORUM_PROMPT,
)

from intents.student.prompt_parts.subject import (
    SUBJECT_PROMPT,
)

from intents.student.prompt_parts.topic import (
    TOPIC_PROMPT,
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

from intents.student.prompt_parts.misc import (
    MISC_PROMPTS,
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

    StudentIntent.TIMETABLE_SUMMARY:
        TIMETABLE_PROMPT,

    StudentIntent.STUDENT_PERFORMANCE:
        PERFORMANCE_PROMPT,

    StudentIntent.STUDENT_REPORT:
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

    StudentIntent.JOURNAL_SUMMARY:
        JOURNAL_PROMPT,

    StudentIntent.SCREEN_NAVIGATION:
        SCREEN_NAVIGATION_PROMPT,

    StudentIntent.ACTION_CONFIRMATION:
        ACTION_CONFIRMATION_PROMPT,

    
}


def build_prompt_for_intent(
    intent: StudentIntent,
):

    selected_parts = [

        BASE_PROMPT,

        PROMPT_MAP.get(
            intent,
            MISC_PROMPTS,
        ),

        DATE_RULES,

        MODULE_RULES,

        RESPONSE_FORMAT,
    ]

    seen = set()

    unique_parts = []

    for part in selected_parts:

        if part in seen:
            continue

        seen.add(part)

        unique_parts.append(part)

    return "\n\n".join(
        unique_parts
    )