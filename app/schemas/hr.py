from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    requirements: str | None = None
    quota: int = Field(default=1, ge=1)
    start_coefficient: float = Field(default=1.2, ge=0.5, le=3.0)
    min_interview_count: int = Field(default=5, ge=1)
    required_license_type: list[str] | None = None
    status: int = 0


class JobUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    requirements: str | None = None
    quota: int | None = None
    start_coefficient: float | None = None
    min_interview_count: int | None = None
    required_license_type: list[str] | None = None
    status: int | None = None


class JobOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    requirements: str | None = None
    quota: int
    start_coefficient: float
    min_interview_count: int
    required_license_type: str | None = None
    status: int
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    job_id: int
    content: str = Field(..., min_length=10)
    type: int = Field(default=1, ge=1, le=3)
    difficulty: int = Field(default=2, ge=1, le=3)
    score_points: list[str] = Field(..., min_length=1)
    follow_up_scripts: list[str] | None = None


class QuestionUpdate(BaseModel):
    content: str | None = None
    type: int | None = None
    difficulty: int | None = None
    score_points: list[str] | None = None
    follow_up_scripts: list[str] | None = None
    is_active: bool | None = None


class QuestionOut(BaseModel):
    id: int
    job_id: int
    content: str
    type: int
    difficulty: int
    score_points: str  # JSON字符串，前端解析
    follow_up_scripts: str | None = None
    is_active: bool
    created_at: str | None = None

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    job_id: int


class SettingsUpdate(BaseModel):
    settings: dict[str, str]
