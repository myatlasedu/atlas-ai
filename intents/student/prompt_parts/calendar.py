CALENDAR_PROMPT = """
--------------------------------------------------

calendar_summary

Used when the student asks about:

- school calendar
- school events
- holidays
- upcoming holidays
- upcoming events
- school activities
- competitions
- celebrations
- functions
- PTM
- annual day
- sports day
- science exhibition
- cultural events
- event schedule
- exam schedule
- campus events

IMPORTANT

This intent is ONLY for school-wide events.

Do NOT use this intent for:

- personal reminders
- personal schedule
- personal appointments
- study sessions
- revision sessions
- user-created events

Those belong to:

personal_event_summary

==================================================

Examples:

General

- Show school calendar
- What is happening today?
- What is happening tomorrow?
- What is happening this week?
- What's happening next week?
- Show upcoming events
- Any school events?
- What is coming up?

Holidays

- Is tomorrow a holiday?
- Show holidays
- Upcoming holidays
- Holidays this month
- Next holiday
- Any holidays next week?

School Events

- Sports day
- Annual day
- Any competitions?
- Any cultural events?
- Science exhibition
- Parent teacher meeting
- School function
- Assembly schedule

Exams

- Upcoming exams
- Exam schedule
- Next exam
- Exams this week

Activities

- School activities
- Upcoming activities
- Activities this month

Keyword Search

- Show sports events
- Find Independence Day celebration
- Search science exhibition
- Show transport awareness event
- Mathematics event

==================================================

TARGET MODULES

calendar_summary

[
    "calendar"
]
"""