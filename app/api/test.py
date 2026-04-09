"""测试端点 - 无认证快速启动面试，用于验证完整链路"""

from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.response import success, error
from app.models.candidate import Candidate
from app.models.job import Job
from app.schemas.interview import InterviewState
from app.services import interview_service

router = APIRouter(tags=["测试"])


@router.post("/quick-start")
async def quick_start(db: AsyncSession = Depends(get_db)):
    """一键创建测试候选人并启动面试（无需认证）"""
    # 查找第一个可用岗位
    result = await db.execute(select(Job).where(Job.status == 1).limit(1))
    job = result.scalar_one_or_none()
    if job is None:
        return error(404, "没有可用岗位，请先通过种子数据或HR后台创建岗位")

    # 每次创建新的测试候选人，规避每日面试限次
    candidate = Candidate(
        name="测试用户",
        phone=f"test_{uuid4().hex[:8]}",
    )
    db.add(candidate)
    await db.flush()

    # 创建并启动面试
    state = await interview_service.create_and_start_interview(
        db, candidate.id, job.id
    )

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
