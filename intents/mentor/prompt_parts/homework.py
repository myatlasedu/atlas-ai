HOMEWORK_PROMPT = """
==================================================
INTENT
==================================================

The intent has ALREADY been classified.

You MUST return:

"intent": "homework_summary"

Never change the intent.

Your ONLY job is to determine:

- view
- dates
- grade
- section
- subject

==================================================
VIEWS
==================================================

summary

General homework overview.

Examples:

- Homework summary
- Homework report
- Homework overview
- Show homework
- Homework this week
- Homework this month

--------------------------------------------------

pending_homework

Homework with pending student submissions.

Examples:

- Show pending homework
- Pending homework
- Homework awaiting submission
- Homework not completed
- Which assignments are incomplete?

--------------------------------------------------

overdue_homework

Homework whose due date has passed and submissions are still pending.

Examples:

- Overdue homework
- Show overdue homework
- Homework past due date
- Missed homework

--------------------------------------------------

due_today

Homework due today.

Examples:

- Homework due today
- What is due today?
- Assignments due today

--------------------------------------------------

submitted_homework

Homework already submitted.

Examples:

- Submitted homework
- Show submitted homework
- Homework submissions

--------------------------------------------------

not_submitted_homework

Students who have not submitted homework.

Examples:

- Who has not submitted homework?
- Show pending submissions
- Missing homework submissions
- Students with pending homework
- Which students haven't submitted?
- Homework not submitted

--------------------------------------------------

awaiting_review

Homework submissions that have been submitted by students
but have not yet been reviewed or graded.

Examples:

- Show homework awaiting review
- Homework awaiting review
- Pending grading
- Which homework needs review?
- Show submissions to review
- Show unreviewed homework
- Which homework should I grade?
- Show homework awaiting grading

--------------------------------------------------

homework_feedback

Homework submissions that have already been reviewed by the teacher.

Examples:

- Show teacher feedback
- Show homework feedback
- Homework reviews
- Reviewed homework
- Which homework has been graded?
- Show graded submissions
- Feedback this week
- Teacher comments

--------------------------------------------------

due_today

Homework due today.

Examples:

- Homework due today
- What is due today?
- Assignments due today
- Which homework is due today?
- Show today's homework

==================================================
OUTPUT RULES
==================================================

Always return:

{
    "intent": "homework_summary",
    "start_date": null,
    "end_date": null,
    "academic_year": null,
    "grade": null,
    "section": null,
    "subject": null,
    "enrichment": null,
    "view": "...",
    "target_modules": ["homework"],
    "confidence": 0.95
}
"""