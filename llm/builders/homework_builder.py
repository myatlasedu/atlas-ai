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

    pending_count = len(pending)
    overdue_count = len(overdue)
    due_today_count = len(due_today)
    due_tomorrow_count = len(due_tomorrow)
    feedback_count = len(feedback)

    def _itemize(
        rows: list,
    ) -> list[dict]:

        return [
            {
                "title": row.get(
                    "title",
                    "Homework",
                ),
                "due_date": (
                    str(
                        row["due_date"]
                    )
                    if row.get("due_date")
                    else None
                ),
            }
            for row in rows[:8]
        ]

    pending_items = _itemize(pending)
    overdue_items = _itemize(overdue)
    due_today_items = _itemize(due_today)
    due_tomorrow_items = _itemize(due_tomorrow)

    feedback_items = [
        {
            "title": row.get(
                "title",
                "Homework",
            ),
            "teacher_note": (
                row.get(
                    "teacher_note",
                    "",
                )
                or ""
            ),
            "marks_obtained": (
                row.get(
                    "marks_obtained",
                    None,
                )
            ),
        }
        for row in feedback[:8]
    ]

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

        "metrics": {

            "pending": pending_count,

            "overdue": overdue_count,

            "due_today": due_today_count,

            "due_tomorrow": due_tomorrow_count,

            "feedback": feedback_count,
        },

        "highlights": highlights,

        "priority_items": priority_items,

        "action_items": action_items,

        "titled_mark": titled_mark,

        "titled_lookup": titled_lookup,

        "pending_items": pending_items,

        "overdue_items": overdue_items,

        "due_today_items": due_today_items,

        "due_tomorrow_items": due_tomorrow_items,

        "feedback_items": feedback_items,
    }