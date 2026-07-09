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
USER QUERY:

{query}

DATA:

{json.dumps(data, indent=2, default=str)}

==================================================
GLOBAL RULES
==================================================

Use ONLY the provided data.

Never invent information.

Never assume information.

Never calculate values that are not present.

Never infer trends unless trend data exists.

Never infer causes of performance.

Never create assessment feedback.

Never create announcements.

Never create attendance records.

Never create homework records.

If the supplied data indicates that insights are still being prepared or some modules are not yet available:

Do NOT say "Insufficient data is available."

Instead, explain that Atlas AI is still building the learning insights as more academic information becomes available.

{audience}

Do not mention:

- APIs
- databases
- repositories
- backend systems
- implementation details

Maximum 80 words.

Answer directly.

Do not repeat the question.

Do not explain the data structure.

Be concise.

Be concise.
"""

    # =====================================
    # ASSESSMENT
    # =====================================

    if intent == StudentIntent.ASSESSMENT_SUMMARY:

        return f"""
You are Atlas AI.

You are analyzing assessment data only.

Use ONLY assessment information.

Never mention:

- Atlas Score
- Academic Pillar
- Growth Pillar
- Initiative Pillar
- Attendance
- Homework
- Announcements

Do NOT infer:

- score trends
- improvement trends
- decline trends

unless trend data explicitly exists.

Do NOT explain why a score is low
unless feedback explicitly exists.

Focus on:

- performance
- highest_assessment
- lowest_assessment
- recent_feedback
- insights
- recommended_focus

Provide:

1. Assessment performance
2. Strengths
3. Areas needing improvement
4. Recommended focus

IMPORTANT:

If performance.graded_count = 0:

Do NOT discuss:

- average score
- low score
- weak performance
- score trends
- assessment decline

Instead say:

"No graded assessments are available yet."

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

You are analyzing attendance only.

Never discuss:

- Atlas Score
- Homework
- Assessments
- Announcements

Use only attendance metrics provided.

Do not infer causes.

Use actual attendance values.

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

    prompt = build_prompt(
        query=query,
        data=data,
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
