import logging
import re


logger = logging.getLogger(__name__)


#
# Marks, grades and class averages are term results. They are
# released by the school when results are declared, not by the
# assistant.
#
# Mentors are staff who enter and review marks, so the policy
# deliberately does not apply to them.
#

BLOCKED_ROLES = frozenset(
    {
        "student",
        "guardian",
    }
)


RESULTS_PENDING_MESSAGE = (
    "I can't share marks or grades. "
    "You'll get your results when the term results are declared."
)


#
# Only the modules that carry term results are redacted.
# Attendance, Atlas Score and topic or subject strength are not
# results and are left untouched.
#

BLOCKED_MODULES = frozenset(
    {
        "assessment",
        "homework",

        # Republishes assessment marks (marks_obtained, grade,
        # total_marks) under its own module name, so it needs the
        # same treatment. Its trends and focus areas survive.
        "student_performance",
    }
)


#
# Keys removed inside those modules. Scoping by module is what
# makes a plain name like "percentage" or "average" safe to strip:
# attendance keeps its own attendance_percentage, and topic and
# subject keep average_score, because neither module is redacted.
#

BLOCKED_FIELDS = frozenset(
    {
        # raw marks
        "marks_obtained",
        "total_marks",
        "marks",
        "grade",
        "grades",
        "percentage",
        "score",
        "scores",

        # aggregates and class comparisons
        "average",
        "highest",
        "lowest",
        "average_percentage",
        "highest_percentage",
        "lowest_percentage",
        "previous_average",
        "recent_average",
        "class_average",
        "trend_history",

        # whole sections that exist only to report a result
        "titled_mark",
        "latest_result",
        "best_assessment",
        "weakest_assessment",
        "highest_assessment",
        "lowest_assessment",
    }
)


#
# Free-text fields a tool may have already formatted a mark into.
#

TEXT_FIELDS = (
    "direct_answer",
    "headline",
    "confirmation_message",
)


_MARKS_LANGUAGE = re.compile(
    r"\b(grade[ds]?|marks?|scored?|percentage|out of \d+|class average)\b",
    re.IGNORECASE,
)


#
# Tools also write marks into free text - insights, highlights,
# recommended actions. A string inside a blocked module is dropped
# when it carries an actual figure, which is what must never reach
# the student.
#
# Bare counts survive ("3 assignments graded"), because a count is
# not a result.
#

_MARKS_FIGURE = re.compile(
    r"""
      \d+(?:\.\d+)?\s*%                      # 62%, 40.5 %
    | \bout\s+of\s+\d+                       # 45 out of 70
    | \bclass\s+average\b                     # any class comparison
    | \b(?:marks|grades?|scores?|average)\b[^.]{0,40}?\d
    | \d[^.]{0,40}?\b(?:marks|grades?|scores?|average)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _carries_a_figure(
    value: str,
) -> bool:

    return bool(
        _MARKS_FIGURE.search(value)
    )


#
# Intents whose answer IS a term result. A marks question inside
# one of these is answered with the standard message instead of
# being run.
#

RESULT_INTENTS = frozenset(
    {
        "assessment_summary",
        "homework_summary",
    }
)


#
# "score" is also the name of a product feature, so an Atlas
# question must never be mistaken for a marks question.
#

EXEMPT_INTENTS = frozenset(
    {
        "atlas_score_summary",
    }
)


#
# Phrases that can only be a marks question. These are refused
# whatever the classifier decided, because "what is my class
# average" often lands on unknown.
#
# Deliberately narrow: "percentage" alone is not here, or it would
# swallow "what is my attendance percentage".
#

UNAMBIGUOUS_MARKS_PATTERNS = (

    re.compile(r"\bclass average\b", re.IGNORECASE),

    re.compile(r"\bmy (?:marks|grade|grades)\b", re.IGNORECASE),

    re.compile(r"\bhow (?:many|much) (?:marks|did i score)\b", re.IGNORECASE),

    re.compile(r"\bwhat (?:marks|grade)\b", re.IGNORECASE),

    re.compile(r"\bmarks? (?:obtained|scored)\b", re.IGNORECASE),
)


MARKS_KEYWORDS = (
    "marks",
    "mark",
    "grade",
    "grades",
    "score",
    "scores",
    "result",
    "results",
    "percentage",
    "how much did i get",
    "how many marks",
)


def applies(
    role,
) -> bool:

    return (
        str(role or "")
        .strip()
        .lower()
        in BLOCKED_ROLES
    )


def _intent_value(
    intent,
) -> str:

    return (
        str(
            getattr(
                intent,
                "value",
                intent,
            )
            or ""
        )
        .strip()
        .lower()
    )


def is_marks_request(
    *,
    role,
    intent,
    query: str,
    asks_for_marks: bool = False,
) -> bool:

    if not applies(role):

        return False

    intent_value = _intent_value(
        intent
    )

    if intent_value in EXEMPT_INTENTS:

        return False

    lowered = (
        str(query or "")
        .lower()
    )

    if any(
        pattern.search(lowered)
        for pattern in UNAMBIGUOUS_MARKS_PATTERNS
    ):

        return True

    if intent_value not in RESULT_INTENTS:

        return False

    if asks_for_marks:

        return True

    return any(
        keyword in lowered
        for keyword in MARKS_KEYWORDS
    )


def _scrub_text(
    value,
):

    if not isinstance(
        value,
        str,
    ):

        return value

    if _MARKS_LANGUAGE.search(value):

        return RESULTS_PENDING_MESSAGE

    return value


def _redact_value(
    value,
):

    if isinstance(
        value,
        dict,
    ):

        clean = {}

        for key, item in value.items():

            if key in BLOCKED_FIELDS:

                continue

            if key in TEXT_FIELDS:

                clean[key] = _scrub_text(
                    item
                )

                continue

            if (
                isinstance(item, str)
                and _carries_a_figure(item)
            ):

                # A narrative field that quotes a figure.

                continue

            clean[key] = _redact_value(
                item
            )

        return clean

    if isinstance(
        value,
        list,
    ):

        return [
            _redact_value(item)
            for item in value
            if not (
                isinstance(item, str)
                and _carries_a_figure(item)
            )
        ]

    if isinstance(
        value,
        tuple,
    ):

        return tuple(
            _redact_value(item)
            for item in value
        )

    return value


def redact_tool_results(
    *,
    role,
    results: dict,
) -> dict:

    #
    # The single choke point. Runs on the raw tool results, so the
    # same redaction covers the API response body, the summarizer
    # context and the audit record at once - the model can never
    # leak a mark it was never shown.
    #

    if not applies(role):

        return results

    if not isinstance(
        results,
        dict,
    ):

        return results

    redacted = {}

    removed_from = []

    for tool_name, payload in results.items():

        module = (
            payload.get("module")
            if isinstance(payload, dict)
            else None
        )

        if module not in BLOCKED_MODULES:

            redacted[tool_name] = payload

            continue

        redacted[tool_name] = _redact_value(
            payload
        )

        removed_from.append(
            tool_name
        )

    if removed_from:

        logger.info(
            "Marks policy: redacted result fields from %s for role=%s",
            removed_from,
            role,
        )

    return redacted
