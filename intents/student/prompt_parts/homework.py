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

When the student names a SPECIFIC homework and asks about it
(marks, status, submission, due date or details),
set "topic" to the FULL homework name EXACTLY as the student wrote it.

- Keep the date EXACTLY as given (e.g. "29 july", "1st August", "28 july").
- Never drop or shorten the date.
- Never shorten or reword the name.
- Never substitute a similar or "closest" homework.
- NEVER leave "topic" null when the student's words contain a
  homework name — even if the name looks misspelled, unusual
  or unknown to you. Copy it letter-for-letter; Atlas will
  match it against real homework titles itself.
- If no specific homework is named, leave "topic" as null.

Examples:

Query: marks for homework 'homework worksheet - 29 july'
topic: "homework worksheet - 29 july"    (NOT "homework worksheet")

Query: what did I get on the worksheet from 1st August
topic: "worksheet from 1st August"

Query: show marks for homework-worksheet28july
topic: "homework-worksheet28july"

Query: tell me about my homework son muy famossos
topic: "son muy famossos"    (copy even MISSPELLED names exactly)

Query: what marks did I get in homework
topic: null

==================================================
HOMEWORK FOCUS - WHAT EXACTLY WAS ASKED
==================================================

Every homework question must also set "homework_focus"
to EXACTLY ONE of these values:

topic_status | pending | overdue | due_today |
due_tomorrow | submitted | graded | feedback |
due_range | next_up | general

Rules:

- A SPECIFIC homework is named (its status, marks,
  submission or details are asked) -> "topic_status".
  Also set "topic" to the full name.
- pending / not submitted / haven't handed in /
  need to finish / still to do -> "pending".
- overdue / late / missed deadlines / missed
  submissions -> "overdue".
- due today -> "due_today".  due tomorrow -> "due_tomorrow".
- submitted / handed in / turned in / did I submit X /
  when did I submit X / what did I submit on DATE
  -> "submitted" (fill start_date = end_date = that date).
- graded / marked / scores so far / my results list
  -> "graded".
- teacher feedback / remarks / notes from teacher
  -> "feedback".
- A DUE-DATE period is mentioned ("this week",
  "last month", "on 31 July", "between X and Y")
  -> "due_range" and fill start_date / end_date.
  For "this week": start_date MUST be the MONDAY of
  the current week and end_date its SUNDAY, using
  today's year.
- what's due first / next deadline / what should I do
  first -> "next_up".
- General overview ("show my homework", "homework
  summary", "how is my homework going") -> "general".

Examples:

Query: what haven't I handed in yet?
homework_focus: "pending"

Query: did I miss any deadlines?
homework_focus: "overdue"

Query: show my graded homework
homework_focus: "graded"

Query: what homework was due on 31 July?
homework_focus: "due_range", start_date = 2026-07-31,
end_date = 2026-07-31

Query: show my homework for this week
homework_focus: "due_range", Monday to Sunday dates

Query: tell me about Elements of Art
homework_focus: "topic_status", topic: "Elements of Art"

Choose a narrow focus ONLY when the user explicitly
named that category; otherwise use "general".
"""