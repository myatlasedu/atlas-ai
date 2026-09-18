from datetime import date

from pydantic import (
    BaseModel,
    Field,
)


class ParsedStudentIntent(BaseModel):

    intent: str

    navigation_target: str | None = None

    start_date: date | None = None

    end_date: date | None = None

    target_modules: list[str] = []

    confidence: float = 0.95

    original_query: str

    raw_query: str | None = None

    is_follow_up: bool = False

    context_resolution: dict = Field(
        default_factory=dict,
        exclude=True,
    )

    topic: str | None = None

    subject: str | None = None

    teacher: str | None = None

    asks_for_marks: bool = False

    invalid_date: bool = False

    late_only: bool = False

    homework_focus: str | None = None