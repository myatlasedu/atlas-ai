PERSONAL_EVENT_PROMPT = """
==================================================

personal_event_summary

Used ONLY when the student asks about THEIR OWN
personal schedule, reminders, appointments,
study sessions, or personal events that they
have created.

This intent is ONLY for user-created events.

DO NOT use this intent for:

- school events
- school calendar
- school holidays
- school activities
- school functions
- school announcements
- sports day
- annual day
- PTM
- school examinations
- cultural events
- competitions
- anything organised by the school

Those belong to:

calendar_summary

==================================================

Used when the student asks about:

- my reminders
- my reminder
- my schedule
- my calendar
- my personal calendar
- my appointments
- my study sessions
- my revision sessions
- my personal events
- my plans
- what have I planned
- what do I have planned
- what have I scheduled
- my tasks
- my to-do

Examples:

- What reminders do I have?
- Show my reminders.
- Show my calendar.
- Show my schedule.
- What have I planned today?
- What do I have tomorrow?
- What appointments do I have?
- Show my study sessions.
- Show my revision sessions.
- Do I have anything planned?
- What personal events do I have?
- What have I scheduled for Friday?

==================================================

personal_event_create

Used when the student wants to create a personal
reminder, study session, appointment or event.

Examples:

- Remind me to study maths tomorrow.
- Create a revision session for Friday.
- Add a football practice event.
- Set a reminder for my chemistry exam.
- Remind me to submit my homework.
- Schedule a study session tonight.
- Create a personal reminder.
- Add a personal appointment.

IMPORTANT

Never create immediately.

Always classify as:

personal_event_create

Event creation requires confirmation.
"""