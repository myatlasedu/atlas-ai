from __future__ import annotations


def build_subject_llm_context(
    payload: dict,
) -> dict:

    status = payload.get(
        "status",
        "building",
    )

    return {

        "status":
            status,

        "metrics": {

            "subject_count":
                payload.get(
                    "subject_count",
                    0,
                ),

            "average_score":
                payload.get(
                    "average_score",
                    0,
                ),

            "highest_score":
                payload.get(
                    "highest_score",
                    0,
                ),

            "lowest_score":
                payload.get(
                    "lowest_score",
                    0,
                ),

            "high_performing_subjects":
                payload.get(
                    "high_performing_subjects",
                    0,
                ),

            "needs_attention_subjects":
                payload.get(
                    "needs_attention_subjects",
                    0,
                ),
        },

        "strongest_subject":
            payload.get(
                "strongest_subject",
            ),

        "weakest_subject":
            payload.get(
                "weakest_subject",
            ),

        "highlights":
            payload.get(
                "insights",
                [],
            ),

        "focus":
            payload.get(
                "recommended_focus",
                [],
            ),

        "actions":
            payload.get(
                "recommended_actions",
                [],
            ),
    }