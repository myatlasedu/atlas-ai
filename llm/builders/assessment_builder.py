# llm/builders/assessment_builder.py

from __future__ import annotations

from core.marks_privacy import (
    GRADED_LABEL,
    PERFORMANCE_WITHHELD_NOTE,
    is_graded,
)


def build_assessment_llm_context(
    payload: dict,
) -> dict:
    """
    The assessment facts the LLM is allowed to see.

    Marks, grades, percentages, averages, trends, consistency ratings and
    rankings are all excluded: each of them either is a mark or is read off
    one. What remains is the schedule - what is coming up, what is pending,
    and whether a result exists at all.
    """

    latest = payload.get("latest_result") or {}

    return {

        "marks_policy": (
            "Marks, grades, scores and percentages must never be stated, and "
            f"neither must performance verdicts. {PERFORMANCE_WITHHELD_NOTE} "
            f"Work that has a result is referred to only as {GRADED_LABEL}."
        ),

        "metrics": {
            "graded": graded,
            # "average": performance.get("average_percentage", 0),
            # "highest": performance.get("highest_percentage", 0),
            # "lowest": performance.get("lowest_percentage", 0),
            "upcoming": payload.get("upcoming_count", 0),
            "pending": payload.get("pending_count", 0),
        },

        "best_assessment": (
            {
                "title": highest["title"],
                # "score": highest["percentage"],
                "grade": highest.get("grade"),
            }
            if highest else None
        ),

        "pending": payload.get("pending", [])[:5],

        "latest_assessment": (
            {
                "title": lowest["title"],
                # "score": lowest["percentage"],
                "grade": lowest.get("grade"),
            }
            if latest else None
        ),

        "highlights": payload.get("insights", [])[:4],

        "actions": payload.get(
            "improvement_opportunities",
            [],
        )[:3],
    }
