from __future__ import annotations

def build_period_breakdown(
    period_rows: list,
) -> dict:

    status_to_key = {
        1: "present",
        2: "missed",
        3: "late",
        4: "excused",
        5: "healthroom",
    }

    breakdown = {
        "present": [],
        "missed": [],
        "late": [],
        "excused": [],
        "healthroom": [],
    }

    for row in period_rows:

        key = status_to_key.get(
            row["status"]
        )

        if key is None:
            continue

        breakdown[key].append(
            {
                "date": row["date"].isoformat(),
                "period": row["period_name"],
                "subject": row["subject_name"],
                "start_time": row["start_time"].isoformat(),
                "end_time": row["end_time"].isoformat(),
            }
        )

    return {
        key: {
            "count": len(lessons),
            "lessons": lessons,
        }
        for key, lessons in breakdown.items()
    }

def build_attendance_llm_context(
    payload: dict,
) -> dict:

    present_days = payload.get(
        "present_days",
        0,
    )

    working_days = payload.get(
        "working_days",
        0,
    )

    absent_days = payload.get(
        "absent_days",
        0,
    )

    absent_day_dates = payload.get(
        "absent_day_dates",
        [],
    )

    non_working_days = payload.get(
        "non_working_days",
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

    period_rows = payload.get(
        "period_rows",
        [],
    )

    if working_days == 0:

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

            "present_days":
                present_days,

            "working_days":
                working_days,

            "absent_days":
                absent_days,

            "absent_day_dates":
                absent_day_dates,

            "non_working_days":
                non_working_days,

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

        "period_breakdown": 
            build_period_breakdown(
                period_rows,
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

def build_attendance_insights(
    payload: dict,
) -> dict:

    insights = []

    recommended_focus = []

    recommended_actions = []

    present_days = payload.get(
        "present_days",
        0,
    )

    working_days = payload.get(
        "working_days",
        0,
    )

    absent_days = payload.get(
        "absent_days",
        0,
    )

    non_working_days = payload.get(
        "non_working_days",
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

    if working_days == 0:

        insights.append(
            "No attendance records are available yet."
        )

    else:

        days_insight = (
            f"You attended school on {present_days} of {working_days} working day(s)"
            f", were absent on {absent_days} day(s)"
        )

        if non_working_days:

            days_insight += (
                f", and there were {non_working_days} non-working day(s)"
                f" (weekends and holidays)"
            )

        insights.append(
            days_insight + "."
        )

        if total_periods:

            insights.append(
                f"You attended {present_periods} of {total_periods} recorded lessons."
            )

        if missed_periods:

            insights.append(
                f"You missed {missed_periods} lesson(s)."
            )

        if late_periods:

            insights.append(
                f"You were late for {late_periods} lesson(s)."
            )

        if excused_periods:

            insights.append(
                f"{excused_periods} lesson(s) were excused."
            )

        if healthroom_periods:

            insights.append(
                f"You visited the health room during {healthroom_periods} lesson(s)."
            )

    if missed_periods:

        recommended_focus.append(
            "Attend every scheduled lesson."
        )

    if missed_periods:

        recommended_actions.append(
            "Reduce missed lessons."
        )

    if late_periods:

        recommended_actions.append(
            "Arrive on time for every class."
        )

    if (
        total_periods > 0
        and
        (
            present_periods / total_periods
        ) < 0.9
    ):

        recommended_actions.append(
            "Improve consistency across all scheduled classes."
        )

    payload["insights"] = insights

    payload["recommended_focus"] = (
        recommended_focus
    )

    payload["recommended_actions"] = (
        recommended_actions
    )

    return payload