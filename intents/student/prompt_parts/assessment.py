ASSESSMENT_PROMPT = """
assessment_summary

Use when the student is asking about school assessments, tests, quizzes or exams.

==================================================
MATCHES
==================================================

Classify as assessment_summary for queries about:

- assessment
- assessments
- test
- tests
- quiz
- quizzes
- exam
- exams
- marks
- score
- scores
- grades
- result
- results
- latest result
- latest assessment
- latest test
- assessment performance
- average marks
- highest score
- lowest score
- best assessment
- weakest assessment
- assessment feedback
- teacher feedback
- teacher comments
- upcoming assessments
- scheduled assessments
- next assessment
- next exam
- next test
- missed assessment
- absent assessment
- exam preparation

Examples:

- What marks did I get?
- Show my latest result.
- What was my best assessment?
- Which assessment did I score lowest in?
- Show assessment feedback.
- What exams are coming up?
- Do I have any tests this week?

==================================================
DO NOT MATCH
==================================================

Do NOT classify as assessment_summary for:

Atlas-related queries:

- Atlas score
- Atlas band
- Atlas rank
- Academic score
- Growth score
- Initiative score
- Academic pillar
- Growth pillar
- Initiative pillar
- Strongest pillar
- Weakest pillar

→ atlas_score_summary

Homework-related queries:

- homework
- assignment
- submission
- overdue homework
- pending homework

→ homework_summary

Navigation requests:

- Open assessments
- Take me to assessments
- Go to exams
- Open assessment screen

→ screen_navigation

==================================================
BUSINESS RULES
==================================================

Assessments are teacher-conducted evaluations.

Students do NOT submit assessments through Atlas.

Therefore assessments are never:

- pending
- overdue
- incomplete

Assessments may be:

- upcoming
- scheduled
- graded
- missed
- absent

==================================================
TARGET MODULES
==================================================

["assessment"]
"""