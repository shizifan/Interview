"""资质校验规则引擎：一票否决 + 四维度评分"""
import json
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate
from app.models.document import Document
from app.models.job import Job
from app.models.score_pool import ScorePool


# ===== 一票否决规则 =====

def check_veto_rules(docs_by_type: dict[int, dict], jobs: list[dict]) -> tuple[bool, str | None]:
    """
    一票否决检查。返回 (passed, reason)。
    docs_by_type: {doc_type: ocr_result_dict}
    jobs: [{required_license_type: [...], ...}]
    """
    # 规则1: 身份证必须上传
    if 1 not in docs_by_type:
        return False, "缺少身份证"

    # 规则2: 驾驶证必须上传
    if 2 not in docs_by_type:
        return False, "缺少驾驶证"

    # 规则3: 驾驶证有效期不能过期
    license_ocr = docs_by_type.get(2, {})
    valid_until = license_ocr.get("valid_until", "")
    if valid_until:
        try:
            exp_date = datetime.strptime(valid_until, "%Y-%m-%d")
            if exp_date < datetime.now():
                return False, "驾驶证已过期"
        except ValueError:
            pass

    # 规则4: 从业资格证有效期不能过期
    cert_ocr = docs_by_type.get(3, {})
    cert_valid = cert_ocr.get("valid_until", "")
    if cert_valid:
        try:
            exp_date = datetime.strptime(cert_valid, "%Y-%m-%d")
            if exp_date < datetime.now():
                return False, "从业资格证已过期"
        except ValueError:
            pass

    # 规则5: 准驾类型匹配（与所有发布中的岗位对比）
    candidate_license = license_ocr.get("license_type", "")
    for job in jobs:
        required = job.get("required_license_type") or []
        if required and candidate_license and candidate_license not in required:
            return False, f"准驾类型 {candidate_license} 不满足岗位 {job.get('name', '')} 要求的 {','.join(required)}"

    return True, None


# ===== 四维度评分 =====

def score_basic_qualification(docs_by_type: dict[int, dict]) -> float:
    """维度1: 基础资质 (满分40分) - 身份证+驾驶证完整性"""
    score = 0.0
    id_ocr = docs_by_type.get(1, {})
    if id_ocr.get("name") and id_ocr.get("id_number"):
        score += 20.0

    license_ocr = docs_by_type.get(2, {})
    if license_ocr.get("license_number"):
        score += 15.0
    if license_ocr.get("license_type"):
        score += 5.0

    return score


def score_driving_experience(candidate_work_exp: int, license_ocr: dict) -> float:
    """维度2: 驾龄/经验 (满分25分)"""
    score = 0.0
    # 工作年限: 每年5分, 最高15分
    score += min(candidate_work_exp * 5, 15.0)

    # 驾驶证初始日期推算驾龄
    issue_date_str = license_ocr.get("issue_date", "")
    if issue_date_str:
        try:
            issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
            driving_years = (datetime.now() - issue_date).days / 365.25
            score += min(driving_years * 2, 10.0)  # 每年2分, 最高10分
        except ValueError:
            pass

    return round(score, 1)


def score_additional_certs(docs_by_type: dict[int, dict]) -> float:
    """维度3: 附加证件 (满分20分)"""
    score = 0.0
    # 从业资格证
    cert_ocr = docs_by_type.get(3, {})
    if cert_ocr.get("cert_number"):
        score += 12.0
        # 有效期内加分
        valid_until = cert_ocr.get("valid_until", "")
        if valid_until:
            try:
                exp_date = datetime.strptime(valid_until, "%Y-%m-%d")
                if exp_date > datetime.now():
                    score += 4.0
            except ValueError:
                pass

    # 体检报告 (type=4)
    health_ocr = docs_by_type.get(4, {})
    if health_ocr:
        score += 4.0

    return score


def score_license_match(license_ocr: dict, jobs: list[dict]) -> float:
    """维度4: 准驾类型匹配 (满分15分)"""
    candidate_type = license_ocr.get("license_type", "")
    if not candidate_type:
        return 0.0

    if not jobs:
        return 10.0  # 无岗位要求时给基础分

    match_count = 0
    for job in jobs:
        required = job.get("required_license_type") or []
        if not required or candidate_type in required:
            match_count += 1

    if match_count == len(jobs):
        return 15.0
    elif match_count > 0:
        return 10.0
    return 0.0


# ===== 综合评定 =====

async def evaluate_candidate(db: AsyncSession, candidate_id: int) -> dict:
    """
    综合评定候选人资质，返回评定结果。
    在每次材料上传/OCR修正后调用。
    """
    # 获取候选人所有材料
    result = await db.execute(
        select(Document).where(Document.candidate_id == candidate_id)
    )
    docs = result.scalars().all()

    # 构建 docs_by_type
    docs_by_type: dict[int, dict] = {}
    for doc in docs:
        if doc.ocr_result:
            try:
                ocr_data = json.loads(doc.ocr_result)
            except (json.JSONDecodeError, TypeError):
                ocr_data = {}
            docs_by_type[doc.type] = ocr_data

    # 获取所有发布中的岗位
    job_result = await db.execute(select(Job).where(Job.status == 1))
    active_jobs = job_result.scalars().all()
    jobs_data = []
    for j in active_jobs:
        req_types = []
        if j.required_license_type:
            try:
                req_types = json.loads(j.required_license_type)
            except (json.JSONDecodeError, TypeError):
                req_types = []
        jobs_data.append({"name": j.name, "required_license_type": req_types, "id": j.id})

    # 获取候选人
    c_result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = c_result.scalar_one_or_none()
    if not candidate:
        return {"passed": False, "reason": "候选人不存在"}

    # 一票否决
    passed, veto_reason = check_veto_rules(docs_by_type, jobs_data)

    # 四维度评分
    license_ocr = docs_by_type.get(2, {})
    dim1 = score_basic_qualification(docs_by_type)
    dim2 = score_driving_experience(candidate.work_experience, license_ocr)
    dim3 = score_additional_certs(docs_by_type)
    dim4 = score_license_match(license_ocr, jobs_data)
    doc_score = round(dim1 + dim2 + dim3 + dim4, 1)

    detail = {
        "veto_passed": passed,
        "veto_reason": veto_reason,
        "dimensions": {
            "basic_qualification": dim1,
            "driving_experience": dim2,
            "additional_certs": dim3,
            "license_match": dim4,
        },
        "doc_score": doc_score,
    }

    # 更新候选人
    candidate.total_score = doc_score
    candidate.qualification_detail = json.dumps(detail, ensure_ascii=False)
    if not passed:
        candidate.status = 3  # 拒绝(一票否决)
    elif doc_score > 0 and candidate.status == 0:
        candidate.status = 1  # 材料已提交

    # 更新评分池（针对每个发布中的岗位）
    for job_data in jobs_data:
        pool_result = await db.execute(
            select(ScorePool).where(
                and_(ScorePool.candidate_id == candidate_id, ScorePool.job_id == job_data["id"])
            )
        )
        entry = pool_result.scalar_one_or_none()
        if entry is None:
            entry = ScorePool(
                candidate_id=candidate_id,
                job_id=job_data["id"],
                doc_score=doc_score,
                total_score=round(doc_score * 0.4, 1),
            )
            db.add(entry)
        else:
            entry.doc_score = doc_score
            entry.total_score = round(doc_score * 0.4 + entry.interview_score * 0.6, 1)

    await db.flush()

    # 重新计算排名
    for job_data in jobs_data:
        await _recalculate_ranks(db, job_data["id"])

    return detail


async def _recalculate_ranks(db: AsyncSession, job_id: int) -> None:
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
