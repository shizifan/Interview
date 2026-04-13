from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db, get_current_candidate
from app.core.exceptions import BusinessError, ERR_LOGIN_FAILED
from app.core.response import success
from app.core.security import create_access_token
from app.models.candidate import Candidate
from app.schemas.candidate import (
    CandidateEnter, CandidateProfile, CandidateProfileUpdate,
    DocumentOut, TokenResponse, OcrCorrection,
)
from app.schemas.interview import InterviewOut
from app.services import candidate_service, document_service

router = APIRouter(tags=["候选人"])


@router.post("/enter")
async def enter_system(data: CandidateEnter, db: AsyncSession = Depends(get_db)):
    """手机号 + 验证码进入系统"""
    if data.code != settings.CANDIDATE_TEST_CODE:
        raise BusinessError(ERR_LOGIN_FAILED, "验证码错误")
    candidate = await candidate_service.enter_system(db, data.phone)
    token = create_access_token(subject=str(candidate.id), role="candidate")
    return success(TokenResponse(
        access_token=token,
        candidate=CandidateProfile.model_validate(candidate),
    ))


@router.get("/me")
async def get_me(
    current: Candidate = Depends(get_current_candidate),
):
    """根据 JWT 返回当前候选人信息（用于刷新后恢复会话）"""
    return success(CandidateProfile.model_validate(current))


@router.get("/jobs")
async def list_jobs_for_candidate(
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    """候选人可见的招聘中岗位列表"""
    from sqlalchemy import select
    from app.models.job import Job
    from app.schemas.hr import JobOut

    result = await db.execute(
        select(Job).where(Job.status == 1).order_by(Job.id.desc())
    )
    jobs = result.scalars().all()
    return success([JobOut.model_validate(j) for j in jobs])


@router.post("/jobs/{job_id}/apply")
async def apply_job(
    job_id: int,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    """候选人申请岗位（创建面试）"""
    from sqlalchemy import select
    from app.models.job import Job
    from app.services import interview_service
    from app.schemas.interview import InterviewState

    result = await db.execute(select(Job).where(Job.id == job_id, Job.status == 1))
    job = result.scalar_one_or_none()
    if job is None:
        return {"code": 404, "message": "岗位不存在或未开放", "data": None}

    state = await interview_service.create_and_start_interview(db, current.id, job_id)
    return success(InterviewState(
        interview_id=state.interview_id,
        current_node=state.current_node,
        current_question_index=state.current_question_index,
        total_questions=len(state.questions),
        tts_text=state.tts_text,
        status=state.status,
        score=state.total_score,
        message=state.message,
    ))


@router.get("/candidates/{candidate_id}/profile")
async def get_profile(
    candidate_id: int,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    candidate = await candidate_service.get_candidate(db, candidate_id)
    if candidate is None:
        return {"code": 404, "message": "候选人不存在", "data": None}
    return success(CandidateProfile.model_validate(candidate))


@router.put("/candidates/{candidate_id}/profile")
async def update_profile(
    candidate_id: int,
    data: CandidateProfileUpdate,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    candidate = await candidate_service.update_profile(
        db, candidate_id, data.model_dump(exclude_unset=True)
    )
    if candidate is None:
        return {"code": 404, "message": "候选人不存在", "data": None}
    return success(CandidateProfile.model_validate(candidate))


@router.post("/candidates/{candidate_id}/documents")
async def upload_document(
    candidate_id: int,
    file: UploadFile = File(...),
    doc_type: int = Form(...),
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    doc = await document_service.upload_document(
        db, candidate_id, doc_type, content, file.filename or "upload.jpg"
    )
    return success(DocumentOut.model_validate(doc))


@router.get("/candidates/{candidate_id}/documents")
async def list_documents(
    candidate_id: int,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    docs = await document_service.list_documents(db, candidate_id)
    return success([DocumentOut.model_validate(d) for d in docs])


@router.put("/candidates/{candidate_id}/documents/{document_id}/ocr")
async def confirm_ocr(
    candidate_id: int,
    document_id: int,
    data: OcrCorrection,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    """确认/修正 OCR 识别结果"""
    doc = await document_service.update_ocr_result(
        db, document_id, candidate_id, data.corrected_fields
    )
    if doc is None:
        return {"code": 404, "message": "材料不存在", "data": None}
    return success(DocumentOut.model_validate(doc))


@router.get("/candidates/{candidate_id}/interviews")
async def list_interviews(
    candidate_id: int,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.interview import Interview

    result = await db.execute(
        select(Interview)
        .where(Interview.candidate_id == candidate_id)
        .order_by(Interview.id.desc())
    )
    interviews = result.scalars().all()
    return success([InterviewOut.model_validate(i) for i in interviews])


@router.get("/candidates/{candidate_id}/interviews/{interview_id}/result")
async def get_interview_result(
    candidate_id: int,
    interview_id: int,
    current: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.interview import Interview

    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if interview is None or interview.candidate_id != candidate_id:
        return {"code": 404, "message": "面试记录不存在", "data": None}
    if interview.status != 2:
        return {"code": 603, "message": "面试尚未完成", "data": None}

    return success({
        "interview": InterviewOut.model_validate(interview),
        "report": interview.report_content,
    })
