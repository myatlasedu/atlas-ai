from datetime import date

from pydantic import (
    BaseModel,
)


class ParsedStudentIntent(BaseModel):

    intent: str

    navigation_target: str | None = None

    start_date: date | None = None

    end_date: date | None = None

    target_modules: list[str] = []

    confidence: float = 0.95

    original_query: str
    
    topic: str | None = None

    subject: str | None = None

    teacher: str | None = None

    asks_for_marks: bool = False

    invalid_date: bool = False

    late_only: bool = False

    homework_focus: str | None = None

    # ==================================================
    # CONVERSATION CONTEXT PROVENANCE
    # ==================================================

    # The user's literal message. `original_query` holds the
    # standalone rewrite that the parser and every downstream
    # keyword heuristic actually ran on.

    raw_query: str | None = None

    resolved_query: str | None = None

    inherited_intent: bool = False

    context_used: dict = {}

    inherited_parameters: list[str] = []