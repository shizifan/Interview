import json
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.question import Question
from app.models.candidate import Candidate
from app.models.interview import Interview
from app.models.score_pool import ScorePool
from app.models.system_settings import SystemSettings


# ===== 岗位管理 =====

async def list_jobs(db: AsyncSession, status: int | None = None, page: int = 1, page_size: int = 20):
    query = select(Job)
    if status is not None:
        query = query.where(Job.status == status)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Job.id.desc())
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_job(db: AsyncSession, job_id: int) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def create_job(db: AsyncSession, data: dict) -> Job:
    if "required_license_type" in data and isinstance(data["required_license_type"], list):
        data["required_license_type"] = json.dumps(data["required_license_type"])
    job = Job(**data)
    db.add(job)
    await db.flush()
    return job


async def update_job(db: AsyncSession, job_id: int, data: dict) -> Job | None:
    job = await get_job(db, job_id)
    if job is None:
        return None
    for key, value in data.items():
        if value is not None and hasattr(job, key):
            if key == "required_license_type" and isinstance(value, list):
                value = json.dumps(value)
            setattr(job, key, value)
    await db.flush()
    return job


async def delete_job(db: AsyncSession, job_id: int) -> bool:
    job = await get_job(db, job_id)
    if job is None:
        return False
    await db.delete(job)
    await db.flush()
    return True


# ===== 题目管理 =====

async def list_questions(db: AsyncSession, job_id: int | None = None, page: int = 1, page_size: int = 20):
    query = select(Question)
    if job_id is not None:
        query = query.where(Question.job_id == job_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Question.id.desc())
    result = await db.execute(query)
    return result.scalars().all(), total


async def get_question(db: AsyncSession, question_id: int) -> Question | None:
    result = await db.execute(select(Question).where(Question.id == question_id))
    return result.scalar_one_or_none()


async def create_question(db: AsyncSession, data: dict) -> Question:
    if "score_points" in data and isinstance(data["score_points"], list):
        data["score_points"] = json.dumps(data["score_points"], ensure_ascii=False)
    if "follow_up_scripts" in data and isinstance(data["follow_up_scripts"], list):
        data["follow_up_scripts"] = json.dumps(data["follow_up_scripts"], ensure_ascii=False)
    question = Question(**data)
    db.add(question)
    await db.flush()
    return question


async def update_question(db: AsyncSession, question_id: int, data: dict) -> Question | None:
    question = await get_question(db, question_id)
    if question is None:
        return None
    for key, value in data.items():
        if value is not None and hasattr(question, key):
            if key in ("score_points", "follow_up_scripts") and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            setattr(question, key, value)
    await db.flush()
    return question


async def delete_question(db: AsyncSession, question_id: int) -> bool:
    question = await get_question(db, question_id)
    if question is None:
        return False
    await db.delete(question)
    await db.flush()
    return True


# ===== 候选人管理 =====

async def list_candidates(db: AsyncSession, status: int | None = None, page: int = 1, page_size: int = 20):
    query = select(Candidate)
    if status is not None:
        query = query.where(Candidate.status == status)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Candidate.total_score.desc())
    result = await db.execute(query)
    return result.scalars().all(), total


async def invite_candidate(db: AsyncSession, candidate_id: int, job_id: int) -> Interview:
    """为候选人创建面试邀请"""
    interview = Interview(candidate_id=candidate_id, job_id=job_id, status=0)
    db.add(interview)
    # 更新评分池
    result = await db.execute(
        select(ScorePool).where(
            and_(ScorePool.candidate_id == candidate_id, ScorePool.job_id == job_id)
        )
    )
    pool_entry = result.scalar_one_or_none()
    if pool_entry:
        pool_entry.is_invited = True
    await db.flush()
    return interview


# ===== 面试管理 =====

async def list_interviews(db: AsyncSession, status: int | None = None, job_id: int | None = None,
                          page: int = 1, page_size: int = 20):
    query = select(Interview)
    if status is not None:
        query = query.where(Interview.status == status)
    if job_id is not None:
        query = query.where(Interview.job_id == job_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Interview.id.desc())
    result = await db.execute(query)
    return result.scalars().all(), total


# ===== 仪表盘 =====

async def get_dashboard_stats(db: AsyncSession) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")

    # 今日面试数
    result = await db.execute(
        select(func.count()).select_from(Interview).where(Interview.start_time.like(f"{today}%"))
    )
    today_interviews = result.scalar() or 0

    # 已完成面试数
    result = await db.execute(
        select(func.count()).select_from(Interview).where(Interview.status == 2)
    )
    completed = result.scalar() or 0

    # 通过面试数（得分>=60）
    result = await db.execute(
        select(func.count()).select_from(Interview).where(
            and_(Interview.status == 2, Interview.score >= 60)
        )
    )
    passed = result.scalar() or 0

    # 待审核材料数
    from app.models.document import Document
    result = await db.execute(
        select(func.count()).select_from(Document).where(Document.status == 0)
    )
    pending_docs = result.scalar() or 0

    # 候选人总数
    result = await db.execute(select(func.count()).select_from(Candidate))
    total_candidates = result.scalar() or 0

    pass_rate = round(passed / completed * 100, 1) if completed > 0 else 0

    return {
        "today_interviews": today_interviews,
        "completed_interviews": completed,
        "pass_rate": pass_rate,
        "pending_documents": pending_docs,
        "total_candidates": total_candidates,
    }


# ===== 系统设置 =====

async def get_settings(db: AsyncSession) -> dict:
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    return {s.key: {"value": s.value, "description": s.description} for s in settings_list}


async def update_settings(db: AsyncSession, data: dict[str, str]) -> dict:
    for key, value in data.items():
        result = await db.execute(select(SystemSettings).where(SystemSettings.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            db.add(SystemSettings(key=key, value=value))
    await db.flush()
    return await get_settings(db)


# ===== 评分池 =====

async def list_score_pool(db: AsyncSession, job_id: int, page: int = 1, page_size: int = 20):
    query = select(ScorePool).where(ScorePool.job_id == job_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size).order_by(ScorePool.doc_score.desc())
    result = await db.execute(query)
    entries = result.scalars().all()

    # 附加候选人信息
    items = []
    for entry in entries:
        candidate = await db.execute(select(Candidate).where(Candidate.id == entry.candidate_id))
        c = candidate.scalar_one_or_none()
        items.append({
            "id": entry.id,
            "candidate_id": entry.candidate_id,
            "job_id": entry.job_id,
            "doc_score": entry.doc_score,
            "interview_score": entry.interview_score,
            "total_score": entry.total_score,
            "rank": entry.rank,
            "is_invited": entry.is_invited,
            "candidate_name": c.name if c else None,
            "candidate_phone": c.phone if c else None,
            "updated_at": entry.updated_at,
        })
    return items, total
