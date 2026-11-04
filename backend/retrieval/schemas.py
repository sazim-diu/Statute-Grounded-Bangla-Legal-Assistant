from pydantic import BaseModel, field_validator


class SearchRequest(BaseModel):
    question: str
    act_id: int | None = None
    k: int | None = None
    session_id: str | None = None

    @field_validator("question")
    @classmethod
    def check_question(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("Question is too short")
        if len(v) > 500:
            raise ValueError("Question is too long (max 500 characters)")
        return v

    @field_validator("k")
    @classmethod
    def check_k(cls, v: int | None) -> int | None:
        if v is not None and not 1 <= v <= 10:
            raise ValueError("k must be between 1 and 10")
        return v


class SectionHit(BaseModel):
    rank: int
    score: float
    section_id: int
    act_id: int
    act_name: str
    act_year: int | None
    chapter: str | None
    section_number: str
    title: str | None
    text: str
    source_url: str | None


class SearchResponse(BaseModel):
    query_id: int | None
    question: str
    best_score: float | None
    snapshot_date: str | None
    results: list[SectionHit]
    disclaimer: str
    amendment_notice: str
