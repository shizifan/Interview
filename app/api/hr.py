import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.response import success
from app.schemas.hr import (
    JobCreate, JobUpdate, JobOut,
    QuestionCreate, QuestionUpdate, QuestionOut,
    InviteRequest, SettingsUpdate,
)
from app.schemas.candidate import CandidateProfile
from app.schemas.interview import InterviewOut, InterviewDetailOut, InterviewAnswerOut
from app.services import hr_service

router = APIRouter(tags=["HR管理"])


# ===== 仪表盘 =====

@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db)):
    stats = await hr_service.get_dashboard_stats(db)
    return success(stats)


# ===== 岗位管理 =====

@router.get("/jobs")
async def list_jobs(
    status: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await hr_service.list_jobs(db, status, page, page_size)
    return success({
        "items": [JobOut.model_validate(j) for j in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/jobs")
async def create_job(data: JobCreate, db: AsyncSession = Depends(get_db)):
    job = await hr_service.create_job(db, data.model_dump())
    return success(JobOut.model_validate(job))


@router.get("/jobs/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await hr_service.get_job(db, job_id)
    if job is None:
        return {"code": 404, "message": "岗位不存在", "data": None}
    return success(JobOut.model_validate(job))


@router.put("/jobs/{job_id}")
async def update_job(job_id: int, data: JobUpdate, db: AsyncSession = Depends(get_db)):
    job = await hr_service.update_job(db, job_id, data.model_dump(exclude_unset=True))
    if job is None:
        return {"code": 404, "message": "岗位不存在", "data": None}
    return success(JobOut.model_validate(job))


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    ok = await hr_service.delete_job(db, job_id)
    if not ok:
        return {"code": 404, "message": "岗位不存在", "data": None}
    return success(message="删除成功")


# ===== 题目管理 =====

@router.get("/questions")
async def list_questions(
    job_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await hr_service.list_questions(db, job_id, page, page_size)
    return success({
        "items": [QuestionOut.model_validate(q) for q in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/questions")
async def create_question(data: QuestionCreate, db: AsyncSession = Depends(get_db)):
    question = await hr_service.create_question(db, data.model_dump())
    return success(QuestionOut.model_validate(question))


@router.get("/questions/{question_id}")
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    question = await hr_service.get_question(db, question_id)
    if question is None:
        return {"code": 404, "message": "题目不存在", "data": None}
    return success(QuestionOut.model_validate(question))


@router.put("/questions/{question_id}")
async def update_question(
    question_id: int, data: QuestionUpdate, db: AsyncSession = Depends(get_db)
):
    question = await hr_service.update_question(db, question_id, data.model_dump(exclude_unset=True))
    if question is None:
        return {"code": 404, "message": "题目不存在", "data": None}
    return success(QuestionOut.model_validate(question))


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    ok = await hr_service.delete_question(db, question_id)
    if not ok:
        return {"code": 404, "message": "题目不存在", "data": None}
    return success(message="删除成功")


# ===== 候选人管理 =====

@router.get("/candidates")
async def list_candidates(
    status: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await hr_service.list_candidates(db, status, page, page_size)
    return success({
        "items": [CandidateProfile.model_validate(c) for c in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    from app.services.candidate_service import get_candidate as get_c
    candidate = await get_c(db, candidate_id)
    if candidate is None:
        return {"code": 404, "message": "候选人不存在", "data": None}
    return success(CandidateProfile.model_validate(candidate))


@router.post("/candidates/{candidate_id}/invite")
async def invite_candidate(
    candidate_id: int, data: InviteRequest, db: AsyncSession = Depends(get_db)
):
    interview = await hr_service.invite_candidate(db, candidate_id, data.job_id)
    return success(InterviewOut.model_validate(interview))


# ===== 面试管理 =====

@router.get("/interviews")
async def list_interviews(
    status: int | None = None,
    job_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await hr_service.list_interviews(db, status, job_id, page, page_size)
    return success({
        "items": [InterviewOut.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/interviews/{interview_id}")
async def get_interview_detail(interview_id: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app.models.interview import Interview
    from app.models.interview_answer import InterviewAnswer
    from app.models.candidate import Candidate
    from app.models.job import Job

    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        return {"code": 404, "message": "面试记录不存在", "data": None}

    answers_result = await db.execute(
        select(InterviewAnswer)
        .where(InterviewAnswer.interview_id == interview_id)
        .order_by(InterviewAnswer.question_order)
    )
    answers = answers_result.scalars().all()

    c_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
    candidate = c_result.scalar_one_or_none()
    j_result = await db.execute(select(Job).where(Job.id == interview.job_id))
    job = j_result.scalar_one_or_none()

    return success(InterviewDetailOut(
        interview=InterviewOut.model_validate(interview),
        answers=[InterviewAnswerOut.model_validate(a) for a in answers],
        candidate_name=candidate.name if candidate else None,
        job_name=job.name if job else None,
    ))


# ===== 评分池 =====

@router.get("/score-pool")
async def list_score_pool(
    job_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    items, total = await hr_service.list_score_pool(db, job_id, page, page_size)
    return success({"items": items, "total": total, "page": page, "page_size": page_size})


# ===== 系统设置 =====

@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    settings_data = await hr_service.get_settings(db)
    return success(settings_data)


@router.put("/settings")
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    result = await hr_service.update_settings(db, data.settings)
    return success(result)
