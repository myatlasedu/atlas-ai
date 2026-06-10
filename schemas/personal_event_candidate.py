from pydantic import BaseModel
from typing import Optional


class PersonalEventCandidate(
    BaseModel
):

    title: str

    event_type: str

    start_datetime: Optional[str] = None

    end_datetime: Optional[str] = None

    description: Optional[str] = None