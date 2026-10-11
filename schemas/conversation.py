from datetime import (
    datetime,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
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

    @field_validator(
        "predicted_intent",
        mode="before",
    )
    
    @classmethod
    def _none_to_empty(
        cls,
        value,
    ):

        return value or ""
