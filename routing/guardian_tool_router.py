from intents.guardian.enums import (
    GuardianIntent
)


TOOL_MAP = {

    GuardianIntent.ATTENDANCE_SUMMARY: [

        "attendance_tool"

    ],

    GuardianIntent.HOMEWORK_SUMMARY: [

        "homework_tool"

    ],

    GuardianIntent.ASSESSMENT_SUMMARY: [

        "assessment_tool"

    ],

    GuardianIntent.ATLAS_SCORE_SUMMARY: [

        "atlas_tool"

    ],

    GuardianIntent.STUDENT_PERFORMANCE: [

        "student_performance_tool"

    ],

    GuardianIntent.STUDENT_REPORT: [

        "atlas_tool",

        "attendance_tool",

        "homework_tool",

        "assessment_tool"

    ],

    GuardianIntent.ANNOUNCEMENT_SUMMARY: [

        "announcement_tool"

    ],

    GuardianIntent.FORUM_SUMMARY: [

        "forum_tool"

    ],

    GuardianIntent.SUBJECT_SUMMARY: [

        "subject_tool"

    ],

    GuardianIntent.TIMETABLE_SUMMARY: [

        "timetable_tool"

    ],

    GuardianIntent.CALENDAR_SUMMARY: [

        "calendar_tool"

    ],
}


def get_tools_for_intent(
    intent: GuardianIntent,
) -> list[str]:

    return TOOL_MAP.get(
        intent,
        [],
    )