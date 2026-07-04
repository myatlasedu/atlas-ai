STUDENT_ANALYSIS_PROMPT = """
--------------------------------------------------

at_risk_students

Examples:

- Which students are at risk?
- Which students need intervention?
- Students needing attention
- Students performing poorly
- Students struggling
- Show at risk students
- Students with poor attendance and marks
- Which students should I help first?

View:

at_risk_students

--------------------------------------------------

student_profile

Examples:

- Show John's performance
- Student report
- Performance of Rahul
- Tell me about Aisha
- Student summary

View:

student_profile

==================================================
STUDENT ANALYSIS RULES
==================================================

Questions about:

- at risk students
- intervention
- struggling students
- weak students
- student performance
- student profile
- student summary
- overall performance

must be classified as:

student_analysis

==================================================
RETURN FORMAT
==================================================

Always return:

{
    "intent": "student_analysis",
    "view": "<selected_view>",
    "target_modules": [
        "attendance",
        "homework",
        "assessment"
    ]
}
"""