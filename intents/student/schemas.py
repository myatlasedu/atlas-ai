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

    start_date: date | None = None
    end_date: date | None = None

    target_modules: list[str] = Field(default_factory=list)

    confidence: float = 0.0

    original_query: str = ""