from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score_pool import ScorePool
from app.models.candidate import Candidate


async def upsert_score(db: AsyncSession, candidate_id: int, job_id: int, doc_score: float) -> ScorePool:
    """插入或更新评分池记录"""
    result = await db.execute(
        select(ScorePool).where(
            and_(ScorePool.candidate_id == candidate_id, ScorePool.job_id == job_id)
        )
    )
    entry = result.scalar_one_or_none()

    if entry is None:
        entry = ScorePool(candidate_id=candidate_id, job_id=job_id, doc_score=doc_score)
        db.add(entry)
    else:
        entry.doc_score = doc_score

    await db.flush()
    await recalculate_ranks(db, job_id)
    return entry


async def recalculate_ranks(db: AsyncSession, job_id: int) -> None:
    """重新计算指定岗位的评分池排名"""
    result = await db.execute(
        select(ScorePool)
        .where(ScorePool.job_id == job_id)
        .order_by(ScorePool.doc_score.desc())
    )
    entries = result.scalars().all()

    for i, entry in enumerate(entries, 1):
        entry.rank = i

    await db.flush()
