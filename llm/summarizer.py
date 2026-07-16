import json
import logging

from intents.student.enums import (
    StudentIntent
)

from llm.client import (
    chat_completion
)

from utils import format_datetime

from llm.student_prompt import (
    STUDENT_SYSTEM_PROMPT
)

from llm.guardian_prompt import (
    GUARDIAN_SYSTEM_PROMPT
)

from llm.builders.context_builder import (
build_llm_context,
)

logger = logging.getLogger(__name__)


def build_prompt(
    query: str,
    data: dict,
    role: str,
    intent    
):

    audience = (
        "Speak directly to the guardian. \
        Use 'your child' or the student's name to refer to the student.\
        Do not tell the guardian to speak to the guardian.\
        Do not address the student directly."
        if role == "guardian"
        else
        "Speak directly to the student. Use 'you' to refer to the student."
    )

    common = f"""
    QUESTION

    {query}

    CONTEXT

    {json.dumps(data, separators=(",", ":"))}

    Rules

    - Use only the supplied context.
    - Never invent information.
    - Never assume missing information.
    - Keep the reply under 80 words.
    - {audience}
    """

        # =====================================
        # ASSESSMENT
        # =====================================

    if intent == StudentIntent.ASSESSMENT_SUMMARY:

        return f"""
    You are Atlas AI.

    Use ONLY the supplied assessment context.

    If status="building":

    Explain that assessment insights are still being prepared as more assessments are completed.

    Otherwise:

    Prioritize your response in this order:

    1. Overall assessment status.
    2. The most important highlight.
    3. Performance trend.
    4. Upcoming assessments (if any).
    5. Recommended focus.
    6. Recommended actions.

    Use:

    - status
    - metrics
    - best_assessment
    - weakest_assessment
    - highlights
    - focus
    - actions

    Do NOT:

    - calculate scores
    - infer trends
    - invent feedback
    - invent recommendations
    - mention JSON
    - mention data fields
    - mention missing information

    Use the supplied highlights and actions exactly as guidance.

    Write naturally.

    Keep the response under 80 words.

    {common}
    """

    # =====================================
    # ATLAS
    # =====================================

    if intent == StudentIntent.ATLAS_SCORE_SUMMARY:

        return f"""
You are Atlas AI.

You are analyzing Atlas Intelligence.

Use ONLY Atlas information.

Never reference:

- assessments
- homework
- attendance
- announcements

unless explicitly provided.

Use:

- atlas_score
- strongest_actionable_pillar
- weakest_actionable_pillar
- insights
- recommended_focus

Do NOT calculate pillars.

Do NOT rank pillars yourself.

Use values already provided.

If a pillar is missing:

Do not discuss it.

IMPORTANT:

If atlas_score.status = "calibrating":

Do not discuss:

- rank
- score changes
- trends

Explain that Atlas Score is still calibrating.

{common}
"""

    if (
        hasattr(StudentIntent, "PERSONAL_EVENT_SUMMARY")
        and
        intent == StudentIntent.PERSONAL_EVENT_SUMMARY
    ):

        return f"""
    You are Atlas AI.

    You are summarizing personal events.

    Use ONLY the provided event data.

    IMPORTANT:

    If event_count > 0:

    You MUST list the events.

    Do NOT say "Insufficient data is available."

    Instead, explain that Atlas AI is still building the learning insights as more academic information becomes available.

    Do NOT summarize only the count.

    For each event include:

    - title
    - scheduled date
    - scheduled time

    Example:

    You have 1 upcoming event:

    • Play Chess — 18 Jun 2026 at 10:30 AM

    If event_count = 0:

    Respond exactly:

    "No events are scheduled."

    Do not invent dates or times.

    {common}
    """
    
    # =====================================
    # JOURNAL
    # =====================================

    if intent == StudentIntent.JOURNAL_SUMMARY:

        return f"""
    You are Atlas AI.

    You are summarizing journal entries.

    Use ONLY journal data.

    If entries exist:

    - Mention the number of entries.
    - Summarize recent entries.

    If no entries exist:

    Say:

    "No journal entries are available."

    Do not invent journal content.

    {common}
    """

    # =====================================
    # ACTION CONFIRMATION
    # =====================================

    if intent == StudentIntent.ACTION_CONFIRMATION:

        return f"""
    You are Atlas AI.

    An action has already been completed.

    Use ONLY supplied data.

    Respond only with the outcome.

    {common}
    """

    # =====================================
    # UNKNOWN
    # =====================================

    if intent == StudentIntent.UNKNOWN:

        return f"""
    You are Atlas AI.

    The request could not be understood.

    Respond:

    "I could not understand your request."

    {common}
    """
    
    # =====================================
    # HOMEWORK
    # =====================================

    if intent == StudentIntent.HOMEWORK_SUMMARY:

        return f"""
You are Atlas AI.

You are analyzing homework data only.

Never discuss:

- Atlas Score
- Assessments
- Attendance
- Announcements

Focus on:

- pending homework
- overdue homework
- due today
- due tomorrow
- teacher feedback

Use only supplied homework data.

{common}
"""

    # =====================================
    # ATTENDANCE
    # =====================================

    if intent == StudentIntent.ATTENDANCE_SUMMARY:

        return f"""
You are Atlas AI.

Use ONLY the supplied attendance context.

The backend has already analyzed the attendance information.

Do NOT perform calculations.

Do NOT infer trends.

Do NOT infer improvement or decline.

Do NOT invent attendance issues.

Use ONLY the supplied information.

If status == "building":

Explain that attendance information is still being built because no attendance records are available yet.

Otherwise, structure the response in this order:

1. Overall attendance status.
2. Days the student attended school.
3. Class period attendance summary.
4. Important highlights.
5. Recommended focus (if present).
6. Recommended actions (if present).

Use:

- status
- metrics
- period_breakdown
- highlights
- focus
- actions

The attendance metrics represent:

- total_marked_days → number of school days with RFID attendance records.
- present_days → days the student attended school.
- total_periods → recorded class periods on attended days.
- present_periods → class periods attended.
- missed_periods → class periods missed.
- late_periods → class periods attended late.
- excused_periods → excused class periods.
- healthroom_periods → class periods spent in the health room.

Do NOT:

- refer to holidays
- refer to absent days
- infer missed school days
- calculate percentages
- mention JSON
- mention field names
- explain the data structure

Write naturally and keep the response under 80 words.

{common}
"""

    # =====================================
    # ANNOUNCEMENTS
    # =====================================

    if (
        hasattr(StudentIntent, "ANNOUNCEMENT_SUMMARY")
        and
        intent == StudentIntent.ANNOUNCEMENT_SUMMARY
    ):

        return f"""
You are Atlas AI.

You are summarizing announcements.

Use ONLY announcement data.

Focus on:

- latest_announcement
- recent_announcements

Do not discuss:

- attendance
- homework
- assessments
- atlas score

If announcements exist:

Summarize the most important ones.

If none exist:

State that there are currently no announcements.

{common}
"""

    # =====================================
    # DAILY SUMMARY
    # =====================================

    if intent == StudentIntent.DAILY_SUMMARY:

        return f"""
You are Atlas AI.

Provide a concise daily summary.

Use only supplied data.

Include:

- attendance
- homework
- assessments
- announcements
- atlas insights

Prioritize action items.

Do not invent missing information.

{common}
"""

    if intent == StudentIntent.STUDENT_PERFORMANCE:

            return f"""
        You are Atlas AI.

        The backend has already analyzed the student's performance.

        Do NOT perform additional analysis.

        Do NOT calculate anything.

        Do NOT infer trends.

        Do NOT invent recommendations.

        Use ONLY the information inside:

        llm_summary

        Specifically:

        - overall_status
        - strengths
        - concerns
        - recommended_actions
        - atlas_status

        Write:

        1. One sentence summarizing overall performance.
        2. Mention the key strengths.
        3. Mention the primary concerns.
        4. Mention the recommended actions.

        Do not mention missing modules.

        Do not mention JSON.

        Do not explain the data structure.

        Use only the supplied information.

        {common}
        """

    if intent == StudentIntent.STUDENT_REPORT:

        return f"""
    You are Atlas AI.

    The backend has already prepared the student's report.

    Use ONLY the supplied data.

    Do NOT perform calculations.

    Do NOT infer trends.

    Do NOT create recommendations beyond those already supplied.

    Prioritize:

    - llm_summary.overall_status
    - llm_summary.strengths
    - llm_summary.concerns
    - llm_summary.recommended_actions

    Mention attendance, homework, assessments and Atlas only if present.

    Produce a concise report in under 120 words.

    {common}
    """
        
    if intent == StudentIntent.SUBJECT_SUMMARY:

        return f"""
    You are Atlas AI.

    You are analyzing subject performance.

    Use only subject data.

    If subject_analysis=true:

    Explain:

    - strongest subject
    - weakest subject
    - score differences
    - grades
    - recommended focus

    Use actual values.

    Do not discuss:

    - attendance
    - homework
    - assessments
    - atlas score

    unless explicitly present.

    {common}
    """

    if intent == StudentIntent.TOPIC_SUMMARY:

        return f"""
            You are Atlas AI.

            You are analyzing topic progress.

            Use only topic data.

            Focus on:

            - completed topics
            - pending topics
            - completion percentage
            - strongest areas
            - weakest areas

            Do not discuss:

            - attendance
            - homework
            - atlas score

            unless explicitly provided.

            {common}
        """
    
    

async def summarize_response(
    query: str,
    data: dict,
    context,
    intent
):
    
    if intent == StudentIntent.PERSONAL_EVENT_SUMMARY:

        events = (
            data
            .get("personal_event_tool", {})
            .get("events", [])
        )

        if events:

            lines = []

            for event in events:

                lines.append(
                    f"• {event['title']} — "
                    f"{format_datetime(event['start_datetime'])}"
                )

            return (
                f"You have {len(events)} upcoming "
                f"event{'s' if len(events) != 1 else ''}:\n\n"
                + "\n".join(lines)
            )

        return "No events are scheduled."


    import json

    print(json.dumps(data, indent=2, default=str))  
    llm_data = build_llm_context(
        data
    )

    print(json.dumps(llm_data, indent=2))

    prompt = build_prompt(
        query=query,
        data=llm_data,
        role=context.role,
        intent=intent
    )

    
    system_prompt = STUDENT_SYSTEM_PROMPT

    if context.role == "guardian":

        system_prompt = GUARDIAN_SYSTEM_PROMPT

    response = await chat_completion(
        [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    logger.info(
        "Summarizer response: %s",
        response
    )

    return response["message"]["content"]
