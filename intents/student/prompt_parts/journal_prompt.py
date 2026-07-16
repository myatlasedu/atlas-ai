JOURNAL_PROMPT = """
==================================================
JOURNAL SUMMARY
==================================================

Intent:
journal_summary

Used when the student wants to:

- read journal entries
- view journal entries
- search journal entries
- review journal history
- summarize journals
- find journals by date
- find journals by topic or keyword

The journal is private and belongs only to the student.

==================================================
SUPPORTED QUERIES
==================================================

General

- Show my journal
- Show my journals
- My journal
- Journal summary
- Journal overview
- Show recent journal entries
- Read my journal
- Review my journal
- Summarize my journal

Date Filters

- Today's journal
- Yesterday's journal
- My journal this week
- My journal last week
- My journal this month
- Show journals from Monday
- Show journals from last Friday
- Show journals between 1 June and 10 June
- Show my latest journal
- Show my first journal entry

Topic Search

- Show my journal about Maths
- Show journal about exams
- Show journal about football
- Show journal mentioning chemistry
- Search my journal for algebra
- Find journal about revision
- What did I write about calculus?
- Show journals about exams from June
- Show my maths journal this week

==================================================
RETURN
==================================================

Always return

{
    "intent": "journal_summary",
    "navigation_target": null,
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [
        "journal"
    ],
    "confidence": 0.95
}

==================================================
JOURNAL CREATE
==================================================

Intent:
journal_create

Used when the student wants to save:

- thoughts
- reflections
- memories
- study notes
- learning experiences
- achievements
- reminders
- personal observations

Creating a journal entry ALWAYS requires confirmation.

Examples

- Save this in my journal.
- Journal this.
- Add this to my journal.
- Create a journal entry.
- Remember this in my journal.
- Save today's reflection.
- Log this in my journal.

Return

{
    "intent": "journal_create",
    "navigation_target": null,
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [
        "journal"
    ],
    "confidence": 0.95
}

==================================================
JOURNAL NAVIGATION
==================================================

When the student wants to open the journal page.

Examples

- Open journal
- Open my journal
- Go to journal
- Take me to journal
- Open journal screen
- Open journal page

Return

{
    "intent": "screen_navigation",
    "navigation_target": "journal",
    "subject": null,
    "topic": null,
    "start_date": null,
    "end_date": null,
    "target_modules": [],
    "confidence": 0.99
}

==================================================
DISAMBIGUATION RULES
==================================================

Reading

- show my journal
- read my journal
- recent journal
- journal history
- journal summary
- journal overview
- today's journal
- yesterday's journal
- this week's journal
- journal about maths
- search journal

→ journal_summary

Creating

- save this in my journal
- journal this
- add this to my journal
- create journal entry
- log this
- save today's reflection
- remember this

→ journal_create

Navigation

- open journal
- go to journal
- open journal page
- open journal screen

→ screen_navigation

==================================================
EXTRACTION RULES
==================================================

Extract these fields whenever possible.

subject

- Only populate if the query explicitly mentions a school subject.

Examples

Maths
English
Science
Chemistry
Physics
Biology
History

Otherwise

subject = null

--------------------------------------------------

topic

Extract the thing the student is searching for.

Examples

Show my maths journal

topic = "maths"

--------------------------------

Search journal for football

topic = "football"

--------------------------------

Find journal about exams

topic = "exam"

--------------------------------

What did I write about calculus?

topic = "calculus"

--------------------------------

Show journals from last week

topic = null

Do NOT include words such as

- journal
- journals
- entry
- entries
- show
- find
- search
- about
- regarding
- related to
- for

Return only the actual search topic.

--------------------------------------------------

Dates

Extract dates whenever present.

Examples

Today
Yesterday
This week
Last week
This month
Last month
Monday
Last Friday
Between 1 June and 10 June

Populate

start_date

end_date

Otherwise return

start_date = null

end_date = null

==================================================
TARGET MODULES
==================================================

journal_summary

[
    "journal"
]
"""