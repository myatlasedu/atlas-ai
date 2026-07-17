from intents.student.enums import (
    StudentIntent
)


TOOL_MAP = {

    StudentIntent.DAILY_SUMMARY: [

        "attendance_tool",

        "homework_tool",

        "assessment_tool",

        "announcement_tool",

        "atlas_tool",

        "calendar_tool"
    ],

    StudentIntent.ATTENDANCE_SUMMARY: [

        "attendance_tool"
    ],

    StudentIntent.HOMEWORK_SUMMARY: [

        "homework_tool"
    ],

    StudentIntent.ASSESSMENT_SUMMARY: [

        "assessment_tool"
    ],

    StudentIntent.ATLAS_SCORE_SUMMARY: [

        "atlas_tool"
    ],

    StudentIntent.STUDENT_PERFORMANCE: [

        "student_performance_tool"
    ],


    StudentIntent.STUDENT_REPORT: [

        "atlas_tool",

        "attendance_tool",

        "homework_tool",

        "assessment_tool"
    ],

    StudentIntent.ANNOUNCEMENT_SUMMARY: [

        "announcement_tool"
    ],

    StudentIntent.CALENDAR_SUMMARY: [

        "calendar_tool"
    ],

    StudentIntent.FORUM_SUMMARY: [

        "forum_tool"
    ],

    StudentIntent.SUBJECT_SUMMARY: [

        "subject_tool"
    ],

    StudentIntent.TOPIC_SUMMARY: [

        "topic_tool"
    ],

    StudentIntent.JOURNAL_SUMMARY: [

        "journal_tool"
    ],

    StudentIntent.JOURNAL_CREATE: [

        "journal_create_tool"
    ],

    StudentIntent.PERSONAL_EVENT_SUMMARY: [

        "personal_event_tool"
    ],

    StudentIntent.PERSONAL_EVENT_CREATE: [

        "personal_event_create_tool"
    ],

    StudentIntent.SCREEN_NAVIGATION: [

        "screen_navigation_tool"
    ],

    StudentIntent.ACTION_CONFIRMATION: [

        "action_executor_tool"
    ]
}


def get_tools_for_intent(
    intent: StudentIntent
) -> list[str]:

    return TOOL_MAP.get(
        intent,
        []
    )

