SCREEN_NAVIGATION_PROMPT = """
--------------------------------------------------

screen_navigation

Used when the student wants to navigate
to a screen inside the application.

==================================================
SUPPORTED NAVIGATION TARGETS
==================================================

- profile
- daily_summary
- atlas_score
- homework
- attendance
- planner
- forum
- events
- classroom
- timetable
- enrichment
- announcements
- mindfullness
- healthroom
- notifications
- resources
- assessments

==================================================
EXAMPLES
==================================================

Open homework

→ navigation_target = homework

Take me to homework

→ navigation_target = homework

Open assignments

→ navigation_target = homework

open resources

→ navigation_target = resources

Take me to resources

→ navigation_target = resources

Show my resources

→ navigation_target = resources

Show attendance page

→ navigation_target = attendance

Take me to attendance

→ navigation_target = attendance

Open journal

→ navigation_target = planner

Take me to journal

→ navigation_target = planner

Open planner

→ navigation_target = planner

Take me to my planner

→ navigation_target = planner

Take me to planner

→ navigation_target = planner

Take to me planner

→ navigation_target = planner

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

Open timetable

→ navigation_target = timetable

Show my timetable

→ navigation_target = timetable

Open Structure of the Day

→ navigation_target = timetable

Show my Structure of the Day

→ navigation_target = timetable

Open today's Structure of the Day

→ navigation_target = timetable

Take me to Structure of the Day

→ navigation_target = timetable

Open SOD

→ navigation_target = timetable

Show my SOD

→ navigation_target = timetable

Take me to SOD

→ navigation_target = timetable

Open lesson schedule

→ navigation_target = timetable

Show today's lessons

→ navigation_target = timetable

Open my lessons

→ navigation_target = timetable

Show my schedule

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

→ navigation_target = mindfullness

Take me to wellbeing

→ navigation_target = mindfullness

Open mindfullness

→ navigation_target = mindfullness

Take me to mindfullness

→ navigation_target = mindfullness

Open health room

→ navigation_target = healthroom

Open profile

→ navigation_target = profile

Show my profile

→ navigation_target = profile

Open assessment

→ navigation_target = assessments

Take me to assessments

→ navigation_target = assessments

Open exams

→ navigation_target = assessments

Show assessments screen

→ navigation_target = assessments

Take me to daily summary

→ navigation_target = daily_summary

Open my daily summary

→ navigation_target = daily_summary

Show my daily summary

→ navigation_target = daily_summary

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

Open Structure of the Day

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "timetable"
}

--------------------------------------------------

User:

Open SOD

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "timetable"
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
    "navigation_target": "assessments"
}

--------------------------------------------------

Only use:

navigation_target = null

when no destination can be determined.

Never return null when the user has
explicitly named a destination.
"""