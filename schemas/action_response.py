from pydantic import BaseModel


class ActionResponse(
    BaseModel
):

    action_required: bool

    confirmation_required: bool

    action_type: str

    payload: dict