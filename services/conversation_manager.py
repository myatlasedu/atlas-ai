import logging
from dataclasses import dataclass

from schemas.conversation import (
    ConversationSession,
)

from utils import (
    is_guardian_context,
)

logger = logging.getLogger(__name__)


CONTEXT_BEARING_INTENTS = {
    "daily_summary",
    "attendance_summary",
    "homework_summary",
    "assessment_summary",
    "atlas_score_summary",
    "announcement_summary",
    "forum_summary",
    "subject_summary",
    "student_performance",
    "student_report",
    "timetable_summary",
    "topic_summary",
    "personal_event_summary",
    "journal_summary",
    "calendar_summary",
    "upcoming_assessments",
    "grading_queue",
    "student_analysis",
    "student_risk",
    "dashboard_summary",
}

INTENT_LABELS = {
    "daily_summary": "Daily Summary",
    "attendance_summary": "Attendance",
    "homework_summary": "Homework",
    "assessment_summary": "Assessments",
    "atlas_score_summary": "Atlas Score",
    "announcement_summary": "Announcements",
    "forum_summary": "Forums",
    "subject_summary": "Subjects",
    "student_performance": "Student Performance",
    "student_report": "Student Reports",
    "timetable_summary": "Timetable",
    "topic_summary": "Topics",
    "personal_event_summary": "Personal Events",
    "journal_summary": "Journal",
    "calendar_summary": "Calendar",
    "upcoming_assessments": "Upcoming Assessments",
    "grading_queue": "Grading Queue",
    "student_analysis": "Student Analysis",
    "student_risk": "Student Risk",
    "dashboard_summary": "Dashboard",
}

_NEUTRAL_INTENTS = {
    "unknown",
    "action_confirmation",
    "screen_navigation",
    "personal_event_create",
    "journal_create",
}

_CONTINUATION_MARKERS = [
    r"\bthat\b",
    r"\bthis\b",
    r"\bit\b",
    r"\bthe other\b",
    r"\bthose\b",
    r"\bsame\b",
    r"\bwhat about\b",
    r"\bhow about\b",
]

_MAX_CONTEXT_CHARS = 1500

_MAX_SUMMARY_CHARS = 200

_MAX_GIST_CHARS = 150


@dataclass
class ConversationResolution:

    session: ConversationSession | None = None

    prior_context: str | None = None

    is_switch: bool = False

    is_continuation: bool = False

    switched_from: str | None = None


def normalize_intent(intent) -> str:

    if intent is None:

        return "unknown"

    if hasattr(intent, "value"):

        return str(intent.value)

    return str(intent)


def label(intent) -> str:

    intent = normalize_intent(intent)

    if not intent or intent == "unknown":

        return "the previous topic"

    return INTENT_LABELS.get(
        intent,
        intent.replace("_", " ").title(),
    )


def _is_followup_query(query: str) -> bool:

    import re

    q = (
        query
        .strip()
        .lower()
    )

    if not q:

        return False

    return any(
        re.search(
            marker,
            q,
        )
        for marker in _CONTINUATION_MARKERS
    )


def _first_sentence(
    text: str,
) -> str:

    text = (
        text
        .strip()
        .replace(
            "\n",
            " ",
        )
    )

    if not text:

        return ""

    split = (
        text
        .split(
            ". ",
            1,
        )
    )

    gist = split[0].strip()

    if not gist:

        return text[:_MAX_GIST_CHARS]

    if not gist.endswith("."):

        gist += "."

    if len(gist) > _MAX_GIST_CHARS:

        gist = gist[:_MAX_GIST_CHARS].rstrip() + "..."

    return gist


def build_prior_context(
    session: ConversationSession,
) -> str:

    if not session or not session.turns:

        return ""

    blocks = []

    total = 0

    for turn in reversed(
        session.turns[-3:]
    ):

        answer = (
            turn.assistant_summary
            or ""
        ).strip()

        gist = _first_sentence(
            answer
        )

        label = (
            INTENT_LABELS.get(
                turn.intent,
                turn.intent.replace("_", " ").title(),
            )
            if turn.intent
            else "Conversation"
        )

        meta = []

        if turn.target_modules:

            meta.append(
                "modules="
                + ", ".join(turn.target_modules)
            )

        if (
            turn.start_date
            or
            turn.end_date
        ):

            meta.append(
                f"dates={turn.start_date}"
                f"{' / ' if turn.start_date and turn.end_date else ''}"
                f"{turn.end_date or ''}"
            )

        block = f"{label}: {gist}"

        if meta:

            block += " [" + "; ".join(meta) + "]"

        total += len(block)

        if total > _MAX_CONTEXT_CHARS:

            break

        blocks.append(block)

    if not blocks:

        return ""

    return "PRIOR CONVERSATION\n" + "\n".join(
        reversed(blocks)
    )


def conversation_scope_key(context):

    from cache.conversation_cache import ConversationCache

    role = getattr(
        context,
        "role",
        None,
    )

    if is_guardian_context(context):

        student_id = getattr(
            context,
            "student_id",
            None,
        )

        if student_id is None:

            logger.warning(
                "Guardian context missing student_id - skipping conversation"
            )

            return None

    return ConversationCache.scope_key(context)


async def resolve(
    context,
    parsed_intent,
    query: str,
    session=None,
) -> ConversationResolution:

    intent = normalize_intent(
        getattr(
            parsed_intent,
            "intent",
            "unknown",
        )
    )

    scope_key = conversation_scope_key(context)

    if scope_key is None:

        return ConversationResolution()

    if session is None:

        session = await _get_session(
            scope_key,
        )

    # ------------------------------------------------------
    # CONTINUATION FALLBACK
    #
    # Classifier said UNKNOWN but we are mid-conversation and
    # the query looks like a follow-up. Continue the current
    # intent with prior context instead of showing the help menu.
    # ------------------------------------------------------

    if (
        intent == "unknown"
        and
        not getattr(
            parsed_intent,
            "is_injection",
            False,
        )
        and
        not getattr(
            parsed_intent,
            "generate_content",
            False,
        )
        and
        session is not None
        and
        session.current_intent
        and
        _is_followup_query(query)
    ):

        logger.info(
            "UNKNOWN follow-up detected - continuing intent %s",
            session.current_intent,
        )

        return ConversationResolution(
            session=session,
            prior_context=build_prior_context(session),
            is_continuation=True,
        )

    if intent in _NEUTRAL_INTENTS:

        return ConversationResolution()

    if (
        session is not None
        and
        session.current_intent
        and
        session.current_intent != intent
    ):

        switched_from = (
            session.current_intent
        )

        await _delete_session(
            scope_key,
        )

        logger.info(
            "Intent switched from %s to %s - session reset",
            switched_from,
            intent,
        )

        return ConversationResolution(
            session=_new_session(
                context,
                intent,
            ),
            is_switch=True,
            switched_from=switched_from,
        )

    if session is None:

        session = _new_session(
            context,
            intent,
        )

        return ConversationResolution(
            session=session,
            prior_context=None,
        )

    return ConversationResolution(
        session=session,
        prior_context=build_prior_context(session),
    )


def _new_session(
    context,
    intent: str,
) -> ConversationSession:

    from datetime import datetime

    from utils import (
        ist_now,
    )

    return ConversationSession(
        user_id=getattr(
            context,
            "user_id",
            0,
        ),
        role=getattr(
            context,
            "role",
            "student",
        ),
        student_id=getattr(
            context,
            "student_id",
            None,
        ),
        current_intent=intent,
        created_at=ist_now(),
    )


async def _get_session(
    scope_key: str,
):

    from cache.conversation_cache import ConversationCache

    return await ConversationCache.get(
        scope_key
    )


async def _delete_session(
    scope_key: str,
):

    from cache.conversation_cache import ConversationCache

    await ConversationCache.delete(
        scope_key
    )
