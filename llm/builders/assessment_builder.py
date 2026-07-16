# llm/builders/assessment_builder.py

from __future__ import annotations


def build_assessment_llm_context(
    payload: dict,
) -> dict:

    performance = payload.get("performance", {})
    consistency = payload.get("consistency", {})
    trend = payload.get("trend", {})
    flags = payload.get("assessment_flags", {})

    highest = payload.get("highest_assessment")
    lowest = payload.get("lowest_assessment")

    graded = performance.get("graded_count", 0)

    if graded == 0:
        status = "building"
    elif flags.get("has_risk_assessments"):
        status = "critical"
    elif trend.get("direction") == "declining":
        status = "attention"
    else:
        status = "good"

    return {

        "status": status,

        "metrics": {
            "graded": graded,
            "average": performance.get("average_percentage", 0),
            "highest": performance.get("highest_percentage", 0),
            "lowest": performance.get("lowest_percentage", 0),
            "upcoming": payload.get("upcoming_count", 0),
            "risk": len(payload.get("risk_assessments", [])),
            "trend": trend.get("direction"),
            "consistency": consistency.get("rating"),
        },

        "best_assessment": (
            {
                "title": highest["title"],
                "score": highest["percentage"],
            }
            if highest else None
        ),

        "weakest_assessment": (
            {
                "title": lowest["title"],
                "score": lowest["percentage"],
            }
            if lowest else None
        ),

        "highlights": payload.get("insights", [])[:4],

        "focus": payload.get("recommended_focus", [])[:3],

        "actions": payload.get(
            "improvement_opportunities",
            [],
        )[:3],
    }