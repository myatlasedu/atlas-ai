from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    Field,
)


class ConversationTurn(BaseModel):

    # One previously answered turn, replayed into intent parsing
    # so follow-up queries can inherit the intent they refer to.

    turn_id: int

    query: str

    # Empty for a turn rebuilt from the transcript after the
    # cache expired: ai_chat_message stores no intent.

    predicted_intent: str = ""

    parsed_intent: dict = Field(
        default_factory=dict,
    )

    selected_tools: list = Field(
        default_factory=list,
    )

    summary: str | None = None

    created_at: datetime | None = None
