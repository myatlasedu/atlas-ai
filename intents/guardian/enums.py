from enum import Enum


class GuardianIntent(
    str,
    Enum
):

    ATTENDANCE_SUMMARY = (
        "attendance_summary"
    )

    HOMEWORK_SUMMARY = (
        "homework_summary"
    )

    ASSESSMENT_SUMMARY = (
        "assessment_summary"
    )

    ATLAS_SCORE_SUMMARY = (
        "atlas_score_summary"
    )

    STUDENT_PERFORMANCE = (
        "student_performance"
    )

    SUBJECT_SUMMARY = (
        "subject_summary"
    )

    ANNOUNCEMENT_SUMMARY = (
        "announcement_summary"
    )

    FORUM_SUMMARY = (
        "forum_summary"
    )

    CALENDAR_SUMMARY = (
        "calendar_summary"
    )

    TIMETABLE_SUMMARY = (
        "timetable_summary"
    )

    STUDENT_REPORT = (
        "student_report"
    )

    UNKNOWN = (
        "unknown"
    )