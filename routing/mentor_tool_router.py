from intents.mentor.enums import (
    MentorIntent
)


TOOL_MAP = {

    MentorIntent.ATTENDANCE_SUMMARY: [

        "attendance_tool"

    ],

    MentorIntent.HOMEWORK_SUMMARY: [

        "homework_tool"

    ],

    MentorIntent.ASSESSMENT_SUMMARY: [

        "assessment_tool"

    ],

    MentorIntent.UPCOMING_ASSESSMENTS: [

        "assessment_tool"

    ],

    MentorIntent.STUDENT_ANALYSIS: [

        "student_analysis_tool"

    ],

    MentorIntent.STUDENT_RISK: [

        "student_analysis_tool"

    ],

    MentorIntent.GRADING_QUEUE: [

        "grading_tool"

    ],

    MentorIntent.TIMETABLE_SUMMARY: [

        "timetable_tool"

    ],

    MentorIntent.DASHBOARD_SUMMARY: [

        "dashboard_tool"

    ]
}


def get_tools_for_intent(
    intent: MentorIntent
) -> list[str]:

    return TOOL_MAP.get(
        intent,
        []
    )