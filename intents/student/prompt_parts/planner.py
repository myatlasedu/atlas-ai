PLANNER_PROMPT = """
==================================================
PLANNER CREATE
==================================================

Intent:
planner_create

The student wants to add an entry to their planner.

Creating a planner entry ALWAYS requires confirmation.

Examples

- Create planner revise chemistry chapter 3 tomorrow
- Write planner finish the maths worksheet
- Add to my planner: football practice on Friday
- Write a planner for 5 October submit science project

Extract

description

The text to save. Remove ONLY the planner command
("create planner", "write planner", "add to my planner",
"write a planner for") and the words that only say WHEN
("tomorrow", "on Friday", "for 5 October").
Keep the student's own wording for everything else.
If nothing remains, description = null.

tag

Exactly one of:

- "Academic"  study, homework, exams, school work
- "Personal"  hobbies, family, health, friends
- "Task"      a to-do or chore to get done
- "Note"      anything else

When unsure, tag = "Note".

start_date / end_date

The planner date, when the query mentions one.
Set both to that same date. Otherwise null.

Return

{
    "intent": "planner_create",
    "description": "revise chemistry chapter 3",
    "tag": "Academic",
    "navigation_target": null,
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [
        "planner"
    ],
    "confidence": 0.95
}

==================================================
PLANNER SUMMARY
==================================================

Intent:
planner_summary

The student wants to read their planner entries.

Examples

- Show my planner
- What is in my planner today?
- My planner this week
- Show planner about chemistry

Extract

topic

The keyword being searched for, if any ("chemistry").
Never include the word "planner". Otherwise null.

start_date / end_date

Extract dates whenever present. Otherwise null.

description = null
tag = null

Return

{
    "intent": "planner_summary",
    "description": null,
    "tag": null,
    "navigation_target": null,
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [
        "planner"
    ],
    "confidence": 0.95
}
"""
