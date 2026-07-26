CALENDAR_PROMPT = """
--------------------------------------------------

calendar_summary

Used when the student asks about:

- school calendar
- school events
- holidays
- upcoming holidays
- upcoming events
- School activities
- Upcoming activities
- Activities this month
- Next activity
- When's my next activity?
- Do I have any activities today?
- Are there any activities this week?
- What activities are coming up?
- Upcoming competitions
- Upcoming exhibitions
- Upcoming celebrations
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

This intent is for school-wide calendar items, including:

- holidays
- exams
- school activities
- school events
- competitions
- annual day
- sports day
- assemblies
- exhibitions
- celebrations
- PTM
- functions
- cultural programmes

If the user asks about:

- next activity
- upcoming activity
- activities this week
- activities this month
- school activities

ALWAYS use calendar_summary.

Do NOT interpret "activity" as a timetable period or Structure of the Day unless the user explicitly asks about today's timetable, today's schedule, today's classes, or the Structure of the Day.

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

Examples

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

TOPIC

Use the topic field to represent either:

1. A calendar category.
2. A free-text event search.

For calendar categories return EXACTLY one of:

holiday
exam
activity
event

Examples

"When is my next holiday?"

topic = "holiday"

"Upcoming holidays"

topic = "holiday"

"Exam schedule"

topic = "exam"

"Next exam"

topic = "exam"

"School activities"

topic = "activity"

"What activities are happening this week?"

topic = "activity"

"Upcoming events"

topic = "event"

"School events"

topic = "event"

"What is happening this week?"

topic = null

==================================================

FREE TEXT SEARCH

If the user is searching for a specific event by name, return that text in topic.

Examples

"Independence Day"

topic = "Independence Day"

"Transport Awareness"

topic = "Transport Awareness"

"Science Exhibition"

topic = "Science Exhibition"

"Annual Day"

topic = "Annual Day"

==================================================

PRIORITY

When the word "activity" is ambiguous:

Use calendar_summary if the user is asking about:

- next activity
- upcoming activity
- future activity
- activities this week
- activities this month
- school activity
- competitions
- events
- celebrations

Use timetable_summary ONLY when the user is asking about:

- today's timetable
- today's classes
- next class
- current lesson
- current period
- Structure of the Day
- class schedule

Examples

"When's my next activity?"

calendar_summary

"What activities are happening this month?"

calendar_summary

"What activity do I have in Period 4?"

timetable_summary

"What is my next class?"

timetable_summary

"Show today's timetable."

timetable_summary

==================================================


OUTPUT

Return

{
    "intent":"calendar_summary",
    "topic":"holiday|exam|activity|event|<search text>|null",
    "start_date":null,
    "end_date":null,
    "target_modules":["calendar"]
}
"""