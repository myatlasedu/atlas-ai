# llm/builders/assessment_builder.py

from __future__ import annotations


def build_assessment_llm_context(
    payload: dict,
) -> dict:

    performance = payload.get("performance", {})
    consistency = payload.get("consistency", {})
    trend = payload.get("trend", {})

    highest = payload.get("highest_assessment")
    lowest = payload.get("lowest_assessment")

    graded = performance.get("graded_count", 0)

    if graded == 0:
        status = "building"
    else:
        status = "good"

    raw_highlights = payload.get("insights", [])
    clean_highlights = [
        h for h in raw_highlights
        if not any(k in h.lower() for k in ["%", "score", "average", "target", "below", "declining", "attention", "poor"])
    ]

    raw_actions = payload.get("improvement_opportunities", [])
    clean_actions = [
        a for a in raw_actions
        if not any(k in a.lower() for k in ["%", "score", "average", "lower-scoring", "below", "consistency"])
    ]

    return {

        "status": status,

        "metrics": {
            "graded": graded,
            "upcoming": payload.get("upcoming_count", 0),
        },

        "best_assessment": None,

        "weakest_assessment": None,

        "highlights": clean_highlights[:4],

        "focus": payload.get("recommended_focus", [])[:3],

        "actions": clean_actions[:3],
    }