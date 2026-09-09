"""
Marks privacy.

Marks, grades, scores and percentages derived from a student's academic
performance are never disclosed to a student or guardian. Whenever a result
exists, the only thing we say about it is that it is GRADED.

This module is the single place that decides:

- the wording used in place of a mark (GRADED_LABEL / the message constants),
- which payload fields carry mark values (MARK_VALUE_KEYS),
- how to strip mark values out of structured data (redact_mark_fields),
- how to scrub mark values out of free text, including anything the LLM
  writes (redact_marks_text).

The Atlas score is an engagement index rather than an academic mark, so it is
deliberately not covered here.
"""

import re


GRADED_LABEL = "GRADED"

REPORT_CARD_NOTE = (
    "Your grade will be available on the report card."
)

GUARDIAN_REPORT_CARD_NOTE = (
    "The grade will be available on the report card."
)

# Plural forms, for answers that list more than one graded item.

REPORT_CARD_NOTE_PLURAL = (
    "Your grades will be available on the report card."
)

GUARDIAN_REPORT_CARD_NOTE_PLURAL = (
    "The grades will be available on the report card."
)

# The one sentence used whenever someone asks for marks, grades, scorecards
# or results. Keep every user-facing answer going through graded_message() so
# the wording stays identical across tools, builders and prompts.

GRADED_MESSAGE_TEMPLATE = (
    "{owner}{title}{kind} has been Graded. {note}"
)

RESULTS_WITHHELD_MESSAGE = (
    "Marks, grades and performance details aren't shared here. "
    f"{REPORT_CARD_NOTE_PLURAL}"
)


# Deliberately free of the words the verdict patterns look for ("average",
# "trend", "ranking"), so the message survives its own scrubber.

PERFORMANCE_WITHHELD_NOTE = (
    "Performance details aren't shared here."
)


def performance_withheld_message(role: str = "student") -> str:
    """
    The reply for a question about performance rather than a specific result.

    Averages, trends, consistency, rankings and "needs attention" verdicts are
    all read off the student's marks, so they are withheld just like the marks.
    """

    note = (
        GUARDIAN_REPORT_CARD_NOTE_PLURAL
        if role == "guardian"
        else REPORT_CARD_NOTE_PLURAL
    )

    return f"{PERFORMANCE_WITHHELD_NOTE} {note}"


def graded_message(
    title=None,
    kind: str = "assessment",
    role: str = "student",
) -> str:
    """
    The standard reply for a request for marks, grades, scorecards or results.

    Example:

        "Your Physics Test 1 assessment has been Graded. Your grade will be
        available on the report card."
    """

    owner = (
        "The student's "
        if role == "guardian"
        else "Your "
    )

    note = (
        GUARDIAN_REPORT_CARD_NOTE
        if role == "guardian"
        else REPORT_CARD_NOTE
    )

    name = str(title or "").strip()

    return GRADED_MESSAGE_TEMPLATE.format(
        owner=owner,
        title=f"{name} " if name else "",
        kind=kind,
        note=note,
    )


# Payload keys whose values are, or are derived from, a student's marks.
# `grade` is handled separately: it is rewritten to GRADED rather than dropped,
# because its presence is what tells us a result exists.

MARK_VALUE_KEYS = frozenset({
    "marks_obtained",
    "total_marks",
    "marks",
    "percentage",
    "average_percentage",
    "highest_percentage",
    "lowest_percentage",
    "previous_average",
    "recent_average",
    "score",
    "average_score",
    "highest_score",
    "lowest_score",
    "homework_average",
    "assessment_average",
    "subject_average",
    "scores",
    "average",
    "highest",
    "lowest",
    "range",
    "std_dev",
})

GRADE_KEYS = frozenset({
    "grade",
    "grades",
})

# Identifiers and labels are copied through untouched. Scrubbing them would
# mangle titles like "Chapter 1/2 Review" for no privacy gain.

PRESERVED_TEXT_KEYS = frozenset({
    "id",
    "module",
    "title",
    "type",
    "state",
    "status",
    "status_tag",
    "focus",
    "rating",
    "direction",
    "risk_level",
    "subject",
    "subject_name",
    "topic",
    "topic_name",
    "teacher",
    "teacher_name",
    "due_date",
    "assessment_date",
    "submitted_at",
    "reviewed_at",
    "graded_at",
    "error",
})


def has_grade(value) -> bool:
    """True when a grade value is actually present (and not already redacted)."""

    text = str(value or "").strip()

    return bool(text) and text != GRADED_LABEL


def is_graded(value) -> bool:
    """
    True when a result exists, whether or not it has already been redacted.

    Use this downstream of redact_mark_fields, where a real grade has already
    been flattened to GRADED and has_grade() would report False.
    """

    return bool(str(value or "").strip())


def redact_mark_fields(value, key=None):
    """
    Recursively remove mark values from a payload.

    Mark-bearing keys are dropped entirely; grade keys are kept but flattened to
    GRADED so downstream code can still tell that a result exists. Free text -
    teacher comments, pre-composed narrative lines - is scrubbed, while
    identifiers and titles are copied through untouched.
    """

    if isinstance(value, dict):

        cleaned = {}

        for item_key, item in value.items():

            lowered = str(item_key).lower()

            if lowered in MARK_VALUE_KEYS:
                continue

            if lowered in GRADE_KEYS:

                if has_grade(item):
                    cleaned[item_key] = GRADED_LABEL

                else:
                    cleaned[item_key] = None

                continue

            cleaned[item_key] = redact_mark_fields(item, lowered)

        return cleaned

    if isinstance(value, list):
        return [redact_mark_fields(item, key) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_mark_fields(item, key) for item in value)

    if isinstance(value, str):

        if key in PRESERVED_TEXT_KEYS:
            return value

        return redact_marks_text(value, fallback="")

    return value


# ---------------------------------------------------------------------------
# Free-text scrubbing
# ---------------------------------------------------------------------------

# Sentences that compare a student against a numeric threshold leak the mark
# even without quoting it, so they are dropped whole rather than patched.

_LEAK_SENTENCE_PATTERNS = (
    # "your average is 72.5", "highest was 91" - a bare number attached to a
    # ranking word. The number must follow a linking word, so titles that
    # happen to contain a digit ("Physics Test 1") are left alone.
    re.compile(
        r"\b(?:average|averaging|mean|highest|lowest|best|weakest|top|worst)\b"
        r"[^.!?\n]{0,40}?\b(?:is|was|of|at|:|-)\s*\d{1,3}(?:\.\d+)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:scored|achieved|obtained|earned)\b\s*(?:a|an|the)?\s*\d",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:above|below|under|over|more than|less than|at least|up to)\b"
        r"[^.!?\n]{0,20}?\d{1,3}\s*(?:%|percent|marks|points)",
        re.IGNORECASE,
    ),
)

# Performance verdicts are read off the same marks: an overall status, a
# trend, an average, a ranking or a "needs attention" flag tells the reader
# how the student scored without quoting a number. Sentences carrying one are
# dropped whole - there is no value to swap out.

_PERFORMANCE_VERDICT_PATTERNS = (
    re.compile(r"\b(?:below|above)\s+target\b", re.IGNORECASE),
    re.compile(r"\bneed(?:s|ing)?\s+attention\b", re.IGNORECASE),
    re.compile(r"\b(?:at|high)[\s-]risk\b", re.IGNORECASE),
    re.compile(
        r"\b(?:declining|improving|deteriorating|worsening|slipping|dropping)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:strongest|weakest|best|worst|top|highest[\s-]scoring|"
        r"lowest[\s-]scoring)\s+(?:\w+\s+)?"
        r"(?:assessment|subject|topic|area|result|performance)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:performance|progress|standing|status|results?|trend)\b"
        r"[^.!?\n]{0,40}?\b(?:critical|poor|good|excellent|moderate|strong|"
        r"weak|healthy|below|above|declining|improving)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bconsisten(?:t|cy|tly)\b", re.IGNORECASE),
    re.compile(r"\baverages?\b", re.IGNORECASE),
    re.compile(
        r"\b(?:doing|performing)\s+(?:very\s+)?(?:well|badly|poorly|great|fine)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:struggling|excelling|underperforming|falling\s+behind)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bweak\s+(?:assessment|subject|topic|area)",
        re.IGNORECASE,
    ),
)

# Individual mark values that can simply be swapped for GRADED. Each pattern
# keeps whatever leads up to the value in group 1 so only the value is replaced.

_MARK_VALUE_PATTERNS = (
    # 42/50, 42 out of 50
    re.compile(
        r"()\b\d{1,4}(?:\.\d+)?\s*(?:/|out\s+of)\s*\d{1,4}(?:\.\d+)?\b",
        re.IGNORECASE,
    ),
    # 84%, 84.5 percent
    re.compile(
        r"()\b\d{1,3}(?:\.\d+)?\s*(?:%|per\s?cent\b|percent\b)",
        re.IGNORECASE,
    ),
    # grade A, Grade: B, graded A*
    re.compile(
        r"((?i:grade[ds]?)\b(?:[^.!?\n]{0,30}?\b(?:is|was|of)\b|\s*[:\-])?\s*)"
        r"[\"']?(?:A\*|[A-EU])(?![\w*])[\"']?",
    ),
    # marks: 42, score of 91
    re.compile(
        r"(\b(?:marks?|scores?|points?)\b\s*(?:of|is|was|were|are|:|-)?\s*)"
        r"\d{1,4}(?:\.\d+)?\b",
        re.IGNORECASE,
    ),
)

# Attendance percentages and the Atlas engagement score are legitimate numbers
# that happen to look like marks, so sentences about them are left alone.

_EXEMPT_CONTEXT = re.compile(
    r"\b(?:attendance|attended|attending|present|presence|absent|absence|"
    r"absences|punctual|punctuality|atlas)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# Leading bullet/number markers, so a list item survives scrubbing as a row.
_LIST_PREFIX = re.compile(r"^(\s*(?:[>*\-•–—]+|\d{1,2}[.)])?\s*)")

# "GRADED (GRADED)" and "GRADED - GRADED" both collapse to a single label.

_BRACKETED_LABEL = re.compile(
    rf"{GRADED_LABEL}\s*[\(\[]\s*{GRADED_LABEL}\s*[\)\]]"
)

_REPEATED_LABEL = re.compile(
    rf"{GRADED_LABEL}(?:[\s,;:/\-–—]*{GRADED_LABEL})+"
)

# "grade GRADED" / "Grade: GRADED" read better as just "GRADED".

_REDUNDANT_GRADE_WORD = re.compile(
    rf"\b(?i:grade[ds]?)\b\s*[:\-]?\s*(?={GRADED_LABEL}\b)"
)

_EMPTY_BRACKETS = re.compile(r"\(\s*\)|\[\s*\]")

_LOOSE_PUNCTUATION = re.compile(r"\s+([,.;:!?])")

_REPEATED_SPACES = re.compile(r"[ \t]{2,}")


def _is_exempt(sentence: str) -> bool:

    return bool(_EXEMPT_CONTEXT.search(sentence))


def contains_marks(text) -> bool:
    """True when the text quotes a mark, grade, score or percentage."""

    if not text:
        return False

    for line in str(text).split("\n"):

        for sentence in _SENTENCE_SPLIT.split(line):

            if _is_exempt(sentence):
                continue

            if any(
                pattern.search(sentence)
                for pattern in (
                    _LEAK_SENTENCE_PATTERNS
                    + _PERFORMANCE_VERDICT_PATTERNS
                    + _MARK_VALUE_PATTERNS
                )
            ):
                return True

    return False


def _tidy(line: str) -> str:

    line = _REDUNDANT_GRADE_WORD.sub("", line)
    line = _BRACKETED_LABEL.sub(GRADED_LABEL, line)
    line = _REPEATED_LABEL.sub(GRADED_LABEL, line)
    line = _EMPTY_BRACKETS.sub("", line)
    line = _LOOSE_PUNCTUATION.sub(r"\1", line)
    line = _REPEATED_SPACES.sub(" ", line)

    return line.strip()


def _scrub_line(line: str) -> str:

    kept = []

    for sentence in _SENTENCE_SPLIT.split(line):

        if _is_exempt(sentence):
            kept.append(sentence)
            continue

        if any(
            pattern.search(sentence)
            for pattern in (
                _LEAK_SENTENCE_PATTERNS
                + _PERFORMANCE_VERDICT_PATTERNS
            )
        ):
            continue

        for pattern in _MARK_VALUE_PATTERNS:
            sentence = pattern.sub(
                rf"\g<1>{GRADED_LABEL}",
                sentence,
            )

        kept.append(sentence)

    return _tidy(" ".join(kept))


def redact_marks_text(text, fallback: str | None = None):
    """
    Scrub marks out of free text.

    Sentences that compare against a numeric threshold are dropped; quoted mark
    values are replaced with GRADED. List structure is preserved so a graded
    item still shows up, just without its value. Returns `fallback` when nothing
    usable survives.
    """

    if not text:
        return text

    original = str(text)

    if not contains_marks(original):
        return original

    output = []

    for line in original.split("\n"):

        if not line.strip():
            output.append(line)
            continue

        prefix_match = _LIST_PREFIX.match(line)
        prefix = prefix_match.group(1) if prefix_match else ""
        body = line[len(prefix):]

        scrubbed = _scrub_line(body)

        if not scrubbed:

            # A bullet emptied by scrubbing still exists as a graded item.
            if prefix.strip():
                output.append(f"{prefix}{GRADED_LABEL}")

            continue

        output.append(f"{prefix}{scrubbed}")

    result = "\n".join(output).strip()

    if not result:
        return fallback if fallback is not None else RESULTS_WITHHELD_MESSAGE

    return result


# Payload keys whose values are free text shown to, or summarized for, the user.

TEXT_KEYS = (
    "direct_answer",
)


def redact_tool_payload(payload):
    """
    Strip marks out of a tool payload before it leaves the tool.

    Mark values are dropped from the structured data and any user-facing text
    the tool has already composed is scrubbed, so neither a direct answer nor
    the LLM context can carry a mark, grade, score or percentage.
    """

    if not isinstance(payload, dict):
        return payload

    cleaned = redact_mark_fields(payload)

    # User-facing text is re-scrubbed from the original so that a line made up
    # entirely of marks becomes the withheld message rather than an empty string.

    for key in TEXT_KEYS:

        original = payload.get(key)

        if isinstance(original, str):

            cleaned[key] = redact_marks_text(
                original,
                fallback=RESULTS_WITHHELD_MESSAGE,
            )

    original_context = payload.get("llm_context")

    if (
        isinstance(original_context, dict)
        and isinstance(cleaned.get("llm_context"), dict)
    ):

        for key, value in original_context.items():

            if isinstance(value, str):

                cleaned["llm_context"][key] = redact_marks_text(
                    value,
                    fallback=RESULTS_WITHHELD_MESSAGE,
                )

    return cleaned
