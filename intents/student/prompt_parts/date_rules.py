DATE_RULES = """
==================================================
DATE EXTRACTION RULES
==================================================

Extract dates only.

If the user explicitly mentions a calendar date, populate:

- start_date
- end_date

using ISO format (YYYY-MM-DD).

Examples:

15 July 2026
→ start_date="2026-07-15"
→ end_date="2026-07-15"

15 Jul
→ YYYY-07-15

2026-07-15
→ keep unchanged

Date ranges:

15 Jul to 20 Jul
→ populate both start_date and end_date.

If the user does NOT explicitly mention a calendar date, return:

start_date = null
end_date = null

Do NOT resolve:

- today
- yesterday
- tomorrow
- this week
- last week
- next week
- this month
- last month
- next month
- Monday
- Tuesday
- weekends

Leave them as null.

The backend resolves all relative dates.
"""