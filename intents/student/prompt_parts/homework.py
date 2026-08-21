HOMEWORK_PROMPT = """
--------------------------------------------------

homework_summary

Used when the student asks about homework,
assignments, submissions, deadlines,
teacher feedback or homework progress.

Examples:

- What homework is pending?
- Show my homework
- Any overdue assignments?
- Homework status
- What is due tomorrow?
- What is due today?
- What homework do I need to complete?
- How many homework assignments are pending?
- Which homework should I prioritize?
- Show teacher feedback
- Did my teacher leave feedback?
- Show recent homework reviews
- What assignments are overdue?
- Which homework has the closest deadline?
- What homework have I not submitted?
- What homework is pending this week?
- What homework is due this week?
- Show pending homework
- Show overdue homework
- Any homework due today?
- Any homework due tomorrow?
- Which homework needs immediate attention?
- What feedback did I receive on my homework?
- Show homework feedback
- Show my latest homework submission
- What homework was recently reviewed?
- Which homework has been graded?
- What marks did I get in homework?

==================================================
HOMEWORK INTERPRETATION RULES
==================================================

Questions about:

- homework
- assignment
- assignments
- submission
- submissions
- due date
- deadline
- pending work
- overdue work
- teacher feedback
- homework feedback
- homework review
- homework marks
- homework grades

must be classified as:

homework_summary

==================================================
SPECIFIC HOMEWORK MARKS - STRICT TITLE EXTRACTION
==================================================

When the student names a SPECIFIC homework and asks for its marks,
set "topic" to the FULL homework name EXACTLY as the student wrote it.

- Keep the date EXACTLY as given (e.g. "29 july", "1st August", "28 july").
- Never drop or shorten the date.
- Never shorten or reword the name.
- Never substitute a similar or "closest" homework.
- If no specific homework is named, leave "topic" as null.

Examples:

Query: marks for homework 'homework worksheet - 29 july'
topic: "homework worksheet - 29 july"    (NOT "homework worksheet")

Query: what did I get on the worksheet from 1st August
topic: "worksheet from 1st August"

Query: show marks for homework-worksheet28july
topic: "homework-worksheet28july"

Query: what marks did I get in homework
topic: null
"""