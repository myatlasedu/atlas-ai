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
"""