ATTENDANCE_PROMPT = """
==================================================
ATTENDANCE
==================================================

Attendance related queries use:

intent = "attendance_summary"

Populate the "view" field using ONLY one of these values:

- summary
- absent_students
- present_students
- late_students
- attendance_percentage
- attendance_trend
- class_summary
- low_attendance

Examples

Query:
Attendance summary today

Output:
{
    "intent":"attendance_summary",
    "view":"summary"
}

Query:
Who is absent today?

Output:
{
    "intent":"attendance_summary",
    "view":"absent_students"
}

Query:
Show absent students this week

Output:
{
    "intent":"attendance_summary",
    "view":"absent_students"
}

Query:
Who is present today?

Output:
{
    "intent":"attendance_summary",
    "view":"present_students"
}

Query:
Who came late today?

Output:
{
    "intent":"attendance_summary",
    "view":"late_students"
}

Query:
Attendance percentage this month

Output:
{
    "intent":"attendance_summary",
    "view":"attendance_percentage"
}

Query:
Attendance trend this month

Output:
{
    "intent":"attendance_summary",
    "view":"attendance_trend"
}

Query:
Attendance by class

Output:
{
    "intent":"attendance_summary",
    "view":"class_summary"
}

Query:
Students with low attendance

Output:
{
    "intent":"attendance_summary",
    "view":"low_attendance"
}
"""