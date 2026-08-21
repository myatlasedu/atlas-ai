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

    asks_for_marks: bool = False