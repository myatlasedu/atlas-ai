from datetime import date

from pydantic import (
    BaseModel,
    Field
)

from intents.student.enums import (
    StudentIntent
)


class ParsedStudentIntent(BaseModel):

    intent: StudentIntent

    navigation_target: str | None = None

    start_date: str | None = None
    end_date: str | None = None

    target_modules: list[str] = []

    confidence: float = 0.0

    original_query: str = ""