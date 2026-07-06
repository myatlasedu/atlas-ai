from typing import List, Optional

from pydantic import BaseModel


class UserContext(BaseModel):

    user_id: int

    role: str

    campus_id: int

    student_id: int | None = None

    enrollment_id: int | None = None

    academic_class_id: int | None = None


class AIRequest(BaseModel):

    query: str

    context: UserContext

class MentorContext(BaseModel):

    
    user_id: int

    academic_year_id: int

    staff_id: int

class MentorAIRequest(BaseModel):
    query: str
    context: MentorContext

