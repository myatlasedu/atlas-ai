RESOURCE_PROMPT = """
--------------------------------------------------

resource_summary

Used when the student asks whether or where study
material exists for a subject or topic:

- supplementary sheet
- supplementary sheets
- worksheet
- worksheets
- notes
- study notes
- study material
- revision sheet
- revision notes
- learning resources
- resources
- reading material
- quiz
- reference link

Examples:

- Is there any supplementary sheet for Spanish?
- Is there a worksheet for Maths?
- Do you have revision notes for Science?
- Are there any study materials for Geography?
- Show my resources for English
- Is there a quiz for this topic?

==================================================
RESOURCE RULES
==================================================

Only extract "subject" when the student names a
subject, using the same SUBJECT FILTER rules as the
homework intent (keep the full subject name).

Only extract "topic" when the student names a
specific topic, chapter or learning objective.

Leave both null when no subject or topic is named.

Do NOT set "topic" to "supplementary sheet",
"worksheet" or any generic material word. "topic"
is only a named chapter / topic / learning
objective.

Do NOT set "asks_for_marks" for these queries.

==================================================
NOT HOMEWORK
==================================================

A question about marks or grades for a specific
titled homework or worksheet is homework_summary,
NOT resource_summary.

A question that only asks whether study material
exists is resource_summary.

==================================================
TARGET MODULES
==================================================

resource_summary

[
    "resource"
]
"""
