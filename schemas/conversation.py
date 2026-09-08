from datetime import datetime

from typing import Any

from pydantic import (
    BaseModel,
    Field,
)


# ==================================================
# PARAMETER INHERITANCE POLICY
# ==================================================

#
# Parameters a follow-up may inherit from the previous turn
# when the intent stays the same ("what about last month?"
# after a homework question keeps the subject filter).
#

SAME_INTENT_INHERITABLE_PARAMETERS = (

    "start_date",

    "end_date",

    "subject",

    "teacher",

    "topic",

    "target_modules",

    "homework_focus",

    "asks_for_marks",

    "late_only",
)


#
# When the follow-up switches intent ("and my attendance?"),
# only the time window carries over. Entity filters are
# intent-specific and would be stale.
#

CROSS_INTENT_INHERITABLE_PARAMETERS = (

    "start_date",

    "end_date",
)


BOOLEAN_PARAMETERS = (

    "asks_for_marks",

    "late_only",
)


LIST_PARAMETERS = (

    "target_modules",
)


DATE_PARAMETERS = (

    "start_date",

    "end_date",
)


# ==================================================
# CONVERSATION TURN
# ==================================================

class ConversationTurn(BaseModel):

    turn_id: int

    query: str

    predicted_intent: str

    parsed_intent: dict[str, Any] = Field(
        default_factory=dict
    )

    selected_tools: list[str] = Field(
        default_factory=list
    )

    summary: str = ""

    created_at: datetime | None = None

    def parameters(
        self,
        allowed: tuple[str, ...] = SAME_INTENT_INHERITABLE_PARAMETERS,
    ) -> dict[str, Any]:

        # The turn's parameters, restricted to what a
        # follow-up is allowed to inherit.

        return {

            key: self.parsed_intent.get(key)

            for key in allowed

            if self.parsed_intent.get(key)
            not in (
                None,
                "",
                [],
                False,
            )
        }

    def as_prompt_payload(self) -> dict[str, Any]:

        # Compact view handed to the resolver LLM. Tool RESULTS
        # are deliberately excluded: they can be megabytes and the
        # resolver only needs what was asked, not what came back.

        return {

            "turn_id":
                self.turn_id,

            "user_query":
                self.query,

            "intent":
                self.predicted_intent,

            "parameters":
                self.parameters(),

            "tool_calls":
                self.selected_tools,

            "summary":
                (
                    self.summary[:400]
                    if self.summary
                    else ""
                ),

            "asked_at":
                (
                    self.created_at.isoformat()
                    if self.created_at
                    else None
                ),
        }


# ==================================================
# RESOLUTION OUTPUT
# ==================================================

class ContextUsage(BaseModel):

    used: bool = False

    turn_ids: list[int] = Field(
        default_factory=list
    )

    inherited_fields: list[str] = Field(
        default_factory=list
    )

    reason: str | None = None


class Clarification(BaseModel):

    required: bool = False

    question: str | None = None

    reason: str | None = None


class QueryResolution(BaseModel):

    resolved_query: str

    intent: str | None = None

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    context_used: ContextUsage = Field(
        default_factory=ContextUsage
    )

    clarification_required: Clarification = Field(
        default_factory=Clarification
    )

    # ----------------------------------------------
    # Internal bookkeeping (not part of the contract)
    # ----------------------------------------------

    inherited_intent: bool = False

    latency_ms: int = 0

    @classmethod
    def passthrough(
        cls,
        query: str,
        reason: str | None = None,
    ) -> "QueryResolution":

        # No usable history, or resolution failed: the query is
        # already standalone and the pipeline behaves exactly as
        # it did before context awareness existed.

        return cls(

            resolved_query=query,

            intent=None,

            parameters={},

            context_used=ContextUsage(
                used=False,
                reason=reason,
            ),

            clarification_required=Clarification(
                required=False
            ),
        )

    def contract(self) -> dict[str, Any]:

        # The documented 5-key structured output.

        return {

            "resolved_query":
                self.resolved_query,

            "intent":
                self.intent,

            "parameters":
                self.parameters,

            "context_used":
                self.context_used.model_dump(),

            "clarification_required":
                self.clarification_required.model_dump(),
        }
