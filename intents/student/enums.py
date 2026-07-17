from enum import Enum


class StudentIntent(str, Enum):

    DAILY_SUMMARY = "daily_summary"

    ATTENDANCE_SUMMARY = "attendance_summary"

    HOMEWORK_SUMMARY = "homework_summary"

    ASSESSMENT_SUMMARY = "assessment_summary"

    ATLAS_SCORE_SUMMARY = "atlas_score_summary"

    ANNOUNCEMENT_SUMMARY = "announcement_summary"

    FORUM_SUMMARY = "forum_summary"

    SUBJECT_SUMMARY = "subject_summary"

    STUDENT_PERFORMANCE = "student_performance"

    STUDENT_REPORT = "student_report"

    TIMETABLE_SUMMARY = "timetable_summary"

    TOPIC_SUMMARY = "topic_summary"

    PERSONAL_EVENT_SUMMARY = "personal_event_summary"

    PERSONAL_EVENT_CREATE = "personal_event_create"

    JOURNAL_SUMMARY = "journal_summary"
    
    JOURNAL_CREATE = "journal_create"

    SCREEN_NAVIGATION = "screen_navigation"

    ACTION_CONFIRMATION = "action_confirmation"

    CALENDAR_SUMMARY = "calendar_summary"

    UNKNOWN = "unknown"
  

