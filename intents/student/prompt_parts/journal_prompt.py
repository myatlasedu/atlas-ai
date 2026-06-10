JOURNAL_PROMPT = """
==================================================
JOURNAL SUMMARY
==================================================

Intent:
journal_summary

Used when the student wants to view,
read, review or search their personal journal.

The journal is private and belongs only
to the student.

Examples:

User:
show my journal

Return:

{
    "intent": "journal_summary",
    "start_date": null,
    "end_date": null,
    "target_modules": ["journal"],
    "confidence": 0.95
}

User:
show recent journal entries

Return:

{
    "intent": "journal_summary",
    "start_date": null,
    "end_date": null,
    "target_modules": ["journal"],
    "confidence": 0.95
}

==================================================
JOURNAL CREATE
==================================================

Intent:
journal_create

Used when the student wants to save
a thought, reflection, memory, note,
learning or personal journal entry.

Creating a journal entry requires confirmation.

Examples:

User:
Today I learned quadratic equations.
Save this in my journal.

Return:

{
    "intent": "journal_create",
    "start_date": null,
    "end_date": null,
    "target_modules": ["journal"],
    "confidence": 0.95
}

User:
Journal this:
I finally understood trigonometry today.

Return:

{
    "intent": "journal_create",
    "start_date": null,
    "end_date": null,
    "target_modules": ["journal"],
    "confidence": 0.95
}

User:
Add this to my journal:
I need to revise chemistry this weekend.

Return:

{
    "intent": "journal_create",
    "start_date": null,
    "end_date": null,
    "target_modules": ["journal"],
    "confidence": 0.95
}

IMPORTANT:

Always return:

- intent
- start_date
- end_date
- target_modules
- confidence

Never omit any field.
"""