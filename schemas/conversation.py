from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    Field,
)


class ConversationTurn(BaseModel):

    turn_id: int

    query: str

    resolved_query: str | None = None
    
    predicted_intent: str = ""

    selected_tools: list = Field(
        default_factory=list,
    )

    summary: str | None = None

    created_at: datetime | None = None
