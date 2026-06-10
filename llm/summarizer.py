import json
import logging

from intents.student.enums import (
    StudentIntent
)

from llm.client import (
    chat_completion
)

logger = logging.getLogger(__name__)


def build_prompt(
    query: str,
    data: dict,
    intent
):

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

If sufficient data is unavailable:

Say:

"Insufficient data is available."

Speak directly to the student.

Do not mention:

- APIs
- databases
- repositories
- backend systems
- implementation details

Maximum 120 words.

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

If events exist:

- Mention the number of events.
- List each event.
- Include title and scheduled date/time.
- Present them in chronological order.

If no events exist:

Say:
"No events are scheduled."

Do not invent dates or times.

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

    # =====================================
    # STUDENT PERFORMANCE
    # =====================================

    if intent == StudentIntent.STUDENT_PERFORMANCE:

        return f"""
            You are Atlas AI.

            You are performing cross-platform student analysis.

            Use ONLY the supplied data.

            You may use:

            - attendance
            - homework
            - assessments
            - subjects
            - atlas

            Focus primarily on:

            - strengths
            - weaknesses
            - recommended_focus
            - signals
            - atlas pillars
            - attendance risks
            - homework risks
            - assessment risks

            Do NOT invent causes.

            Do NOT create data.

            Do NOT assume trends unless trend data exists.

            If cross_analysis=true:

            Provide:

            1. Overall performance summary
            2. Key strengths
            3. Areas needing improvement
            4. Recommended focus areas
            5. Academic risk indicators (if any)

            Use the supplied strengths,
            weaknesses,
            signals,
            and recommended_focus lists.

            {common}
        """

    # =====================================
    # STUDENT REPORT
    # =====================================

    if intent == StudentIntent.STUDENT_REPORT:

        return f"""
You are Atlas AI.

Provide a complete student report.

Use all available information.

Summarize:

- attendance
- homework
- assessments
- announcements
- atlas performance

Provide:

1. Strengths
2. Areas of concern
3. Recommended next steps

Use only supplied data.

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

    prompt = build_prompt(
        query=query,
        data=data,
        intent=intent
    )

    response = await chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "You are Atlas AI. "
                    "Answer only using supplied data. "
                    "Never invent information."
                )
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