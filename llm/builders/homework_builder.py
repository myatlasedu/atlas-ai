from __future__ import annotations


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

    # ==========================================
    # STATUS
    # ==========================================

    if titled_lookup:

        status = "info"

    elif overdue_count:

        status = "critical"

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

            "due_today": due_today_count,

            "due_tomorrow": due_tomorrow_count,

            "feedback": feedback_count,

            "submitted": submitted_count,

            "graded": graded_count,
        },

        "highlights": highlights,

        "priority_items": priority_items,

        "action_items": action_items,

        "titled_mark": titled_mark,

        "titled_lookup": titled_lookup,

        "pending": pending,

        "overdue": overdue,

        "due_today": due_today,

        "due_tomorrow": due_tomorrow,

        "recent_feedback": feedback,

        "submitted": submitted,

        "graded": graded,

        "next_up": next_up,

        "due_window": due_window,
    }