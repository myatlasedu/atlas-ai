from pydantic import BaseModel
from datetime import date

class ParsedGuardianIntent(BaseModel):

    intent: str

    navigation_target: str | None = None

    start_date: date | None = None

    end_date: date | None = None

    academic_year: str | None = None

    grade: str | None = None

    section: str | None = None

    subject: str | None = None

    topic: str | None = None

    enrichment: str | bool | None = None

    view: str | None = None

    target_modules: list[str] = []

    confidence: float = 0.95

    original_query: str = ""

    is_injection: bool = False

    generate_content: bool = False

    asks_for_marks: bool = False