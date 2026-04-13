from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate


async def enter_system(db: AsyncSession, phone: str) -> Candidate:
    """通过手机号进入系统，自动查找或创建候选人记录"""
    result = await db.execute(select(Candidate).where(Candidate.phone == phone))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        candidate = Candidate(phone=phone)
        db.add(candidate)
        await db.flush()
    return candidate


async def get_candidate(db: AsyncSession, candidate_id: int) -> Candidate | None:
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    return result.scalar_one_or_none()


async def update_profile(db: AsyncSession, candidate_id: int, data: dict) -> Candidate | None:
    candidate = await get_candidate(db, candidate_id)
    if candidate is None:
        return None
    for key, value in data.items():
        if value is not None and hasattr(candidate, key):
            setattr(candidate, key, value)
    await db.flush()
    return candidate
