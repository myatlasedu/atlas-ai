from __future__ import annotations


def build_attendance_llm_context(
    payload: dict,
) -> dict:

    total_marked_days = payload.get(
        "total_marked_days",
        0,
    )

    present_days = payload.get(
        "present_days",
        0,
    )

    attendance_percentage = payload.get(
        "attendance_percentage",
        0,
    )

    total_periods = payload.get(
        "total_periods",
        0,
    )

    present_periods = payload.get(
        "present_periods",
        0,
    )

    missed_periods = payload.get(
        "missed_periods",
        0,
    )

    late_periods = payload.get(
        "late_periods",
        0,
    )

    excused_periods = payload.get(
        "excused_periods",
        0,
    )

    healthroom_periods = payload.get(
        "healthroom_periods",
        0,
    )

    if total_marked_days == 0:

        status = "building"

    elif attendance_percentage >= 95:

        status = "excellent"

    elif attendance_percentage >= 85:

        status = "good"

    elif attendance_percentage >= 75:

        status = "attention"

    else:

        status = "critical"

    return {

        "status":
            status,

        "metrics": {

            "attendance_percentage":
                attendance_percentage,

            "total_marked_days":
                total_marked_days,

            "present_days":
                present_days,

            "total_periods":
                total_periods,

            "present_periods":
                present_periods,

            "missed_periods":
                missed_periods,

            "late_periods":
                late_periods,

            "excused_periods":
                excused_periods,

            "healthroom_periods":
                healthroom_periods,
        },

        "period_breakdown": {

            "present":
                present_periods,

            "missed":
                missed_periods,

            "late":
                late_periods,

            "excused":
                excused_periods,

            "healthroom":
                healthroom_periods,
        },

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