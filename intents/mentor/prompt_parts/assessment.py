ASSESSMENT_PROMPT = """
--------------------------------------------------

assessment_summary

Examples:

- Assessment summary
- Show assessment summary
- Assessment report
- Assessment statistics
- Assessment dashboard

View:

summary

--------------------------------------------------

pending_grading

Examples:

- Show pending grading
- Pending grading
- Assessments awaiting grading
- Show ungraded assessments
- Which assessments need grading?
- What should I grade today?

View:

pending_grading

--------------------------------------------------

upcoming_assessments

Examples:

- Upcoming assessments
- Upcoming tests
- Upcoming exams
- Upcoming quizzes
- Assessments this week
- Tests tomorrow
- Exams next week
- What assessments are scheduled?

View:

upcoming_assessments

--------------------------------------------------

graded_assessments

Examples:

- Show graded assessments
- Recently graded assessments
- Completed grading
- Assessment results

View:

graded_assessments

--------------------------------------------------

low_scores

Examples:

- Who scored below 40?
- Lowest marks
- Weak performers
- Students needing improvement

View:

low_scores

--------------------------------------------------

top_performers

Examples:

- Top performers
- Highest marks
- Students scoring above 90
- Class toppers

View:

top_performers

--------------------------------------------------

assessment_feedback

Examples:

- Show assessment feedback
- Teacher comments
- Assessment remarks
- Feedback on assessments

View:

assessment_feedback

--------------------------------------------------

subject_statistics

Examples:

- Subject statistics
- Maths assessment performance
- Science assessment report
- Assessment analytics

View:

subject_statistics

==================================================
ASSESSMENT INTERPRETATION RULES
==================================================

Questions about:

- assessment
- assessments
- quiz
- test
- exam
- grading
- assessment results
- assessment feedback
- teacher comments
- low scores
- top performers
- subject performance
- assessment analytics

must be classified as:

assessment_summary

==================================================
RETURN FORMAT
==================================================

Always return:

{
    "intent": "assessment_summary",
    "view": "<selected_view>",
    "target_modules": ["assessment"]
}
"""