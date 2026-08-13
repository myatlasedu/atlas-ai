from datetime import date, datetime

from pydantic import BaseModel, Field

from uuid import (
    uuid4,
)


class ConversationTurn(BaseModel):

    user_query: str

    assistant_summary: str

    intent: str

    target_modules: list[str] = []

    start_date: date | None = None

    end_date: date | None = None


class ConversationSession(BaseModel):

    session_id: str = (
        Field(
            default_factory=lambda: (
                str(
                    uuid4()
                )
            )
        )
    )

    user_id: int

    role: str

    student_id: int | None = None

    current_intent: str | None = None

    turns: list[ConversationTurn] = []

    rev: int = 0

    created_at: datetime | None = None

    updated_at: datetime | None = None
