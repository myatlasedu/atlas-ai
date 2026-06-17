import logging

from llm.client import (
    chat_completion
)

from intents.student.schemas import (
    ParsedStudentIntent
)

from intents.student.prompt_selector import (
    build_prompt_for_query
)

from intents.student.prompts import (
    get_student_intent_prompt
)

from intents.student.enums import (
    StudentIntent
)

from intents.base.parser import (
    parse_llm_json
)

from intents.base.fallbacks import (
    build_fallback_student_intent
)

logger = logging.getLogger(__name__)


async def parse_student_intent(
    query: str
) -> ParsedStudentIntent:


    prompt = build_prompt_for_query(
        query=query
    )

    logger.info(
        "PROMPT >>>\n%s",
        prompt
    )

    # prompt = (
    #     get_student_intent_prompt()
    # )

    logger.info(
        "Using intent parser for query: %s",
        query
    )

    response = await chat_completion(
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    content = (
        response["message"]["content"]
    )

    logger.info(
        "RAW MODEL RESPONSE >>> %r",
        content
    )

    try:

        parsed = parse_llm_json(
            content
        )

        logger.info(
            "Parsed intent json: %s",
            parsed
        )

        # =====================================
        # NORMALIZE INTENT STRING
        # =====================================

        intent = (
            str(
                parsed.get(
                    "intent",
                    ""
                )
            )
            .strip()
            .lower()
        )

        # =====================================
        # HEURISTIC NORMALIZATION
        # =====================================

        if "homework" in intent:

            intent = "homework_summary"

        elif (
            "assessment" in intent
            or "exam" in intent
            or "test" in intent
            or "grade" in intent
            or "mark" in intent
        ):

            intent = "assessment_summary"

        elif "attendance" in intent:

            intent = "attendance_summary"

        elif (
            "atlas" in intent
            or intent == "score"
        ):

            intent = "atlas_score_summary"

        elif (
            "performance" in intent
            or "analysis" in intent
        ):

            intent = "student_performance"

        elif "subject" in intent:

            intent = "subject_summary"

        elif "topic" in intent:

            intent = "topic_summary"

        elif "announcement" in intent:

            intent = "announcement_summary"

        elif "forum" in intent:

            intent = "forum_summary"

        elif (
            "journal" in intent
        ):

            if (
                "create" in intent
                or "add" in intent
                or "save" in intent
            ):

                intent = "journal_create"

            else:

                intent = "journal_summary"

        elif (
            "event" in intent
            or "calendar" in intent
            or "schedule" in intent
            or "reminder" in intent
        ):

            if (
                "create" in intent
                or "add" in intent
                or "new" in intent
            ):

                intent = "personal_event_create"

            else:

                intent = "personal_event_summary"

        elif (
            "confirm" in intent
            or "confirmation" in intent
        ):

            intent = "action_confirmation"

        elif (
            "navigation" in intent
            or "navigate" in intent
            or "screen" in intent
        ):

            intent = "screen_navigation"

        # =====================================
        # EXPLICIT NORMALIZATION MAP
        # =====================================

        normalization_map = {

            "event_summary":
                "personal_event_summary",

            "events_summary":
                "personal_event_summary",

            "calendar_summary":
                "personal_event_summary",

            "schedule_summary":
                "personal_event_summary",

            "event_create":
                "personal_event_create",

            "create_event":
                "personal_event_create",

            "calendar_create":
                "personal_event_create",

            "reminder_create":
                "personal_event_create",

            "event_confirmation":
                "action_confirmation",

            "confirm_event":
                "action_confirmation",

            "confirmation":
                "action_confirmation",

            "journal":
                "journal_summary",

            "journal_view":
                "journal_summary",

            "view_journal":
                "journal_summary",

            "show_journal":
                "journal_summary",

            "create_journal":
                "journal_create",

            "journal_entry_create":
                "journal_create",

            "journal_create_entry":
                "journal_create",

            "screen_navigation":
                "screen_navigation",

            "navigation":
                "screen_navigation",

            "navigate":
                "screen_navigation",

            "open_screen":
                "screen_navigation"
        }

        if intent in normalization_map:

            intent = (
                normalization_map[
                    intent
                ]
            )

        parsed["intent"] = intent

        logger.info(
            "Normalized intent: %s",
            intent
        )

        # =====================================
        # NORMALIZATION MAP
        # =====================================

        normalization_map = {

            # -------------------------------
            # HOMEWORK
            # -------------------------------

            "homework":
                "homework_summary",

            "homeworks":
                "homework_summary",

            "show_homework":
                "homework_summary",

            "show_homeworks":
                "homework_summary",

            "pending_homework":
                "homework_summary",

            "homeworks_summary":
                "homework_summary",

            # -------------------------------
            # ATTENDANCE
            # -------------------------------

            "attendance":
                "attendance_summary",

            "show_attendance":
                "attendance_summary",

            "attendance_report":
                "attendance_summary",

            # -------------------------------
            # ASSESSMENTS
            # -------------------------------

            "assessment":
                "assessment_summary",

            "assessments":
                "assessment_summary",

            "show_assessments":
                "assessment_summary",

            "test_summary":
                "assessment_summary",

            "exam_summary":
                "assessment_summary",

            "marks_summary":
                "assessment_summary",

            "grades_summary":
                "assessment_summary",

            # -------------------------------
            # ATLAS
            # -------------------------------

            "atlas":
                "atlas_score_summary",

            "atlas_score":
                "atlas_score_summary",

            "score_summary":
                "atlas_score_summary",

            # -------------------------------
            # PERFORMANCE
            # -------------------------------

            "performance":
                "student_performance",

            "performance_summary":
                "student_performance",

            "student_analysis":
                "student_performance",

            "academic_performance":
                "student_performance",

            # -------------------------------
            # SUBJECTS
            # -------------------------------

            "subject":
                "subject_summary",

            "subjects":
                "subject_summary",

            "show_subjects":
                "subject_summary",

            # -------------------------------
            # TOPICS
            # -------------------------------

            "topic":
                "topic_summary",

            "topics":
                "topic_summary",

            "show_topics":
                "topic_summary",

            # -------------------------------
            # ANNOUNCEMENTS
            # -------------------------------

            "announcement":
                "announcement_summary",

            "announcements":
                "announcement_summary",

            "show_announcements":
                "announcement_summary",

            # -------------------------------
            # FORUM
            # -------------------------------

            "forum":
                "forum_summary",

            "forums":
                "forum_summary",

            "forum_posts":
                "forum_summary",

            # -------------------------------
            # EVENTS
            # -------------------------------

            "event_summary":
                "personal_event_summary",

            "events_summary":
                "personal_event_summary",

            "calendar_summary":
                "personal_event_summary",

            "schedule_summary":
                "personal_event_summary",

            "calendar":
                "personal_event_summary",

            "events":
                "personal_event_summary",

            # -------------------------------
            # EVENT CREATE
            # -------------------------------

            "event_create":
                "personal_event_create",

            "create_event":
                "personal_event_create",

            "calendar_create":
                "personal_event_create",

            "reminder_create":
                "personal_event_create",

            # -------------------------------
            # ACTION CONFIRMATION
            # -------------------------------

            "event_confirmation":
                "action_confirmation",

            "confirm_event":
                "action_confirmation",

            "confirmation":
                "action_confirmation",

            # -------------------------------
            # JOURNAL VIEW
            # -------------------------------

            "journal":
                "journal_summary",

            "journal_view":
                "journal_summary",

            "view_journal":
                "journal_summary",

            "show_journal":
                "journal_summary",

            # -------------------------------
            # JOURNAL CREATE
            # -------------------------------

            "create_journal":
                "journal_create",

            "journal_entry_create":
                "journal_create",

            "journal_create_entry":
                "journal_create"
        }

        if intent in normalization_map:

            intent = (
                normalization_map[
                    intent
                ]
            )

        parsed["intent"] = intent

        logger.info(
            "Normalized intent: %s",
            intent
        )

        # =====================================
        # VALIDATE INTENT
        # =====================================

        valid_intents = {

            item.value
            for item in StudentIntent
        }

        if intent not in valid_intents:

            logger.warning(
                "Unknown intent returned by model: %s",
                intent
            )

            fallback = (
                build_fallback_student_intent()
            )

            fallback[
                "original_query"
            ] = query

            return ParsedStudentIntent(
                **fallback
            )

        # =====================================
        # DEFAULTS
        # =====================================

        parsed.setdefault(
            "target_modules",
            []
        )

        parsed.setdefault(
            "confidence",
            0.95
        )

        parsed[
            "original_query"
        ] = query

        return ParsedStudentIntent(
            **parsed
        )

    except Exception:

        logger.exception(
            "Intent parsing failed"
        )

        fallback = (
            build_fallback_student_intent()
        )

        fallback[
            "original_query"
        ] = query

        return ParsedStudentIntent(
            **fallback
        )