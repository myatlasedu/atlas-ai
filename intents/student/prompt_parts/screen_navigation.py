SCREEN_NAVIGATION_PROMPT = """
--------------------------------------------------

screen_navigation

Used when the student wants to navigate
to a screen inside the application.

==================================================
SUPPORTED NAVIGATION TARGETS
==================================================

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
- report_cards

==================================================
EXAMPLES
==================================================

Open homework

→ navigation_target = homework

Take me to homework

→ navigation_target = homework

Open assignments

→ navigation_target = homework

Show attendance page

→ navigation_target = attendance

Take me to attendance

→ navigation_target = attendance

Open journal

→ navigation_target = journal

Take me to the forum

→ navigation_target = forum

Open calendar

→ navigation_target = events

Show my events

→ navigation_target = events

Open classroom

→ navigation_target = classroom

Open timetable

→ navigation_target = timetable

Show my schedule

→ navigation_target = timetable

Open enrichment

→ navigation_target = enrichment

Show announcements

→ navigation_target = announcements

Open notifications

→ navigation_target = notifications

Open wellbeing

→ navigation_target = wellbeing

Open health room

→ navigation_target = healthroom

Open profile

→ navigation_target = profile

Show my profile

→ navigation_target = profile

Open assessment

→ navigation_target = assessment

Take me to assessments

→ navigation_target = assessment

Open exams

→ navigation_target = assessment

Show assessments screen

→ navigation_target = assessment

Open report card

→ navigation_target = report_cards

Show my report card

→ navigation_target = report_cards

Take me to report cards

→ navigation_target = report_cards

Open report card screen

→ navigation_target = report_cards

View my report

→ navigation_target = report_cards

Show my academic report

→ navigation_target = report_cards

==================================================
CLASSIFICATION RULES
==================================================

Classify as:

screen_navigation

ONLY when the user is asking to navigate
to a screen inside the application.

Examples:

- open homework
- take me to homework
- open attendance
- go to attendance
- open profile
- show timetable
- open exams
- open report card
- take me to announcements

==================================================
DO NOT CLASSIFY AS SCREEN NAVIGATION
==================================================

If the user is requesting information,
summaries or analytics.

Examples:

What homework is pending?

→ homework_summary

What is my attendance percentage?

→ attendance_summary

What events do I have tomorrow?

→ personal_event_summary

Show my wellbeing report.

→ wellbeing_summary

How did I perform in assessments?

→ assessment_summary

==================================================
OUTPUT RULES
==================================================

When the intent is:

screen_navigation

You MUST populate:

navigation_target

using one of the supported navigation targets.

Never leave navigation_target as null
if the destination is clearly mentioned.

Examples:

User:

Take me to homework

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "homework"
}

--------------------------------------------------

User:

Open attendance

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "attendance"
}

--------------------------------------------------

User:

Open timetable

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "timetable"
}

--------------------------------------------------

User:

Open exams

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "assessment"
}

--------------------------------------------------

User:

Open report card

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "report_cards"
}

Only use:

navigation_target = null

when no destination can be determined.

Never return null when the user has
explicitly named a destination.
"""