from __future__ import annotations

from utils import format_datetime, VALID_HOMEWORK_GRADES


def format_row_dates(row):
    if not isinstance(row, dict):
        return row
    return {
        "title": row.get("title"),
        "subject_name": row.get("subject_name"),
        "teacher_name": row.get("teacher_name"),
        "status_tag": row.get("status_tag"),
        "due_date": str(row.get("due_date"))[:10] if row.get("due_date") else None,
        "submitted_at": format_datetime(row.get("submitted_at")) if row.get("submitted_at") else None,
        "reviewed_at": format_datetime(row.get("reviewed_at")) if row.get("reviewed_at") else None,
        "grade": (row.get("grade") or "").strip() if row.get("grade") else None,
    }


def build_homework_llm_context(
    payload: dict,
) -> dict:

    titled_mark = payload.get(
        "titled_mark"
    )

    titled_lookup = payload.get(
        "titled_lookup"
    )

    pending = payload.get(
        "pending",
        [],
    )

    overdue = payload.get(
        "overdue",
        [],
    )

    due_today = payload.get(
        "due_today",
        [],
    )

    due_tomorrow = payload.get(
        "due_tomorrow",
        [],
    )

    feedback = payload.get(
        "recent_feedback",
        [],
    )

    submitted = payload.get(
        "submitted",
        [],
    )

    graded = payload.get(
        "graded",
        [],
    )

    resubmit = payload.get(
        "resubmit",
        [],
    )

    upcoming = payload.get(
        "upcoming",
        [],
    )

    awaiting_marks = payload.get(
        "awaiting_marks",
        [],
    )

    next_up = payload.get(
        "next_up",
        None,
    )

    focus = payload.get(
        "focus",
        None,
    )

    due_window = payload.get(
        "due_window",
        None,
    )

    pending_count = len(pending)
    overdue_count = len(overdue)
    due_today_count = len(due_today)
    due_tomorrow_count = len(due_tomorrow)
    feedback_count = len(feedback)
    submitted_count = len(submitted)
    graded_count = len(graded)
    resubmit_count = len(resubmit)
    upcoming_count = len(upcoming)
    awaiting_marks_count = len(awaiting_marks)

    # ==========================================
    # STATUS
    # ==========================================

    if titled_lookup:

        status = "info"

    elif overdue_count:

        status = "critical"

    elif resubmit_count:

        status = "attention"

    elif due_today_count or pending_count:

        status = "attention"

    else:

        status = "good"

    # ==========================================
    # HEADLINE
    # ==========================================

    if titled_mark:

        grade = (titled_mark.get("grade") or "").strip()

        if grade in VALID_HOMEWORK_GRADES:

            headline = (
                f"Your grade for "
                f"{titled_mark.get('title')} "
                f"is {grade}."
            )

        else:

            headline = (
                f"{titled_mark.get('title')} "
                f"has been graded, but no grade "
                f"is recorded yet."
            )

    elif titled_lookup:

        headline = (
            f"Homework lookup for "
            f"{titled_lookup.get('title')}."
        )

    elif focus == "graded" and not overdue_count:

        headline = (
            f"{graded_count} homework assignment(s) "
            f"have been graded."
        )

    elif focus == "submitted" and not overdue_count:

        headline = (
            f"You have handed in "
            f"{submitted_count} homework assignment(s)."
        )

    elif focus == "feedback":

        headline = (
            f"Teacher feedback is available on "
            f"{feedback_count} assignment(s)."
        ) if feedback_count else (
            "No teacher feedback yet."
        )

    elif focus == "resubmit":

        headline = (
            f"{resubmit_count} homework assignment(s) "
            f"need to be resubmitted."
        ) if resubmit_count else (
            "No homework is waiting for resubmission."
        )

    elif focus == "upcoming":

        headline = (
            f"{upcoming_count} homework assignment(s) "
            f"coming up."
        ) if upcoming_count else (
            "No homework is coming up."
        )

    elif focus == "awaiting_marks":

        headline = (
            f"{awaiting_marks_count} homework assignment(s) "
            f"submitted but not yet graded."
        ) if awaiting_marks_count else (
            "No submitted homework is awaiting marks."
        )

    elif overdue_count:

        headline = (
            "Some homework requires immediate attention."
        )

    elif due_today_count:

        headline = (
            "You have homework due today."
        )

    elif pending_count:

        headline = (
            "You have homework to complete."
        )

    else:

        headline = (
            "You are up to date with your homework."
        )

    # ==========================================
    # HIGHLIGHTS
    # ==========================================

    highlights = []

    if pending_count:

        highlights.append(
            f"{pending_count} pending homework assignment(s)."
        )

    if overdue_count:

        highlights.append(
            f"{overdue_count} overdue homework assignment(s)."
        )

    if due_today_count:

        highlights.append(
            f"{due_today_count} assignment(s) due today."
        )

    if due_tomorrow_count:

        highlights.append(
            f"{due_tomorrow_count} assignment(s) due tomorrow."
        )

    if feedback_count:

        highlights.append(
            f"Teacher feedback available for {feedback_count} assignment(s)."
        )

    if resubmit_count:

        highlights.append(
            f"{resubmit_count} resubmission(s) requested."
        )

    if upcoming_count:

        highlights.append(
            f"{upcoming_count} homework assignment(s) coming up."
        )

    if awaiting_marks_count:

        highlights.append(
            f"{awaiting_marks_count} homework assignment(s) "
            f"awaiting marks."
        )

    # ==========================================
    # PRIORITY ITEMS
    # ==========================================

    priority_items = []

    source = (
        overdue
        or due_today
        or pending
    )

    for item in source[:3]:

        priority_items.append(
            item.get(
                "title",
                "Homework",
            )
        )

    # ==========================================
    # ACTIONS
    # ==========================================

    action_items = []

    if overdue_count:

        action_items.append(
            "Complete overdue homework first."
        )

    if due_today_count:

        action_items.append(
            "Submit today's homework before the deadline."
        )

    if due_tomorrow_count:

        action_items.append(
            "Prepare homework due tomorrow."
        )

    if feedback_count:

        action_items.append(
            "Review your teacher's feedback."
        )

    return {

        "module": "homework",

        "status": status,

        "headline": headline,

        "focus": focus,

        "metrics": {

            "pending": pending_count,

            "overdue": overdue_count,

            "resubmit": resubmit_count,

            "upcoming": upcoming_count,

            "due_today": due_today_count,

            "due_tomorrow": due_tomorrow_count,

            "feedback": feedback_count,

            "submitted": submitted_count,

            "graded": graded_count,

            "awaiting_marks": awaiting_marks_count,
        },

        "highlights": highlights,

        "priority_items": priority_items,

        "action_items": action_items,

        "titled_mark": titled_mark,

        "titled_lookup": titled_lookup,

        "pending": [format_row_dates(x) for x in pending[:10]],

        "overdue": [format_row_dates(x) for x in overdue[:10]],

        "due_today": [format_row_dates(x) for x in due_today[:10]],

        "due_tomorrow": [format_row_dates(x) for x in due_tomorrow[:10]],

        "recent_feedback": [format_row_dates(x) for x in feedback[:10]],

        "submitted": [format_row_dates(x) for x in submitted[:10]],

        "graded": [format_row_dates(x) for x in graded[:10]],

        "resubmit": [format_row_dates(x) for x in resubmit[:10]],

        "upcoming": [format_row_dates(x) for x in upcoming[:10]],

        "awaiting_marks": [format_row_dates(x) for x in awaiting_marks[:10]],

        "next_up": (
            format_row_dates(next_up)
            if isinstance(next_up, dict)
            else None
        ),

        "due_window": due_window,
    }