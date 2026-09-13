"""
Conversation context for intent parsing.

The last few answered turns (query + intent) are replayed into the
classifier so a follow-up query can be resolved against the turn it
actually refers to, while a self-contained query keeps its own intent.
"""

import logging

from schemas.conversation import (
    ConversationTurn,
)


logger = logging.getLogger(__name__)


MAX_CONTEXT_TURNS = 5


# Fields a follow-up may inherit from the turn it refers to.
# The current query always wins; inheritance only fills blanks.

INHERITABLE_FIELDS = (
    "topic",
    "subject",
    "teacher",
    "homework_focus",
    "navigation_target",
)


# ==================================================
# PROMPT SECTIONS
# ==================================================

CONTEXT_RULES = """
==================================================
CONVERSATION CONTEXT
==================================================

You are given the user's RECENT CONVERSATION
(most recent first) and the CURRENT QUERY.

Work in three steps.

STEP 1 - decide whether the CURRENT QUERY is a
follow-up.

STEP 2 - rewrite it into a self-contained
resolved_query.

STEP 3 - classify the resolved_query.

Never answer any query.

Never classify a recent query.

==================================================
THE CURRENT QUERY ALWAYS WINS
==================================================

The recent conversation may only ADD what the
CURRENT QUERY left unsaid.

It may NEVER drop, replace or contradict anything
the CURRENT QUERY states.

If the CURRENT QUERY names its own module, subject,
person or time window, that value is final.

--------------------------------------------------

STEP 1 - is_follow_up

true when the CURRENT QUERY cannot be understood on
its own and continues the recent conversation.

Signals:

- pronouns with no subject
  ("what about it", "show them", "that one")

- a bare filter or time window
  ("and last week?", "what about this month?",
   "for Maths", "only pending")

- a continuation word
  ("also", "then", "more", "same for", "what else")

false when the CURRENT QUERY is complete on its own,
even if a recent turn was about something else.

--------------------------------------------------

STEP 2 - resolved_query

If is_follow_up is false:

resolved_query is the CURRENT QUERY, copied word for
word. Change nothing.

If is_follow_up is true:

Rewrite the CURRENT QUERY into one complete question
by borrowing ONLY the missing parts (the module, the
subject, the person) from the recent turn it follows
up on.

Keep every detail the CURRENT QUERY states - above
all its time window.

Keep it short and natural, in the user's own words.

Example 1

recent: "Show me the homework of last month"
         (homework_summary)
current: "What about this month?"

-> is_follow_up: true
-> resolved_query: "Show me the homework for this month"

The module (homework) is borrowed.
The time window (this month) is the current
query's own and must survive.

Example 2

recent: "Show me the homework of last month"
         (homework_summary)
current: "What about my attendance last month?"

-> is_follow_up: false
-> resolved_query: "What about my attendance last month?"

The current query already names its module and its
time window, so nothing is borrowed.

Example 3

recent: "How was my attendance in July"
         (attendance_summary)
current: "and August?"

-> is_follow_up: true
-> resolved_query: "How was my attendance in August"

Example 4

recent: "Show attendance of that month"
        (attendance_summary)

before recent: "Show homework of July month"
               (homework_summary)

current: "What's about this month?"

-> is_follow_up: true
-> resolved_query: "Show my attendance of this month"
-> context_turn: <recent attendance turn number>

The current query is a follow-up to the attendance turn
because "this month" is a time-window filter that can be
applied to the attendance subject.

The older homework turn is not followed because its subject
matter is different.

The time window "this month" comes from the CURRENT QUERY
and must be preserved.

--------------------------------------------------

STEP 3 - intent

Classify the resolved_query using the intent
definitions above.

A follow-up therefore lands on the intent of the
turn it continues, and a stand-alone query keeps
its own intent.

--------------------------------------------------

CHOOSING THE TURN TO FOLLOW

The recent turns may have different intents.

Follow the recent turn whose SUBJECT MATTER is
closest to the CURRENT QUERY, not simply the newest
one.

If the CURRENT QUERY fits two recent turns with
DIFFERENT intents equally well, follow the MORE
RECENT turn.

Report that turn's number as context_turn.

==================================================
OUTPUT (overrides any earlier output format)
==================================================

Return ONLY

{
    "is_follow_up": true or false,
    "resolved_query": "<self-contained query>",
    "intent": "<one_of_the_allowed_intents>",
    "context_turn": <number of the turn followed, or null>
}

Set context_turn to null when is_follow_up is false.
"""


# ==================================================
# FOLLOW-UP DETECTION
# ==================================================

# Words that only make sense against something already asked.

FOLLOW_UP_MARKERS = (
    "what about",
    "how about",
    "what if",
    "and what",
    "same for",
    "same in",
    "instead",
    "also",
    "as well",
    "too",
    "else",
    "more",
    "again",
    "that one",
    "those",
    "them",
    "it",
    "its",
    "this one",
    "the same",
    "previous",
    "earlier",
    "last one",
    "next one",
)


MAX_FOLLOW_UP_WORDS = 6


def is_follow_up_query(
    query: str,
) -> bool:

    # Deterministic safety net for RULE 1: used only when the
    # classifier could not place the query on its own.

    normalized = (
        query
        .strip()
        .lower()
        .strip("?!.")
    )

    if not normalized:

        return False

    if normalized.startswith(
        (
            "and ",
            "or ",
            "but ",
            "then ",
            "also ",
            "what about",
            "how about",
        )
    ):

        return True

    words = normalized.split()

    if len(words) <= MAX_FOLLOW_UP_WORDS:

        # Short queries are the ones that lean on context; a longer
        # sentence carries enough of its own subject to stand alone.

        return any(
            marker in normalized
            if " " in marker
            else marker in words
            for marker in FOLLOW_UP_MARKERS
        ) or len(words) <= 3

    return False


# ==================================================
# HISTORY RENDERING
# ==================================================


def turn_text(
    turn: ConversationTurn,
) -> str:

    # A turn that was itself a follow-up was answered as its resolved
    # query; replay that, so a chain of follow-ups keeps its subject.

    parsed = turn.parsed_intent or {}

    if isinstance(
        parsed,
        dict,
    ):

        resolved = parsed.get(
            "original_query"
        )

        if resolved and str(resolved).strip():

            return str(resolved).strip()

    return turn.query.strip()


def _turn_line(
    position: int,
    turn: ConversationTurn,
) -> str:

    parsed = turn.parsed_intent or {}

    details = []

    for field in (
        "topic",
        "subject",
        "homework_focus",
    ):

        value = parsed.get(
            field
        )

        if value:

            details.append(
                f"{field}={value}"
            )

    suffix = (
        f" | {', '.join(details)}"
        if details
        else ""
    )

    return (
        f"{position}. query: \"{turn_text(turn)}\""
        f" | intent: {turn.predicted_intent}"
        f"{suffix}"
    )


def build_history_block(
    turns: list[ConversationTurn],
) -> str:

    # Newest first: turn 1 is the immediately preceding query.

    if not turns:

        return ""

    lines = [
        _turn_line(
            position,
            turn,
        )
        for position, turn in enumerate(
            turns[:MAX_CONTEXT_TURNS],
            start=1,
        )
    ]

    return (
        "==================================================\n"
        "RECENT CONVERSATION (most recent first)\n"
        "==================================================\n\n"
        + "\n".join(lines)
    )


def build_classifier_messages(
    *,
    base_prompt: str,
    query: str,
    turns: list[ConversationTurn] | None,
) -> list[dict]:

    # No history -> keep the original single-query contract untouched.

    if not turns:

        return [
            {
                "role": "system",
                "content": base_prompt,
            },
            {
                "role": "user",
                "content": query,
            },
        ]

    return [
        {
            "role": "system",
            "content": (
                f"{base_prompt}\n{CONTEXT_RULES}"
            ),
        },
        {
            "role": "user",
            "content": (
                f"{build_history_block(turns)}\n\n"
                "==================================================\n"
                "CURRENT QUERY\n"
                "==================================================\n\n"
                f"{query}"
            ),
        },
    ]


def resolve_context_turn(
    *,
    turns: list[ConversationTurn] | None,
    context_turn,
) -> ConversationTurn | None:

    # The classifier answers with a 1-based position into the
    # history block it was shown; map it back to the real turn.

    if not turns or context_turn in (None, "", "null"):

        return None

    try:

        position = int(
            context_turn
        )

    except (
        TypeError,
        ValueError,
    ):

        logger.warning(
            "Classifier returned a non-numeric context_turn: %r",
            context_turn,
        )

        return None

    if not 1 <= position <= len(turns[:MAX_CONTEXT_TURNS]):

        logger.warning(
            "Classifier referenced an out-of-range turn: %r",
            context_turn,
        )

        return None

    return turns[position - 1]


# ==================================================
# PARAMETER INHERITANCE
# ==================================================


def inherit_parameters(
    parsed: dict,
    source_turn: ConversationTurn | None,
) -> dict:

    # A follow-up carries its own words only ("and last week?");
    # everything it left unsaid comes from the turn it refers to.

    if not source_turn:

        return parsed

    previous = source_turn.parsed_intent or {}

    if not isinstance(
        previous,
        dict,
    ):

        return parsed

    # Only inherit inside the same intent: a screen_navigation
    # target must never leak into a homework answer.

    if (
        str(previous.get("intent", ""))
        !=
        str(parsed.get("intent", ""))
    ):

        return parsed

    for field in INHERITABLE_FIELDS:

        if not parsed.get(field) and previous.get(field):

            parsed[field] = previous[field]

            logger.info(
                "Inherited %s=%r from turn %s.",
                field,
                previous[field],
                source_turn.turn_id,
            )

    if not parsed.get("target_modules") and previous.get("target_modules"):

        parsed["target_modules"] = list(
            previous["target_modules"]
        )

    # Dates travel as a pair; a follow-up that names its own
    # window ("and August?") already overrode both.

    if (
        not parsed.get("start_date")
        and
        not parsed.get("end_date")
        and
        previous.get("start_date")
    ):

        parsed["start_date"] = previous.get("start_date")

        parsed["end_date"] = previous.get("end_date")

        logger.info(
            "Inherited date window %s -> %s from turn %s.",
            parsed["start_date"],
            parsed["end_date"],
            source_turn.turn_id,
        )

    return parsed


# ==================================================
# RESOLVED QUERY
# ==================================================


def resolve_followup_query(
    *,
    query: str,
    resolved_query,
    is_follow_up: bool,
    context_turn: ConversationTurn | None,
) -> str:

    # The rewrite is only ever allowed to ADD context. Anything that
    # looks like the model answering a different question falls back
    # to the user's own words.

    if not is_follow_up:

        return query

    candidate = str(
        resolved_query
        or ""
    ).strip()

    if not candidate:

        return query

    # A rewrite that merely echoes the turn being followed has dropped
    # the current query entirely ("what about this month?" ->
    # "show me the homework of last month").

    if context_turn and _same_text(
        candidate,
        turn_text(context_turn),
    ):

        logger.warning(
            "Discarding echoed rewrite of turn %s: %r",
            context_turn.turn_id,
            candidate,
        )

        return query

    # A rewrite should stay a short question; a runaway answer is not one.

    if len(candidate) > max(
        len(query) * 4,
        160,
    ):

        logger.warning(
            "Discarding oversized rewrite: %r",
            candidate,
        )

        return query

    if candidate != query:

        logger.info(
            "Resolved follow-up %r -> %r",
            query,
            candidate,
        )

    return candidate


def _same_text(
    left: str,
    right: str,
) -> bool:

    return (
        left.strip().lower().strip("?!. ")
        ==
        right.strip().lower().strip("?!. ")
    )


# ==================================================
# CLASSIFIER RESULT
# ==================================================


class IntentClassification:

    # Classifier answer: the intent, the self-contained query it was
    # classified from, and the recent turn it followed (if any).

    __slots__ = (
        "intent",
        "context_turn",
        "resolved_query",
        "is_follow_up",
    )

    def __init__(
        self,
        intent,
        context_turn: ConversationTurn | None = None,
        resolved_query: str = "",
        is_follow_up: bool = False,
    ):

        self.intent = intent

        self.context_turn = context_turn

        self.resolved_query = resolved_query

        self.is_follow_up = is_follow_up

    def __iter__(self):

        # Allows: intent, source_turn = classification

        yield self.intent

        yield self.context_turn

    def __repr__(self):

        return (
            "IntentClassification("
            f"intent={self.intent!r}, "
            f"is_follow_up={self.is_follow_up!r}, "
            f"resolved_query={self.resolved_query!r}, "
            "context_turn="
            f"{self.context_turn.turn_id if self.context_turn else None})"
        )
