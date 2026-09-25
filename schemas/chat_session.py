from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
)


class ChatSession(BaseModel):

    # One conversation thread, as listed in the sidebar.

    id: int

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

    session_id: int

    query: str

    answer: str | None = None

    context_resolution: dict | None = None

    selected_tools: list | None = None

    parsed_intent: dict | None = None

    predicted_intent: str | None = None

    created_at: datetime


class ChatTranscript(BaseModel):

    session: ChatSession

    messages: list[ChatMessage] = Field(
        default_factory=list,
    )


class UpdateSessionRequest(BaseModel):

    user_id: int

    role: str

    title: str | None = None

    status: str | None = Field(
        default=None,
        pattern="^(active|archived)$",
    )
