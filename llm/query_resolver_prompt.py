import json

from intents.student.classifier_prompt import (
    CLASSIFIER_PROMPT,
)

from schemas.conversation import (
    SAME_INTENT_INHERITABLE_PARAMETERS,
)


def _intent_catalogue() -> str:

    #
    # Reuse the classifier's own taxonomy rather than keeping a
    # second copy in sync. Everything between its INTENTS heading
    # and its closing OUTPUT block is the catalogue and the
    # disambiguation rules; the surrounding wrapper is the
    # classifier's own job description, which does not apply here.
    #

    separator = "=" * 50

    start = CLASSIFIER_PROMPT.find(
        f"{separator}\nINTENTS"
    )

    end = CLASSIFIER_PROMPT.rfind(
        f"{separator}\nOUTPUT"
    )

    if start == -1 or end <= start:

        # Prompt was restructured: fall back to the whole thing
        # rather than silently dropping the taxonomy.

        return CLASSIFIER_PROMPT.strip()

    return CLASSIFIER_PROMPT[start:end].strip()


INTENT_CATALOGUE = _intent_catalogue()


def build_query_resolver_prompt(
    *,
    role: str,
    allowed_intents: list[str],
    today: str,
    timezone_name: str,
) -> str:

    intents_block = "\n".join(
        f"- {intent}"
        for intent in allowed_intents
    )

    parameters_block = "\n".join(
        f"- {name}"
        for name in SAME_INTENT_INHERITABLE_PARAMETERS
    )

    return f"""
You are Atlas AI's conversational query resolver and intent
classifier for the {role} assistant.

You do TWO things in one pass:

1. Rewrite the user's LATEST message into a STANDALONE query,
   using the recent conversation only when the latest message
   cannot stand on its own.

2. Decide the intent of that standalone query - either the
   intent of the turn it continues, or a fresh one from the
   catalogue below.

Do NOT answer the question.
Do NOT invent facts, subjects, names or dates that are absent
from the conversation.
Do NOT explain your reasoning outside the JSON.
Return ONLY valid JSON. Never use markdown.

==================================================
TODAY
==================================================

Today is {today} in the user's timezone ({timezone_name}).

Resolve every relative date against THIS date and THIS
timezone. Never invent another year.

==================================================
ALLOWED INTENT VALUES
==================================================

{intents_block}

{INTENT_CATALOGUE}

==================================================
ALLOWED PARAMETERS
==================================================

{parameters_block}

Dates use ISO format (YYYY-MM-DD).
target_modules is a list of strings.
asks_for_marks and late_only are booleans.
Omit any parameter you have no evidence for. Never guess.

==================================================
OUTPUT
==================================================

Return EXACTLY this shape:

{{
  "resolved_query": "<standalone version of the latest message>",
  "intent": "<an intent from the catalogue - required>",
  "parameters": {{}},
  "context_used": {{
    "used": true,
    "turn_ids": [1],
    "inherited_fields": ["intent", "subject"],
    "reason": "<one short sentence>"
  }},
  "clarification_required": {{
    "required": false,
    "question": null,
    "reason": null
  }}
}}

==================================================
RULES
==================================================

1. SELF-CONTAINED MESSAGES

If the latest message already makes sense on its own, copy it
into resolved_query unchanged, set "intent" to null, leave
"parameters" empty and set context_used.used to false.

A message that names its own subject AND its own topic is
self-contained even if it resembles the previous turn.

2. CONTEXTUAL MESSAGES

A message is contextual when it:

- is a fragment ("what about this month?", "and last week?")
- uses a pronoun or a demonstrative with no antecedent
  ("what about that one?", "show me those", "and hers?")
- changes only one detail of the previous question
  ("same for Physics", "only the pending ones")
- asks for more of the same ("any others?", "show more")

For a contextual message, rewrite it as a full question by
borrowing the missing pieces from the most recent relevant
turn, and list every borrowed field in
context_used.inherited_fields.

3. INTENT

You MUST always return an intent from the INTENT CATALOGUE.
The only time "intent" may be null is when you are asking for
clarification.

Choose it like this:

- If the message continues the previous topic (a fragment, one
  changed detail, a pronoun pointing at the last answer), reuse
  the intent of the turn it continues and list "intent" in
  context_used.inherited_fields.

- Otherwise classify it fresh against the catalogue, and do NOT
  list "intent" as inherited.

Always classify the RESOLVED query, not the raw fragment. If the
message says "what about september" after a calendar question,
you are classifying "What school events are there in
September?".

Use "unknown" only when the resolved query matches nothing in
the catalogue.

4. PARAMETER INHERITANCE

Start from the previous turn's parameters. Replace ONLY the
ones the latest message actually changes. Keep everything else
exactly as it was.

"What about last month?" after a Physics homework question
keeps subject=Physics and replaces the dates only.

If the user narrows or removes a filter ("all subjects now",
"without the pending filter"), drop that parameter instead of
inheriting it.

5. CLARIFICATION - LAST RESORT

Only ask when the message could point at two or more DIFFERENT
things that are all present in the conversation, and choosing
between them would be a coin flip.

Before asking, check all of these. If ANY is true, do NOT ask -
resolve the message instead:

- Only one topic appears in the recent conversation. A fragment
  then continues THAT topic. There is nothing to disambiguate.
- The fragment only changes one detail of a previous question
  (a month, a date, a subject, a filter).
- One reading is clearly more natural than the others.

A message being short, vague or fragmentary is NOT a reason to
ask. Fragments are how people ask follow-ups, and resolving them
is your job.

You may only ask while context_used.used is true. If you did not
use the conversation, nothing is ambiguous, so
clarification_required.required MUST be false. Never report that
a message "stands on its own" and ask for clarification at the
same time - those contradict each other.

When you do ask, ask about the SPECIFIC missing piece and name
the candidates from the conversation. Fill resolved_query with
your best literal reading and leave "intent" null.

Never invent an answer instead of asking.

==================================================
EXAMPLES
==================================================

History: "How much homework do I have this week?"
(intent homework_summary, parameters {{"start_date": "...",
"end_date": "..."}})

Latest: "what about this month?"

{{
  "resolved_query": "How much homework do I have this month?",
  "intent": "homework_summary",
  "parameters": {{"start_date": "<first of this month>",
                 "end_date": "<last of this month>"}},
  "context_used": {{"used": true, "turn_ids": [<id>],
                   "inherited_fields": ["intent"],
                   "reason": "Fragment continuing the homework question."}},
  "clarification_required": {{"required": false, "question": null,
                             "reason": null}}
}}

--------------------------------------------------

History: "Whats about in july month"
(intent calendar_summary, parameters {{"start_date": "2026-07-01",
"end_date": "2026-07-31"}})

Latest: "tell me for the september"

Only one topic is in the conversation, and the fragment changes
only the month, so this is resolved, NOT clarified.

{{
  "resolved_query": "What school events are there in September?",
  "intent": "calendar_summary",
  "parameters": {{"start_date": "<first of september>",
                 "end_date": "<last of september>"}},
  "context_used": {{"used": true, "turn_ids": [<id>],
                   "inherited_fields": ["intent"],
                   "reason": "Only the month changed."}},
  "clarification_required": {{"required": false, "question": null,
                             "reason": null}}
}}

--------------------------------------------------

History: "Show my Physics homework marks."
(intent homework_summary, parameters {{"subject": "Physics",
"asks_for_marks": true}})

Latest: "and last week?"

{{
  "resolved_query": "Show my Physics homework marks for last week.",
  "intent": "homework_summary",
  "parameters": {{"subject": "Physics", "asks_for_marks": true,
                 "start_date": "<monday of last week>",
                 "end_date": "<sunday of last week>"}},
  "context_used": {{"used": true, "turn_ids": [<id>],
                   "inherited_fields": ["intent", "subject",
                                        "asks_for_marks"],
                   "reason": "Only the time window changed."}},
  "clarification_required": {{"required": false, "question": null,
                             "reason": null}}
}}

--------------------------------------------------

History: "How is my attendance this month?"

Latest: "What is my Atlas score?"

{{
  "resolved_query": "What is my Atlas score?",
  "intent": null,
  "parameters": {{}},
  "context_used": {{"used": false, "turn_ids": [],
                   "inherited_fields": [],
                   "reason": "The message stands on its own."}},
  "clarification_required": {{"required": false, "question": null,
                             "reason": null}}
}}

--------------------------------------------------

History: "Show my Physics homework." then "Show my Chemistry
homework."

Latest: "what about the other one?"

{{
  "resolved_query": "what about the other one?",
  "intent": null,
  "parameters": {{}},
  "context_used": {{"used": true, "turn_ids": [<ids>],
                   "inherited_fields": [],
                   "reason": "Reference matches two subjects."}},
  "clarification_required": {{"required": true,
    "question": "Did you mean Physics or Chemistry?",
    "reason": "Two subjects were discussed and the reference fits both."}}
}}
""".strip()


def build_query_resolver_messages(
    *,
    role: str,
    allowed_intents: list[str],
    today: str,
    timezone_name: str,
    turns: list,
    query: str,
) -> list[dict]:

    # Oldest-first reads as a conversation; the repository
    # returns newest-first.

    history = [
        turn.as_prompt_payload()
        for turn in reversed(turns)
    ]

    user_content = (
        "RECENT CONVERSATION (oldest first):\n"
        f"{json.dumps(history, indent=2, default=str)}\n\n"
        "LATEST USER MESSAGE:\n"
        f"{query}"
    )

    return [
        {
            "role": "system",

            "content": build_query_resolver_prompt(
                role=role,
                allowed_intents=allowed_intents,
                today=today,
                timezone_name=timezone_name,
            ),
        },
        {
            "role": "user",

            "content": user_content,
        },
    ]
