from pydantic import BaseModel, Field


class CandidateEnter(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    code: str = Field(..., min_length=1, description="验证码")


class CandidateProfile(BaseModel):
    id: int
    name: str
    phone: str
    id_card: str | None = None
    gender: int = 1
    age: int | None = None
    education: str | None = None
    work_experience: int = 0
    address: str | None = None
    status: int = 0
    total_score: float = 0.0
    created_at: str | None = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    candidate: CandidateProfile | None = None


class CandidateProfileUpdate(BaseModel):
    name: str | None = None
    id_card: str | None = None
    gender: int | None = None
    age: int | None = None
    education: str | None = None
    work_experience: int | None = None
    address: str | None = None


class DocumentOut(BaseModel):
    id: int
    candidate_id: int
    type: int
    file_name: str
    file_path: str
    file_size: int | None = None
    ocr_result: str | None = None
    status: int = 0
    reject_reason: str | None = None
    score: float = 0.0
    created_at: str | None = None

    class Config:
        from_attributes = True


class OcrCorrection(BaseModel):
    corrected_fields: dict[str, str]
