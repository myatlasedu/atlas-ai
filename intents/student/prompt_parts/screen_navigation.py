SCREEN_NAVIGATION_PROMPT = """
--------------------------------------------------

screen_navigation

Used when the student wants to navigate
to a screen inside the application.

Supported Targets:

- profile
- homework
- attendance
- journal
- forum
- events
- classroom
- timetable
- enrichment
- announcements
- notifications
- wellbeing
- healthroom
- assessment
- report_card

==================================================

Examples

Open homework
→ navigation_target=homework

Take me to homework
→ navigation_target=homework

Open assignments
→ navigation_target=homework

Show attendance page
→ navigation_target=attendance

Open journal
→ navigation_target=journal

Take me to the forum
→ navigation_target=forum

Open calendar
→ navigation_target=events

Show my events
→ navigation_target=events

Open classroom
→ navigation_target=classroom

Open timetable
→ navigation_target=timetable

Open enrichment
→ navigation_target=enrichment

Show announcements
→ navigation_target=announcements

Open notifications
→ navigation_target=notifications

Open wellbeing
→ navigation_target=wellbeing

Open health room
→ navigation_target=healthroom

Open profile
→ navigation_target=profile

Show my profile
→ navigation_target=profile

Open assessment
→ navigation_target=assessment

Take me to assessments
→ navigation_target=assessment

Open exams
→ navigation_target=assessment

Show assessments screen
→ navigation_target=assessment

Open report card
→ navigation_target=report_cards

Show my report card
→ navigation_target=report_cards

Take me to report cards
→ navigation_target=report_cards

Open report card screen
→ navigation_target=report_cards

View my report
→ navigation_target=report_cards

Show my academic report
→ navigation_target=report_cards

==================================================

IMPORTANT

Only classify as screen_navigation
when the user wants to navigate.

Examples:

- open homework
- take me to attendance
- open profile
- show timetable
- go to wellbeing

Do NOT classify as screen_navigation
when asking for information.

Examples:

What homework is pending?
→ homework_summary

What is my attendance percentage?
→ attendance_summary

What events do I have tomorrow?
→ personal_event_summary

Show my wellbeing report
→ wellbeing_summary

Return:

screen_navigation
"""