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

==================================================
SUBJECT FILTER
==================================================

When the student names a SUBJECT to scope the homework
question, set "subject" to the subject name exactly as
the student wrote it.

Keep the full name (e.g. "Global Perspectives", not
"global" or "perspectives").

Leave "subject" as null when no subject is named.

Examples:

Query: show all my submitted Math homework
subject: "Math"

Query: which Science homework is pending?
subject: "Science"

Query: what homework is pending?
subject: null

Setting "subject" must not change "topic" or
"asks_for_marks": those stay null / false unless a
specific titled homework's marks are named.

Examples:

Query: show all my submitted Math homework with marks
and feedback
subject: "Math"
topic: null
asks_for_marks: false

Query: what did I get on 'workbook - 29 july'?
subject: null
topic: "workbook - 29 july"
asks_for_marks: true

==================================================
ASKS_FOR_MARKS FLAG
==================================================

Set "asks_for_marks" to true ONLY when the student names a
SPECIFIC homework / assignment / worksheet / submission AND
asks for its MARKS / GRADE / SCORE / RESULT.

This flag works together with "topic": set BOTH when a specific
titled homework's marks are requested.

- If the student asks about marks for a specific titled homework:
  asks_for_marks: true, topic = full homework name.

- If NO specific homework is named (e.g. "what marks did I get
  in homework" without a title), set asks_for_marks: false.

- If the student asks about homework status, deadlines, pending,
  overdue or feedback WITHOUT asking for a specific titled
  homework's marks, set asks_for_marks: false.

Examples:

Query: what did I get on the worksheet from 1st August
asks_for_marks: true
topic: "worksheet from 1st August"

Query: what marks did I get in homework
asks_for_marks: false
topic: null

Query: what homework is pending?
asks_for_marks: false
topic: null
"""