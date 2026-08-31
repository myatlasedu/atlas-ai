from __future__ import annotations

from utils import format_datetime


def format_row_dates(row):
    row = dict(row)
    for key in ("submitted_at", "reviewed_at"):
        if row.get(key):
            row[key] = format_datetime(row[key])
    return row


def build_homework_llm_context(
    payload: dict,
) -> dict:

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

    if overdue_count:

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

        headline = (
            f"Your mark for "
            f"{titled_mark.get('title')} "
            f"is "
            f"{titled_mark.get('marks_obtained')}/"
            f"{titled_mark.get('total_marks')} "
            f"({titled_mark.get('percentage')}%)."
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

        "pending": [format_row_dates(x) for x in pending],

        "overdue": [format_row_dates(x) for x in overdue],

        "due_today": [format_row_dates(x) for x in due_today],

        "due_tomorrow": [format_row_dates(x) for x in due_tomorrow],

        "recent_feedback": [format_row_dates(x) for x in feedback],

        "submitted": [format_row_dates(x) for x in submitted],

        "graded": [format_row_dates(x) for x in graded],

        "resubmit": [format_row_dates(x) for x in resubmit],

        "upcoming": [format_row_dates(x) for x in upcoming],

        "awaiting_marks": [format_row_dates(x) for x in awaiting_marks],

        "next_up": (
            format_row_dates(next_up)
            if isinstance(next_up, dict)
            else None
        ),

        "due_window": due_window,
    }