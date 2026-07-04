from enum import Enum


class MentorIntent(str, Enum):

    # ==========================
    # Attendance
    # ==========================

    ATTENDANCE_SUMMARY = (
        "attendance_summary"
    )

    # ==========================
    # Homework
    # ==========================

    HOMEWORK_SUMMARY = (
        "homework_summary"
    )

    # ==========================
    # Assessments
    # ==========================

    ASSESSMENT_SUMMARY = (
        "assessment_summary"
    )

    UPCOMING_ASSESSMENTS = (
        "upcoming_assessments"
    )

    GRADING_QUEUE = (
        "grading_queue"
    )

    # ==========================
    # Students
    # ==========================

    STUDENT_ANALYSIS = (
        "student_analysis"
    )

    STUDENT_RISK = (
        "student_risk"
    )

    STUDENT_REPORT = (
        "student_report"
    )

    # ==========================
    # Timetable
    # ==========================

    TIMETABLE_SUMMARY = (
        "timetable_summary"
    )

    # ==========================
    # Dashboard
    # ==========================

    DASHBOARD_SUMMARY = (
        "dashboard_summary"
    )

    # ==========================
    # Announcements
    # ==========================

    ANNOUNCEMENT_SUMMARY = (
        "announcement_summary"
    )

    # ==========================
    # Unknown
    # ==========================

    UNKNOWN = (
        "unknown"
    )