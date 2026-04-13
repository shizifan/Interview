from pydantic import BaseModel


class ScorePoolOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    doc_score: float = 0.0
    rank: int | None = None
    is_invited: bool = False
    candidate_name: str | None = None
    candidate_phone: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True
