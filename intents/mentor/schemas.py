from datetime import date

from pydantic import BaseModel

from intents.mentor.enums import (
    MentorIntent
)


class ParsedMentorIntent(BaseModel):

    intent: MentorIntent

    # Date Range
    start_date: date | None = None
    end_date: date | None = None

    # Filters
    academic_year: str | None = None

    grade: str | None = None

    section: str | None = None

    subject: str | None = None

    enrichment: bool | None = None

    # Generic View
    view: str | None = None

    # Modules to execute
    target_modules: list[str] = []

    confidence: float = 0.95

    original_query: str | None = None