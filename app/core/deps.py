from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.core.security import decode_access_token


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _extract_token(authorization: str | None = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    return authorization[7:]


async def get_current_candidate(
    token: str = Depends(_extract_token),
    db: AsyncSession = Depends(get_db),
):
    """从 JWT 解析候选人身份"""
    from app.models.candidate import Candidate

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期")
    if payload.get("role") != "candidate":
        raise HTTPException(status_code=401, detail="无权访问候选人接口")
    candidate_id = int(payload["sub"])
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=401, detail="候选人不存在")
    return candidate


async def get_current_hr_user(
    token: str = Depends(_extract_token),
    db: AsyncSession = Depends(get_db),
):
    """从 JWT 解析 HR 用户身份"""
    from app.models.hr_user import HRUser

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期")
    if payload.get("role") != "hr":
        raise HTTPException(status_code=401, detail="无权访问HR管理接口")
    user_id = int(payload["sub"])
    result = await db.execute(select(HRUser).where(HRUser.id == user_id, HRUser.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="HR用户不存在或已禁用")
    return user
