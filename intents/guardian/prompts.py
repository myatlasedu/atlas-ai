from intents.guardian.enums import (
    GuardianIntent
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

from intents.student.prompt_parts.subject import (
    SUBJECT_PROMPT
)

from intents.student.prompt_parts.announcement import (
    ANNOUNCEMENT_PROMPT
)

from intents.student.prompt_parts.forum import (
    FORUM_PROMPT
)

# from intents.guardian.prompt_parts.student_report import (
#     STUDENT_REPORT_PROMPT
# )


PROMPT_MAP = {

    GuardianIntent.ATTENDANCE_SUMMARY:
        ATTENDANCE_PROMPT,

    GuardianIntent.HOMEWORK_SUMMARY:
        HOMEWORK_PROMPT,

    GuardianIntent.ASSESSMENT_SUMMARY:
        ASSESSMENT_PROMPT,

    GuardianIntent.ATLAS_SCORE_SUMMARY:
        ATLAS_PROMPT,

    GuardianIntent.STUDENT_PERFORMANCE:
        PERFORMANCE_PROMPT,

    GuardianIntent.SUBJECT_SUMMARY:
        SUBJECT_PROMPT,

    GuardianIntent.ANNOUNCEMENT_SUMMARY:
        ANNOUNCEMENT_PROMPT,

    GuardianIntent.FORUM_SUMMARY:
        FORUM_PROMPT,

    # GuardianIntent.STUDENT_REPORT:
    #     STUDENT_REPORT_PROMPT,
}


def get_guardian_intent_prompt(
    intent: GuardianIntent
):

    prompt = PROMPT_MAP.get(
        intent,
        ""
    )

    return f"""
You are Atlas AI's guardian intent parser.

The user's intent has ALREADY been classified.

Intent:

{intent.value}

You MUST keep the intent field exactly as:

"{intent.value}"

Do NOT change it.

Do NOT invent another intent.

Your only job is to extract:

- dates
- grade
- section
- subject
- enrichment
- view

{prompt}

Return:

{{
    "intent": "{intent.value}",
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