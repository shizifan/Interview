import os
from datetime import datetime

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.document import Document
from app.models.candidate import Candidate
from app.models.score_pool import ScorePool
from app.services.ocr_service import get_ocr_service


async def upload_document(
    db: AsyncSession,
    candidate_id: int,
    doc_type: int,
    file_content: bytes,
    file_name: str,
) -> Document:
    """上传材料并触发OCR处理"""
    # 保存文件
    date_dir = datetime.now().strftime("%Y-%m")
    save_dir = os.path.join(settings.UPLOAD_DIR, date_dir, str(candidate_id))
    os.makedirs(save_dir, exist_ok=True)

    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    ext = os.path.splitext(file_name)[1] or ".jpg"
    saved_name = f"{doc_type}_{timestamp}{ext}"
    file_path = os.path.join(save_dir, saved_name)

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)

    # 创建文档记录
    doc = Document(
        candidate_id=candidate_id,
        type=doc_type,
        file_path=file_path,
        file_name=file_name,
        file_size=len(file_content),
        status=1,  # 审核中
    )
    db.add(doc)
    await db.flush()

    # 触发OCR
    ocr_service = get_ocr_service()
    ocr_result = await ocr_service.recognize(file_path, doc_type)

    import json
    doc.ocr_result = json.dumps(ocr_result, ensure_ascii=False)

    # 规则校验和评分
    score = _calculate_doc_score(doc_type, ocr_result)
    doc.score = score
    doc.status = 2  # 通过

    # 触发资质综合评定
    from app.services.qualification_service import evaluate_candidate
    await evaluate_candidate(db, candidate_id)
    await db.flush()

    return doc


def _calculate_doc_score(doc_type: int, ocr_result: dict) -> float:
    """根据材料类型和OCR结果计算得分"""
    score = 0.0

    if doc_type == 1:  # 身份证
        if ocr_result.get("name") and ocr_result.get("id_number"):
            score = 20.0  # 基础资质分（满分占比的一部分）
    elif doc_type == 2:  # 驾驶证
        if ocr_result.get("license_number"):
            score = 30.0
            # 检查有效期
            valid_until = ocr_result.get("valid_until", "")
            if valid_until:
                try:
                    exp_date = datetime.strptime(valid_until, "%Y-%m-%d")
                    if exp_date > datetime.now():
                        score += 10.0  # 有效期加分
                except ValueError:
                    pass
    elif doc_type == 3:  # 从业资格证
        if ocr_result.get("cert_number"):
            score = 20.0
            valid_until = ocr_result.get("valid_until", "")
            if valid_until:
                try:
                    exp_date = datetime.strptime(valid_until, "%Y-%m-%d")
                    if exp_date > datetime.now():
                        score += 10.0
                except ValueError:
                    pass
    else:
        score = 5.0  # 其他材料

    return score


async def _update_candidate_score(db: AsyncSession, candidate_id: int) -> None:
    """重新计算候选人综合得分"""
    result = await db.execute(
        select(Document).where(Document.candidate_id == candidate_id)
    )
    docs = result.scalars().all()

    # 基础资质分（60%）= 所有材料得分之和，最高60分
    doc_total = min(sum(d.score for d in docs), 60.0)

    # 经验年限分（20%）
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate:
        exp_score = min(candidate.work_experience * 4, 20.0)  # 每年4分，最高20分
        # 附加材料分（20%）= 材料完整度
        completeness = min(len(docs) / 3 * 20, 20.0)  # 3种材料齐全得满分
        candidate.total_score = round(doc_total + exp_score + completeness, 1)
        if candidate.total_score > 0 and candidate.status == 0:
            candidate.status = 2  # 自动通过审核


async def list_documents(db: AsyncSession, candidate_id: int) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.candidate_id == candidate_id).order_by(Document.id.desc())
    )
    return list(result.scalars().all())


async def update_ocr_result(
    db: AsyncSession, document_id: int, candidate_id: int, corrected_fields: dict[str, str]
) -> Document | None:
    """更新 OCR 识别结果（候选人修正后）"""
    import json

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.candidate_id == candidate_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        return None

    # 合并修正字段到现有 OCR 结果
    existing: dict = {}
    if doc.ocr_result:
        try:
            existing = json.loads(doc.ocr_result)
        except (json.JSONDecodeError, TypeError):
            existing = {}

    existing.update(corrected_fields)
    doc.ocr_result = json.dumps(existing, ensure_ascii=False)

    # 重新计算单文档得分
    doc.score = _calculate_doc_score(doc.type, existing)

    # 触发资质综合评定
    from app.services.qualification_service import evaluate_candidate
    await evaluate_candidate(db, candidate_id)
    await db.flush()

    return doc
