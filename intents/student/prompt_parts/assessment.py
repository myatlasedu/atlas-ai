ASSESSMENT_PROMPT = """
--------------------------------------------------

assessment_summary

Used when the student asks about assessments,
tests, quizzes, exams, grades, marks,
results, performance, feedback,
teacher comments or upcoming assessments.

Examples:

- Show latest assessment
- What was my score?
- Recent tests
- Assessment results
- Upcoming assessments
- Any tests this week?
- What exams are coming up?
- What assessments are scheduled for me?
- Which assessment is next?

Results & Marks:

- What marks did I get?
- Show my grades
- What was my latest result?
- What was my latest assessment result?
- Show my latest test result
- How many marks did I score?
- What grade did I get?
- What was my best assessment?
- What was my weakest assessment?
- Which assessment did I score highest in?
- Which assessment did I score lowest in?

Performance:

- How am I performing in assessments?
- What is my average assessment score?
- Am I improving in assessments?
- Show assessment performance
- How many assessments have been graded?
- Summarize my assessment performance
- How am I doing in tests?

Feedback:

- Show assessment feedback
- Did my teacher leave feedback?
- Any teacher comments on my assessments?
- What feedback did I receive?
- Show recent assessment reviews
- Show teacher comments on my tests
- What did my teacher say about my assessment?

Missed:

- Which assessment did I miss?

==================================================
ASSESSMENT INTERPRETATION RULES
==================================================

Questions about:

- test
- tests
- quiz
- quizzes
- exam
- exams
- assessment
- assessments
- marks
- grades
- assessment result
- assessment results
- assessment performance
- assessment feedback
- teacher comments
- teacher feedback
- graded assessments
- latest assessment
- latest result
- best assessment
- weakest assessment
- highest assessment score
- lowest assessment score
- upcoming assessment
- upcoming test
- upcoming exam
- scheduled assessment
- next assessment
- exam preparation

must be classified as:

assessment_summary

==================================================
DO NOT CLASSIFY AS ASSESSMENT
==================================================

The following belong to Atlas:

- atlas score
- academic score
- growth score
- initiative score
- atlas band
- atlas rank
- academic pillar
- growth pillar
- initiative pillar
- strongest pillar
- weakest pillar
- overall performance
- performance pillars

These MUST be classified as:

atlas_score_summary

NOT:

assessment_summary

==================================================
DISAMBIGUATION RULES
==================================================

"What score did I get?"

→ assessment_summary

"What marks did I get?"

→ assessment_summary

"What grade did I get?"

→ assessment_summary

"How is my academic score?"

→ atlas_score_summary

"What is my growth score?"

→ atlas_score_summary

"What is my initiative score?"

→ atlas_score_summary

"What is my Atlas score?"

→ atlas_score_summary

"What is my strongest pillar?"

→ atlas_score_summary

"What is my weakest pillar?"

→ atlas_score_summary

==================================================
TARGET MODULES
==================================================

assessment_summary

[
    "assessment"
]

==================================================
ASSESSMENT BUSINESS RULES
==================================================

Assessments are school-conducted exams,
tests, quizzes or evaluations.

Assessments are NOT homework.

Students do NOT submit assessments
through Atlas AI.

Therefore:

- assessments are never pending
- assessments are never overdue
- assessments are never incomplete

An assessment may be:

- upcoming
- scheduled
- graded
- missed
- absent

When discussing future assessments,
always refer to them as:

- upcoming assessments
- scheduled assessments
- upcoming exams
- upcoming tests

Never describe them as:

- pending assessments
- overdue assessments
- incomplete assessments

Preparation is the expected action,
not submission.

==================================================
ASSESSMENT SUMMARIZATION RULES
==================================================

When summarizing assessment data,
prioritize information in the following order:

1. Risk assessments
2. Performance trend
3. Lowest-performing assessment
4. Upcoming assessments
5. Highest-performing assessment
6. Historical achievements

If a declining trend exists:

- Make the declining trend the primary message.
- Do NOT begin the summary with positive achievements.
- Explain that recent performance needs attention.
- Mention previous strong performance only as supporting context.

If one or more risk assessments exist:

- Explicitly mention the assessment(s) requiring attention.
- Mention the score if available.
- Recommend focusing on improving those assessments.

If upcoming assessments exist:

- Encourage preparation for the upcoming assessments.
- Do NOT say they need to be completed or submitted.

A historical high score must NEVER outweigh a recent decline.

For example:

GOOD:

"Recent assessment performance shows a declining trend despite previous strong results."

BAD:

"Your child has performed well..."

when:

- trend.direction == "declining"
- OR risk assessments exist.

If both strengths and concerns exist:

Acknowledge strengths,
but emphasize current concerns first.

==================================================
NAVIGATION RULES
==================================================

If the student wants to open
the assessment screen:

Examples:

- open assessment
- open assessments
- take me to assessments
- show assessment page
- go to exams
- open exam screen

Classify as:

screen_navigation

NOT:

assessment_summary
"""