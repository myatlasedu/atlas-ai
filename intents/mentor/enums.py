from enum import Enum


class MentorIntent(str, Enum):

    ATTENDANCE_SUMMARY = (
        "attendance_summary"
    )

    HOMEWORK_SUMMARY = (
        "homework_summary"
    )

    ASSESSMENT_SUMMARY = (
        "assessment_summary"
    )

    UPCOMING_ASSESSMENTS = (
        "upcoming_assessments"
    )

    STUDENT_ANALYSIS = (
        "student_analysis"
    )

    STUDENT_RISK = (
        "student_risk"
    )

    GRADING_QUEUE = (
        "grading_queue"
    )

    TIMETABLE_SUMMARY = (
        "timetable_summary"
    )

    DASHBOARD_SUMMARY = (
        "dashboard_summary"
    )

    UNKNOWN = (
        "unknown"
    )