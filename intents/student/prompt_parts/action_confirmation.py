ACTION_CONFIRMATION_PROMPT = """
--------------------------------------------------

action_confirmation

Used when the student is confirming
a previously requested action.

Examples:

- yes
- yes please
- confirm
- proceed
- go ahead
- okay
- okay create it
- create it
- yes create it
- do it
- continue

==================================================

CLASSIFICATION RULES

If the message is primarily a confirmation
of a previously requested action,
classify as:

action_confirmation

Do not classify as:

- daily_summary
- attendance_summary
- homework_summary
- assessment_summary
- student_performance

when the user is clearly confirming an action.
"""