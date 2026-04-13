from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score_pool import ScorePool


async def upsert_score(db: AsyncSession, candidate_id: int, job_id: int, doc_score: float) -> ScorePool:
    """插入或更新评分池记录（材料分）"""
    result = await db.execute(
        select(ScorePool).where(
            and_(ScorePool.candidate_id == candidate_id, ScorePool.job_id == job_id)
        )
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        entry = ScorePool(
            candidate_id=candidate_id,
            job_id=job_id,
            doc_score=doc_score,
            total_score=round(doc_score * 0.4, 1),
        )
        db.add(entry)
    else:
        entry.doc_score = doc_score
        entry.total_score = round(doc_score * 0.4 + entry.interview_score * 0.6, 1)

    await db.flush()
    await recalculate_ranks(db, job_id)
    return entry


async def update_interview_score(
    db: AsyncSession, candidate_id: int, job_id: int, interview_score: float
) -> ScorePool:
    """面试完成后更新面试分并重算综合分"""
    result = await db.execute(
        select(ScorePool).where(
            and_(ScorePool.candidate_id == candidate_id, ScorePool.job_id == job_id)
        )
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        entry = ScorePool(
            candidate_id=candidate_id,
            job_id=job_id,
            interview_score=interview_score,
            total_score=round(interview_score * 0.6, 1),
        )
        db.add(entry)
    else:
        entry.interview_score = interview_score
        entry.total_score = round(entry.doc_score * 0.4 + interview_score * 0.6, 1)

    await db.flush()
    await recalculate_ranks(db, job_id)
    return entry


async def recalculate_ranks(db: AsyncSession, job_id: int) -> None:
    """重新计算指定岗位的评分池排名"""
    result = await db.execute(
        select(ScorePool)
        .where(ScorePool.job_id == job_id)
        .order_by(ScorePool.total_score.desc())
    )
    entries = result.scalars().all()

    for i, entry in enumerate(entries, 1):
        entry.rank = i

    await db.flush()
