PERFORMANCE_PROMPT = """
==================================================
STUDENT PERFORMANCE
==================================================

Intent:
student_performance

Used when the student wants a holistic
performance review that combines multiple
areas of student life and learning.

This intent is used for analysis,
recommendations, risks, trends and
improvement guidance.

==================================================
USED FOR
==================================================

- overall performance
- holistic performance
- performance review
- performance analysis
- strengths
- weaknesses
- improvement advice
- academic risk
- readiness
- recommendations
- performance decline
- focus areas
- improvement plan
- performance concerns
- learning habits
- study recommendations

Examples:

- How am I doing overall?
- Give me a performance overview.
- Review my academic performance.
- What are my strengths?
- What are my weaknesses?
- What concerns do you see?
- What should I focus on next?
- What is preventing me from improving?
- Why is my performance declining?
- Am I at risk academically?
- How prepared am I?
- What should I improve?
- Where do I need the most support?
- Give me recommendations based on my performance.
- Analyze my performance.
- Summarize how I am doing as a student.
- How can I improve my Atlas score?

Return:

{
    "intent": "student_performance",
    "target_modules": ["student_performance"],
    "confidence": 0.95
}

==================================================
CLASSIFICATION RULES
==================================================

Questions that require combining
multiple systems such as:

- attendance
- homework
- assessments
- subjects
- atlas

must be classified as:

student_performance

Examples:

- How am I doing overall?
- What are my strengths?
- What are my weaknesses?
- What should I focus on?
- Am I at risk academically?
- Give me a performance review.
- Analyze my performance.

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following MUST NOT be classified as:

student_performance

They belong to:

atlas_score_summary

- atlas score
- academic score
- growth score
- initiative score
- atlas band
- atlas rank
- strongest pillar
- weakest pillar
- academic pillar
- growth pillar
- initiative pillar
- pillar score
- atlas progress
- atlas trend

Examples:

How is my academic score?
→ atlas_score_summary

What is my growth score?
→ atlas_score_summary

What is my initiative score?
→ atlas_score_summary

What is my Atlas score?
→ atlas_score_summary

What is my strongest pillar?
→ atlas_score_summary

What is my weakest pillar?
→ atlas_score_summary

==================================================
DO NOT USE STUDENT PERFORMANCE
==================================================

The following belong to:

assessment_summary

- assessment result
- test result
- exam result
- marks
- grades
- assessment feedback
- upcoming assessments
- pending assessments

Examples:

What marks did I get?
→ assessment_summary

What was my latest assessment result?
→ assessment_summary

Do I have any upcoming assessments?
→ assessment_summary

==================================================
TARGET MODULES
==================================================

student_performance

[
    "student_performance"
]
"""