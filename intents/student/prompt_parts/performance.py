PERFORMANCE_PROMPT = """
==================================================
STUDENT PERFORMANCE
==================================================

Intent:
student_performance

Use this intent ONLY when the user is asking for a
holistic or cross-module analysis of their learning.

Student Performance combines information from multiple
academic modules to produce an overall evaluation.

==================================================
USE ONLY FOR CROSS-MODULE ANALYSIS
==================================================

Choose student_performance only when the answer requires
combining two or more of the following modules:

- attendance
- homework
- assessments
- subjects
- atlas

Typical examples:

- How am I doing overall?
- Give me a performance review.
- Review my academic performance.
- Summarize my progress.
- What are my biggest strengths?
- What are my biggest weaknesses?
- What should I improve?
- What should I focus on?
- Am I at academic risk?
- How prepared am I overall?
- How can I become a better student?
- Give me recommendations.
- Analyze my overall performance.
- What areas need the most attention?
- What is preventing me from improving?
- Where should I spend more time studying?

==================================================
USED FOR
==================================================

This intent is appropriate for:

- overall performance
- holistic performance
- performance review
- performance analysis
- academic strengths
- academic weaknesses
- improvement advice
- study recommendations
- academic risks
- readiness
- overall progress
- focus areas
- learning habits
- recommendations
- overall summary

==================================================
CLASSIFICATION RULES
==================================================

If answering the question requires looking across
multiple systems, classify as:

student_performance

Examples:

"How am I doing overall?"
→ student_performance

"What should I improve?"
→ student_performance

"What are my strengths?"
→ student_performance

"What are my weaknesses?"
→ student_performance

"What should I focus on?"
→ student_performance

"Am I at academic risk?"
→ student_performance

"Give me a performance review."
→ student_performance

"Analyze my performance."
→ student_performance

"Summarize my progress."
→ student_performance

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

attendance_summary

- attendance
- attendance percentage
- attendance today
- attendance yesterday
- attendance this week
- attendance this month
- absent today
- present today
- late today
- missed classes
- period attendance
- attendance statistics

Examples:

"What is my attendance?"
→ attendance_summary

"Attendance yesterday"
→ attendance_summary

"How many classes did I miss?"
→ attendance_summary

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

homework_summary

- homework
- pending homework
- overdue homework
- due today
- due tomorrow
- homework feedback
- homework status
- assignments

Examples:

"What homework is pending?"
→ homework_summary

"Any overdue homework?"
→ homework_summary

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

assessment_summary

- assessment
- exam
- quiz
- test
- marks
- grades
- latest assessment
- upcoming assessment
- assessment feedback
- assessment result
- assessment score

Examples:

"What marks did I get?"
→ assessment_summary

"Latest assessment"
→ assessment_summary

"What exams are coming?"
→ assessment_summary

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

subject_summary

- strongest subject
- weakest subject
- best subject
- worst subject
- subject score
- subject grades
- subject comparison
- compare subjects
- list subjects
- subject performance
- subject analysis
- subject overview
- subject strengths
- subject weaknesses

Examples:

"My strongest subject."
→ subject_summary

"My weakest subject."
→ subject_summary

"Compare my subjects."
→ subject_summary

"List all my subjects."
→ subject_summary

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

atlas_score_summary

- atlas score
- academic score
- growth score
- engagement score
- atlas band
- atlas rank
- strongest pillar
- weakest pillar
- academic pillar
- growth pillar
- engagement pillar
- pillar score
- atlas trend
- atlas progress

Examples:

"What is my Atlas Score?"
→ atlas_score_summary

"What is my strongest pillar?"
→ atlas_score_summary

"What is my weakest pillar?"
→ atlas_score_summary

==================================================
IMPORTANT
==================================================

If the query clearly belongs to one specific module,
DO NOT classify it as student_performance.

Choose the most specific intent possible.

Only use student_performance when the answer genuinely
requires combining multiple modules.

==================================================
RETURN
==================================================

{
    "intent": "student_performance",
    "target_modules": [
        "student_performance"
    ],
    "confidence": 0.95
}
"""