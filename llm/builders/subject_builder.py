from __future__ import annotations

from core.marks_privacy import PERFORMANCE_WITHHELD_NOTE


def build_subject_llm_context(
    payload: dict,
) -> dict:
    """
    The subject facts the LLM is allowed to see.

    Subject scores, rankings and "high performing" / "needs attention" counts
    are all read off the student's marks, so only the enrolled subjects and
    their count leave this builder.
    """

    return {

        "marks_policy": (
            "Never state a subject score, mark, grade, percentage or ranking, "
            f"and never name a strongest or weakest subject. "
            f"{PERFORMANCE_WITHHELD_NOTE}"
        ),

        "metrics": {

            "subject_count":
                payload.get(
                    "subject_count",
                    0,
                ),
        },

        "subjects": [
            {
                "subject_name": item.get("subject_name"),
                "teacher_name": item.get("teacher_name"),
            }
            for item in (payload.get("subjects") or [])[:15]
            if isinstance(item, dict)
        ],
    }
