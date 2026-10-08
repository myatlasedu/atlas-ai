SCREEN_NAVIGATION_PROMPT = """
--------------------------------------------------

screen_navigation

Used when the guardian wants to navigate
to a screen inside the application.

==================================================
SUPPORTED NAVIGATION TARGETS
==================================================

- homework
- attendance
- assessments
- report_cards
- timetable
- announcements
- events

==================================================
EXAMPLES
==================================================

Open homework
→ navigation_target = homework

Take me to my child's homework
→ navigation_target = homework

Open attendance
→ navigation_target = attendance

Go to attendance
→ navigation_target = attendance

Open timetable
→ navigation_target = timetable

Open structure of the day
→ navigation_target = timetable

Take me to announcements
→ navigation_target = announcements

Open events
→ navigation_target = events

Open calendar
→ navigation_target = events

Open food menu
→ navigation_target = food_menu

Take me to the food menu
→ navigation_target = food_menu

Show food menu
→ navigation_target = food_menu

Take me to resources
→ navigation_target = resources

Show my child books
→ navigation_target = resources

Show my child's resources
→ navigation_target = resources

Show my child's Study Material
→ navigation_target = resources

==================================================
OUTPUT RULES
==================================================

You MUST populate:

navigation_target

using one of the supported navigation targets.

Use navigation_target = null ONLY when the
destination is not one of the supported targets.

Example:

User:

Take me to homework

Output:

{
    "intent": "screen_navigation",
    "navigation_target": "homework"
}
"""
