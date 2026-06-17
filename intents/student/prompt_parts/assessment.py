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
- upcoming assessment
- scheduled assessment
- next assessment
- upcoming exam
- upcoming test
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

Assessments are not homework.

Students do not submit assessments
through Atlas AI.

Therefore:

- assessments cannot be pending
- assessments cannot be overdue
- assessments cannot be incomplete

An assessment may be:

- upcoming
- scheduled
- graded
- missed
- absent

Questions about preparing for an exam,
upcoming tests or scheduled assessments
must be classified as:

assessment_summary

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