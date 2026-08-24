from pydantic import BaseModel


class ParsedGuardianIntent(BaseModel):

    intent: str

    navigation_target: str | None = None

    start_date: str | None = None

    end_date: str | None = None

    academic_year: str | None = None

    grade: str | None = None

    section: str | None = None

    subject: str | None = None

    enrichment: bool | None = None

    view: str | None = None

    target_modules: list[str] = []

    confidence: float = 0.95

    original_query: str = ""