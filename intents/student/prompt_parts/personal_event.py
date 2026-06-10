PERSONAL_EVENT_PROMPT = """
--------------------------------------------------

personal_event_summary

Used when the student asks about:

- calendar
- schedule
- events
- reminders
- upcoming events
- personal events
- upcoming events
- appointments
- study sessions
- activities

Examples:

- events tomorrow
- upcoming events
- what events do i have
- show my calendar
- show my schedule
- what is scheduled today
- what reminders do i have
- show upcoming events
- do i have anything planned
- what study sessions are scheduled

==================================================

personal_event_create

Used when the student wants to create:

- reminder
- study session
- personal event
- exam reminder
- activity

Examples:

- Remind me to study maths tomorrow.
- Create a revision session for Friday.
- Add a football practice event.
- Set a reminder for my chemistry exam.

IMPORTANT:

Never create immediately.

Always classify as:

personal_event_create

Event creation requires confirmation.
"""