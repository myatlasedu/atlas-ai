import calendar
import difflib
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

# ==========================================================
# CONSTANTS & TIMEZONES
# ==========================================================

IST = ZoneInfo("Asia/Kolkata")

MARKS_QUERY_KEYWORDS = ("marks", "grade", "score", "result")
HOMEWORK_QUERY_KEYWORDS = ("homework", "assignment", "worksheet", "submission", " hw")
FEEDBACK_QUERY_KEYWORDS = ("feedback", "remarks", "comments", "teacher say", "teacher said")
VALID_HOMEWORK_GRADES = ("A*", "A", "B", "C", "D", "E", "U")

MARKS_MANIPULATION_KEYWORDS = (
    "give me 100", "give me 100%", "100% marks", "100% grade",
    "100 percent", "change my marks", "set my marks",
    "update my marks", "increase my marks", "boost my marks",
    "full marks",
)

_MARKS_KEYS_TO_REMOVE = {
    "grade", "marks", "marks_obtained", "total_marks",
    "score", "final_grade", "percentage", "average_percentage",
    "highest_percentage", "lowest_percentage",
}

_WEEKDAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

DATE_WINDOW_PHRASES = (
    "day before yesterday", "yesterday", "today", "tomorrow",
    "this week", "last week", "next week",
    "this month", "last month", "next month",
    "this year", "last year", "next year",
)

_RELATIVE_WINDOW_PHRASES = DATE_WINDOW_PHRASES[4:]

_MONTH_NUMBERS = {
    name.lower(): i
    for i, name in enumerate(calendar.month_name) if name
}
_MONTH_NUMBERS.update({
    abbr.lower(): i
    for i, abbr in enumerate(calendar.month_abbr) if abbr
})
_MONTH_NUMBERS["sept"] = 9

_AMBIGUOUS_MONTHS = {
    "may", "jan", "feb", "mar", "apr", "jun",
    "jul", "aug", "sept", "sep", "oct", "nov", "dec",
}

_DATE_MARKERS = {
    "of", "in", "for", "during", "from",
    "since", "till", "until", "through", "between",
}

_MONTH_PATTERN = re.compile(
    r"\b(?:(?P<day1>\d{1,2})\s*(?:st|nd|rd|th)?\s+(?:of\s+)?)?"
    r"(?P<month>" + "|".join(_MONTH_NUMBERS.keys()) + r")"
    r"(?:\s+(?P<day2>\d{1,2})\s*(?:st|nd|rd|th)?)?"
    r"(?:\s*,?\s*(?P<year>\d{4}))?\b"
)

_INVALID_DATE_PATTERN = re.compile(
    r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(?P<month>"
    + "|".join(_MONTH_NUMBERS.keys())
    + r")\b"
)

# ==========================================================
# TIME HELPERS
# ==========================================================

def ist_now() -> datetime:
    return datetime.now(IST)

def ist_today() -> date:
    return ist_now().date()

ist_datetime = ist_now

def convert_to_ist(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(IST).isoformat()

def format_datetime(value: datetime | str) -> str:
    if not isinstance(value, datetime):
        value = datetime.fromisoformat(str(value))
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    return value.astimezone(IST).strftime("%d %b %Y at %I:%M %p")

# ==========================================================
# STRING & ENTITY RESOLUTION
# ==========================================================

def detect_invalid_date(query: str) -> bool:
    for match in _INVALID_DATE_PATTERN.finditer(query.lower()):
        day = int(match.group("day"))
        month = _MONTH_NUMBERS[match.group("month")]
        max_days = calendar.monthrange(ist_today().year, month)[1]
        if not (1 <= day <= max_days):
            return True
    return False

def resolve_canonical_name(raw: str, names: list[str], cutoff: float = 0.6) -> str | None:
    match = difflib.get_close_matches(
        str(raw).lower(),
        [str(n).lower() for n in names],
        n=1,
        cutoff=cutoff,
    )
    if match:
        return next(n for n in names if str(n).lower() == match[0])
    return None

def format_homework_graded_response(title: str, role: str = "student", close_match_note: str = "") -> str:
    target = "Your child's" if role == "guardian" else "Your"
    grade_target = "The" if role == "guardian" else "Your"
    return f"{close_match_note}{target} {title} homework has been graded. {grade_target} grade will be available on the report card."

def format_homework_ungraded_response(title: str, role: str = "student", close_match_note: str = "") -> str:
    target = "Your child's" if role == "guardian" else "Your"
    grade_target = "The" if role == "guardian" else "Your"
    return f"{close_match_note}{target} {title} homework has not been graded yet. {grade_target} grade will be available on the report card once declared."

# ==========================================================
# DATE RANGE RESOLUTION
# ==========================================================

def date_query(parsed: dict) -> str:
    raw = str(parsed.get("raw_query") or "").lower().strip()
    resolved = str(parsed.get("original_query") or "").lower().strip()
    if raw and (any(phrase in raw for phrase in DATE_WINDOW_PHRASES) or month_window(raw) is not None):
        return raw
    return resolved

def _is_date_usage(query: str, match: re.Match) -> bool:
    token = match.group("month")
    if token not in _AMBIGUOUS_MONTHS:
        return True
    if match.group("day1") or match.group("day2") or match.group("year"):
        return True
    preceding = query[: match.start()].split()
    return bool(preceding and preceding[-1] in _DATE_MARKERS)

def month_window(query: str) -> tuple[date, date] | None:
    if not query:
        return None
    lowered = query.lower()
    if any(phrase in lowered for phrase in _RELATIVE_WINDOW_PHRASES):
        return None

    for match in _MONTH_PATTERN.finditer(lowered):
        if not _is_date_usage(lowered, match):
            continue

        month = _MONTH_NUMBERS[match.group("month")]
        year = int(match.group("year")) if match.group("year") else ist_today().year
        last_day = calendar.monthrange(year, month)[1]
        day = match.group("day1") or match.group("day2")

        if day:
            day = int(day)
            if not 1 <= day <= last_day:
                return None
            target = date(year, month, day)
            return target, target

        return date(year, month, 1), date(year, month, last_day)
    return None

def resolve_dates(parsed: dict) -> dict:
    today = ist_today()
    query = date_query(parsed)

    # 1. Respect explicit ISO dates if already parsed
    start_date = parsed.get("start_date")
    end_date = parsed.get("end_date")
    if isinstance(start_date, date) and isinstance(end_date, date):
        return parsed
    if isinstance(start_date, str) and isinstance(end_date, str):
        try:
            parsed["start_date"] = date.fromisoformat(start_date)
            parsed["end_date"] = date.fromisoformat(end_date)
            return parsed
        except ValueError:
            pass

    # 2. Relative Days (yesterday, today, tomorrow)
    if "day before yesterday" in query:
        target = today - timedelta(days=2)
        parsed["start_date"] = parsed["end_date"] = target
        return parsed

    if "yesterday" in query:
        days = 1 + query.count("day before") + query.count("last")
        target = today - timedelta(days=days)
        parsed["start_date"] = parsed["end_date"] = target
        return parsed

    if "today" in query:
        parsed["start_date"] = parsed["end_date"] = today
        return parsed

    if "tomorrow" in query:
        days = 1 + query.count("next")
        target = today + timedelta(days=days)
        parsed["start_date"] = parsed["end_date"] = target
        return parsed

    # 3. Explicit Month Windows
    window = month_window(query)
    if window:
        parsed["start_date"], parsed["end_date"] = window
        return parsed

    # 4. Weeks
    current_week_start = today - timedelta(days=today.weekday())
    if "this week" in query:
        parsed["start_date"], parsed["end_date"] = current_week_start, today
        return parsed

    if "week" in query:
        if "last" in query:
            weeks = query.count("last")
            start = current_week_start - timedelta(days=7 * weeks)
            parsed["start_date"], parsed["end_date"] = start, start + timedelta(days=6)
            return parsed
        if "next" in query:
            weeks = query.count("next")
            start = current_week_start + timedelta(days=7 * weeks)
            parsed["start_date"], parsed["end_date"] = start, start + timedelta(days=6)
            return parsed
        parsed["start_date"], parsed["end_date"] = current_week_start, today
        return parsed

    # 5. Months
    if "this month" in query:
        parsed["start_date"], parsed["end_date"] = today.replace(day=1), today
        return parsed

    if "month" in query:
        if "last" in query:
            months_back = query.count("last")
            year, month = today.year, today.month
            for _ in range(months_back):
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1
            last_day = calendar.monthrange(year, month)[1]
            parsed["start_date"] = date(year, month, 1)
            parsed["end_date"] = date(year, month, last_day)
            return parsed
        if "next" in query:
            months_forward = query.count("next")
            year, month = today.year, today.month
            for _ in range(months_forward):
                month += 1
                if month == 13:
                    month = 1
                    year += 1
            last_day = calendar.monthrange(year, month)[1]
            parsed["start_date"] = date(year, month, 1)
            parsed["end_date"] = date(year, month, last_day)
            return parsed
        parsed["start_date"], parsed["end_date"] = today.replace(day=1), today
        return parsed

    # 6. Past / Next X Days
    match_past = re.search(r"(?:past|last)\s+(\d+)\s+days", query)
    if match_past:
        parsed["start_date"] = today - timedelta(days=int(match_past.group(1)))
        parsed["end_date"] = today
        return parsed

    match_next = re.search(r"next\s+(\d+)\s+days", query)
    if match_next:
        parsed["start_date"] = today
        parsed["end_date"] = today + timedelta(days=int(match_next.group(1)))
        return parsed

    # 7. Weekdays
    for weekday_name, weekday in _WEEKDAY_MAP.items():
        if f"last {weekday_name}" in query:
            delta = (today.weekday() - weekday) % 7 or 7
            target = today - timedelta(days=delta)
            parsed["start_date"] = parsed["end_date"] = target
            return parsed
        if f"next {weekday_name}" in query:
            delta = (weekday - today.weekday()) % 7 or 7
            target = today + timedelta(days=delta)
            parsed["start_date"] = parsed["end_date"] = target
            return parsed
        if re.search(rf"\b{weekday_name}\b", query):
            delta = (weekday - today.weekday()) % 7
            target = today + timedelta(days=delta)
            parsed["start_date"] = parsed["end_date"] = target
            return parsed

    return parsed

# ==========================================================
# GRADE SANITIZATION
# ==========================================================

def process_and_sanitize_grades(data):
    if isinstance(data, dict):
        has_grade_mark_indicator = any(
            k in data for k in (
                "grade", "marks", "marks_obtained", "total_marks",
                "score", "final_grade", "percentage",
                "is_graded", "isGrade", "isGraded",
            )
        ) or (
            data.get("status") in (2, 3)
            or data.get("status_tag") in ("graded", "submitted_not_graded")
        )

        if has_grade_mark_indicator:
            is_graded = False
            for key in ("isGrade", "isGraded", "is_graded"):
                if isinstance(data.get(key), bool):
                    is_graded = data[key]
                    break
            else:
                if data.get("status") in (2, 3) or data.get("status_tag") == "graded":
                    is_graded = True
                elif data.get("marks_obtained") is not None or (data.get("grade") and str(data.get("grade")).strip()):
                    is_graded = True

            data["isGrade"] = data["isGraded"] = data["is_graded"] = is_graded

            for key in _MARKS_KEYS_TO_REMOVE:
                data.pop(key, None)

        for k, v in list(data.items()):
            data[k] = process_and_sanitize_grades(v)
        return data

    if isinstance(data, list):
        return [process_and_sanitize_grades(item) for item in data]

    return data