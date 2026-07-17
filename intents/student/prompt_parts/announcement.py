ANNOUNCEMENT_PROMPT = """
==================================================
ANNOUNCEMENT SUMMARY
==================================================

Intent:
announcement_summary

Used when the student wants to:

- view announcements
- read announcements
- search announcements
- school notices
- class notices
- latest announcements
- recent announcements
- announcement history
- announcements by date
- announcements by subject
- announcements by keyword

==================================================
SUPPORTED QUERIES
==================================================

General

- Show announcements
- Show recent announcements
- Show all announcements
- Latest announcements
- Any announcements?
- Any updates?
- What's new?
- Show school notices
- Show class notices

Latest

- Latest announcement
- Most recent announcement
- New announcement
- Last announcement

Oldest

- First announcement
- Oldest announcement
- Earliest announcement

Date Filters

- Today's announcements
- Yesterday's announcements
- Announcements this week
- Announcements last week
- Announcements this month
- Announcements from Monday
- Announcements between 1 June and 10 June

Keyword Search

- Announcements about exams
- Show announcements about sports
- Search announcements for transport
- Find announcements about fees
- Show notices about Mathematics
- Show announcements mentioning holiday

==================================================
RETURN
==================================================

{
    "intent": "announcement_summary",
    "start_date": null,
    "end_date": null,
    "subject": null,
    "topic": null,
    "target_modules": [
        "announcement"
    ],
    "confidence": 0.95
}

==================================================
DATE EXTRACTION
==================================================

Extract whenever present.

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

==================================================
KEYWORD EXTRACTION
==================================================

If the student searches announcements about something,
extract it into:

topic

Examples

Announcements about exams

topic = "exam"

Announcements about sports

topic = "sports"

Search announcements for transport

topic = "transport"

Show notices about Mathematics

topic = "mathematics"

If no keyword is present

topic = null

==================================================
TOPIC EXTRACTION RULES
==================================================

Extract only the search keyword.

Do NOT include

- announcement
- announcements
- notice
- notices
- show
- search
- find
- about
- regarding
- related to

Examples

Show announcements about exams

topic = "exam"

-------------------------

Search announcements for sports

topic = "sports"

-------------------------

Announcements this week

topic = null

==================================================
TARGET MODULES
==================================================

announcement_summary

[
    "announcement"
]
"""