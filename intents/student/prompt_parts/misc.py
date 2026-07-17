CALENDAR_PROMPT = """
==================================================
CALENDAR SUMMARY
==================================================

Intent:

calendar_summary

Used when the student asks about:

- school calendar
- upcoming events
- holidays
- activities
- school functions
- celebrations
- competitions
- event schedule
- calendar events
- exams on the calendar

==================================================
SUPPORTED QUERIES
==================================================

General

- Show my calendar
- Show school calendar
- What is happening today?
- What is happening tomorrow?
- What is happening this week?
- What is happening next week?
- What's coming up?
- Show upcoming events
- Show calendar
- Any events?

Holiday

- Is tomorrow a holiday?
- Show holidays
- Show upcoming holidays
- Any holidays this week?
- Holidays this month
- When is the next holiday?

Exam Events

- Show upcoming exams
- Any exams this week?
- Next exam
- Exam calendar
- Show exam schedule

Activities

- Show activities
- Upcoming activities
- Any activities this week?
- School activities

Events

- Show events
- Upcoming events
- School functions
- Sports day
- Annual day
- Science exhibition
- Parent teacher meeting
- Cultural event

Keyword Search

- Show sports events
- Find Independence Day event
- Show transport events
- Search science events
- Find assembly
- Show Mathematics events

==================================================
DATE EXTRACTION
==================================================

Extract whenever present.

Examples

Today
Tomorrow
Yesterday
This week
Last week
Next week
This month
Last month
Next month
Monday
Next Friday
Between 1 June and 10 June

Populate

start_date
end_date

==================================================
TOPIC EXTRACTION
==================================================

Extract the event category or search keyword.

Examples

Show holidays

topic = "holiday"

--------------------------------

Upcoming exams

topic = "exam"

--------------------------------

School activities

topic = "activity"

--------------------------------

Show sports events

topic = "sports"

--------------------------------

Science exhibition

topic = "science"

--------------------------------

PTM

topic = "ptm"

--------------------------------

What's happening this week?

topic = null

==================================================
TARGET MODULES
==================================================

calendar_summary

[
    "calendar"
]
"""