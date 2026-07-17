TIMETABLE_PROMPT = """
--------------------------------------------------

timetable_summary

Questions about the student's Structure of the Day.

Atlas AI follows Cambridge terminology.

Understand BOTH Cambridge terminology and common school terminology.

==================================================
UNDERSTAND ALL OF THE FOLLOWING
==================================================

Cambridge terminology

- Structure of the Day
- SOD
- Today's Structure of the Day
- Tomorrow's Structure of the Day
- Weekly Structure of the Day
- Lesson
- Lessons
- Current Lesson
- Next Lesson
- Free Lesson

Common terminology

- timetable
- class timetable
- school timetable
- daily timetable
- weekly timetable
- schedule
- class schedule
- lesson schedule
- today's classes
- tomorrow's classes
- current class
- next class
- period
- periods
- class period
- teaching period
- free period

==================================================
USE THIS INTENT WHEN THE USER ASKS ABOUT
==================================================

- today's Structure of the Day
- tomorrow's Structure of the Day
- this week's Structure of the Day
- lesson timings
- lesson order
- current lesson
- next lesson
- first lesson
- last lesson
- free lessons
- today's classes
- tomorrow's classes
- today's timetable
- tomorrow's timetable
- class schedule

==================================================
DO NOT USE THIS INTENT FOR
==================================================

Personal reminders

Personal appointments

Personal calendar events

School events

Holidays

Announcements

Homework

Attendance

Assessments

Those belong to their respective intents.

==================================================
EXAMPLES
==================================================

Structure of the Day

→ timetable_summary

SOD

→ timetable_summary

Show my Structure of the Day

→ timetable_summary

Open today's Structure of the Day

→ timetable_summary

What is my Structure of the Day today?

→ timetable_summary

What is my Structure of the Day tomorrow?

→ timetable_summary

Show today's lessons

→ timetable_summary

Show tomorrow's lessons

→ timetable_summary

What lesson do I have now?

→ timetable_summary

What is my next lesson?

→ timetable_summary

Do I have a free lesson?

→ timetable_summary

Show my timetable

→ timetable_summary

Show tomorrow's timetable

→ timetable_summary

Show today's schedule

→ timetable_summary

What period do I have now?

→ timetable_summary

What is my next period?

→ timetable_summary

Do I have a free period?

→ timetable_summary

==================================================
OUTPUT RULES
==================================================

Intent

timetable_summary

Target Modules

[
    "timetable"
]

IMPORTANT

The AI should understand both Cambridge and common school terminology.

Users may say:

- timetable
- schedule
- period
- periods

These MUST still classify as:

timetable_summary

Internally the backend may use "timetable", but Atlas AI should always use Cambridge terminology when responding:

- Structure of the Day
- Lesson
- Lessons
- Current Lesson
- Next Lesson

Never classify requests about Structure of the Day or SOD as calendar events or personal events.
"""