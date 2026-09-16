from datetime import datetime

from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class ChatSession(BaseModel):

    # One conversation thread, as listed in the sidebar.

    id: UUID

    user_id: int

    role: str

    title: str | None = None

    status: str

    message_count: int = 0

    last_message_at: datetime | None = None

    created_at: datetime

    updated_at: datetime


class ChatMessage(BaseModel):

    # One answered turn: what was asked and what came back.

    id: int

    session_id: UUID

    turn_index: int

    query: str

    answer: str | None = None

    status: str

    error_message: str | None = None

    audit_id: int | None = None

    created_at: datetime

    updated_at: datetime


class ChatTranscript(BaseModel):

    session: ChatSession

    messages: list[ChatMessage] = Field(
        default_factory=list,
    )


class CreateSessionRequest(BaseModel):

    user_id: int

    role: str

    title: str | None = None


class UpdateSessionRequest(BaseModel):

    user_id: int

    role: str

    title: str | None = None

    status: str | None = Field(
        default=None,
        pattern="^(active|archived)$",
    )
