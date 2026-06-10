MODULE_RULES = """
==================================================
MODULE RULES
==================================================

daily_summary
["attendance","homework","assessment","atlas"]

attendance_summary
["attendance"]

homework_summary
["homework"]

assessment_summary
["assessment"]

atlas_score_summary
["atlas"]

student_performance
[
    "attendance",
    "homework",
    "assessment",
    "subject",
    "atlas"
]

subject_summary
["subject"]

topic_summary
["topic"]

announcement_summary
["announcement"]

forum_summary
["forum"]

event_summary
["event"]

lesson_plan_summary
["lesson_plan"]

lor_summary
["lor"]

student_report
[
    "atlas",
    "attendance",
    "homework",
    "assessment",
    "subject"
]

personal_event_summary
["personal_event"]

personal_event_create
["personal_event_create"]

action_confirmation
[]
"""