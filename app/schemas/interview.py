from pydantic import BaseModel


class InterviewOut(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    start_time: str | None = None
    end_time: str | None = None
    status: int = 0
    score: float = 0.0
    current_question_index: int = 0
    current_node: str = "intro"
    report_content: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


class CandidateInterviewOut(BaseModel):
    """候选人可见的面试信息（不含得分和报告）"""
    id: int
    candidate_id: int
    job_id: int
    start_time: str | None = None
    end_time: str | None = None
    status: int = 0
    current_question_index: int = 0
    current_node: str = "intro"
    created_at: str | None = None

    class Config:
        from_attributes = True


class InterviewState(BaseModel):
    interview_id: int
    current_node: str
    current_question_index: int
    total_questions: int
    tts_text: str | None = None
    question_text: str | None = None
    status: str
    message: str | None = None


class StartInterviewRequest(BaseModel):
    candidate_id: int
    job_id: int


class SubmitAnswerRequest(BaseModel):
    answer_text: str


class InterviewAnswerOut(BaseModel):
    id: int
    interview_id: int
    question_id: int
    question_order: int
    answer_text: str | None = None
    follow_up_count: int = 0
    score: float = 0.0
    score_detail: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


class InterviewDetailOut(BaseModel):
    interview: InterviewOut
    answers: list[InterviewAnswerOut] = []
    candidate_name: str | None = None
    job_name: str | None = None
