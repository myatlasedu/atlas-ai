# intents/student/prompt_selector.py

from intents.student.prompt_parts.base import (
    BASE_PROMPT
)

from intents.student.prompt_parts.date_rules import (
    DATE_RULES
)

from intents.student.prompt_parts.module_rules import (
    MODULE_RULES
)

from intents.student.prompt_parts.response_format import (
    RESPONSE_FORMAT
)

from intents.student.prompt_parts.action_confirmation import (
    ACTION_CONFIRMATION_PROMPT
)

from intents.student.prompt_parts.attendance import (
    ATTENDANCE_PROMPT
)

from intents.student.prompt_parts.homework import (
    HOMEWORK_PROMPT
)

from intents.student.prompt_parts.assessment import (
    ASSESSMENT_PROMPT
)

from intents.student.prompt_parts.atlas import (
    ATLAS_PROMPT
)

from intents.student.prompt_parts.performance import (
    PERFORMANCE_PROMPT
)

from intents.student.prompt_parts.accouncement import (
    ANNOUNCEMENT_PROMPT
)

from intents.student.prompt_parts.forum import (
    FORUM_PROMPT
)

from intents.student.prompt_parts.subject import (
    SUBJECT_PROMPT
)

from intents.student.prompt_parts.personal_event import (
    PERSONAL_EVENT_PROMPT
)

from intents.student.prompt_parts.journal_prompt import (
    JOURNAL_PROMPT
)

from intents.student.prompt_parts.misc import (
    MISC_PROMPTS
)


def build_prompt_for_query(
    query: str
):

    query = (
        query or ""
    ).lower()

    selected_parts = [

        BASE_PROMPT,

        ACTION_CONFIRMATION_PROMPT
    ]

    # =====================================
    # JOURNAL
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "journal",
            "journals",
            "note",
            "notes",
            "reflection",
            "reflections",
            "diary",
            "wrote",
            "journaled"
        ]
    ):

        selected_parts.extend([

            JOURNAL_PROMPT
        ])

    # =====================================
    # PERSONAL EVENTS
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "event",
            "events",
            "calendar",
            "schedule",
            "meeting",
            "tomorrow",
            "today",
            "next week",
            "birthday",
            "appointment"
        ]
    ):

        selected_parts.extend([

            PERSONAL_EVENT_PROMPT
        ])

    # =====================================
    # ATTENDANCE
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "attendance",
            "present",
            "absent",
            "late",
            "school attendance"
        ]
    ):

        selected_parts.extend([

            ATTENDANCE_PROMPT
        ])

    # =====================================
    # HOMEWORK
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "homework",
            "assignment",
            "assignments",
            "submission",
            "due",
            "teacher note"
        ]
    ):

        selected_parts.extend([

            HOMEWORK_PROMPT
        ])

    # =====================================
    # ASSESSMENTS
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "assessment",
            "assessments",
            "test",
            "tests",
            "exam",
            "exams",
            "quiz",
            "quizzes",
            "grade",
            "grades",
            "marks",
            "result",
            "results"
        ]
    ):

        selected_parts.extend([

            ASSESSMENT_PROMPT
        ])

    # =====================================
    # ATLAS
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "atlas",
            "academic score",
            "growth score",
            "initiative score",
            "atlas score",
            "atlas band",
            "atlas rank",
            "pillar",
            "strongest pillar",
            "weakest pillar"
        ]
    ):

        selected_parts.extend([

            ATLAS_PROMPT
        ])

    # =====================================
    # PERFORMANCE
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "performance",
            "strength",
            "strengths",
            "weakness",
            "weaknesses",
            "risk",
            "focus",
            "improve",
            "improvement",
            "doing overall",
            "prepared",
            "readiness"
        ]
    ):

        selected_parts.extend([

            PERFORMANCE_PROMPT,

            ATLAS_PROMPT
        ])

    # =====================================
    # ANNOUNCEMENTS
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "announcement",
            "announcements",
            "notice",
            "notices"
        ]
    ):

        selected_parts.extend([

            ANNOUNCEMENT_PROMPT
        ])

    # =====================================
    # FORUM
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "forum",
            "discussion",
            "post",
            "posts",
            "thread"
        ]
    ):

        selected_parts.extend([

            FORUM_PROMPT
        ])

    # =====================================
    # SUBJECTS / TOPICS
    # =====================================

    if any(
        keyword in query
        for keyword in [

            "subject",
            "subjects",
            "topic",
            "topics",
            "chapter",
            "chapters"
        ]
    ):

        selected_parts.extend([

            SUBJECT_PROMPT
        ])

    # =====================================
    # NO MATCH
    # =====================================

    if len(selected_parts) <= 2:

        selected_parts.extend([

            ATTENDANCE_PROMPT,

            HOMEWORK_PROMPT,

            ASSESSMENT_PROMPT,

            ATLAS_PROMPT,

            PERFORMANCE_PROMPT,

            ANNOUNCEMENT_PROMPT,

            FORUM_PROMPT,

            SUBJECT_PROMPT,

            PERSONAL_EVENT_PROMPT,

            JOURNAL_PROMPT,

            MISC_PROMPTS
        ])

    # =====================================
    # GLOBAL RULES
    # =====================================

    selected_parts.extend([

        DATE_RULES,

        MODULE_RULES,

        RESPONSE_FORMAT
    ])

    # =====================================
    # DEDUPE
    # =====================================

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