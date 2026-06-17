from intents.student.enums import (
    StudentIntent
)


def get_tools_for_intent(
    intent
):
    if (
        intent
        ==
        StudentIntent.UNKNOWN
    ):

        return []

    # =====================================
    # DAILY SUMMARY
    # =====================================

    if (
        intent
        ==
        StudentIntent.DAILY_SUMMARY
    ):

        return [

            "attendance_tool",

            "homework_tool",

            "assessment_tool",

            "announcement_tool",

            "atlas_tool"
        ]

    # =====================================
    # ATTENDANCE
    # =====================================

    if (
        intent
        ==
        StudentIntent.ATTENDANCE_SUMMARY
    ):

        return [
            "attendance_tool"
        ]

    # =====================================
    # HOMEWORK
    # =====================================

    if (
        intent
        ==
        StudentIntent.HOMEWORK_SUMMARY
    ):

        return [
            "homework_tool"
        ]

    # =====================================
    # ASSESSMENTS
    # =====================================

    if (
        intent
        ==
        StudentIntent.ASSESSMENT_SUMMARY
    ):

        return [
            "assessment_tool"
        ]

    # =====================================
    # ATLAS SCORE
    # =====================================

    if (
        intent
        ==
        StudentIntent.ATLAS_SCORE_SUMMARY
    ):

        return [
            "atlas_tool"
        ]

    # =====================================
    # PERFORMANCE
    # =====================================

    if (
        intent
        ==
        StudentIntent.STUDENT_PERFORMANCE
    ):

        return [
            "student_performance_tool"
        ]

    # =====================================
    # REPORT
    # =====================================

    if (
        intent
        ==
        StudentIntent.STUDENT_REPORT
    ):

        return [

            "atlas_tool",

            "attendance_tool",

            "homework_tool",

            "assessment_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.ANNOUNCEMENT_SUMMARY
    ):

        return [
            "announcement_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.FORUM_SUMMARY
    ):

        return [
            "forum_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.SUBJECT_SUMMARY
    ):

        return [
            "subject_tool"
        ]

    if (
        intent
        ==
        StudentIntent.TOPIC_SUMMARY
    ):

        return [
            "topic_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.JOURNAL_SUMMARY
    ):

        return [
            "journal_tool"
        ]

    if (
        intent
        ==
        StudentIntent.JOURNAL_CREATE
    ):

        return [
            "journal_create_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.PERSONAL_EVENT_SUMMARY
    ):

        return [
            "personal_event_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.PERSONAL_EVENT_CREATE
    ):

        return [
            "personal_event_create_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.SCREEN_NAVIGATION
    ):

        return [
            "screen_navigation_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.ACTION_CONFIRMATION
    ):

        return [
            "action_executor_tool"
        ]
    
    if (
        intent
        ==
        StudentIntent.ACTION_CONFIRMATION
    ):

        return [
            "action_executor_tool"
        ]
    
    return []

