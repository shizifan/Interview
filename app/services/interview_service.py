import json
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BusinessError, ERR_DAILY_LIMIT, ERR_INTERVIEW_STATUS, ERR_RECOVERY_EXPIRED, ERR_NO_QUESTIONS
from app.models.interview import Interview
from app.models.question import Question
from app.models.interview_answer import InterviewAnswer
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.interview_state_machine import InterviewStateMachine, InterviewGraphState
from app.services.llm_service import get_llm_service


async def create_and_start_interview(db: AsyncSession, candidate_id: int, job_id: int) -> InterviewGraphState:
    """创建面试记录并开始面试"""
    interview = Interview(candidate_id=candidate_id, job_id=job_id, status=0)
    db.add(interview)
    await db.flush()
    return await start_interview(db, interview.id)


async def start_interview(db: AsyncSession, interview_id: int) -> InterviewGraphState:
    """开始面试"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        raise BusinessError(404, "面试记录不存在")

    if interview.status != 0:
        raise BusinessError(ERR_INTERVIEW_STATUS, "面试状态不正确，无法开始")

    # 检查每日限次
    today = datetime.now().strftime("%Y-%m-%d")
    count_result = await db.execute(
        select(func.count()).select_from(Interview).where(
            and_(
                Interview.candidate_id == interview.candidate_id,
                Interview.job_id == interview.job_id,
                Interview.start_time.like(f"{today}%"),
                Interview.status.in_([1, 2]),
            )
        )
    )
    today_count = count_result.scalar() or 0
    if today_count >= settings.MAX_DAILY_INTERVIEWS:
        raise BusinessError(ERR_DAILY_LIMIT, f"每日面试次数已达上限（{settings.MAX_DAILY_INTERVIEWS}次）")

    # 加载题目
    q_result = await db.execute(
        select(Question).where(
            and_(Question.job_id == interview.job_id, Question.is_active == True)
        ).order_by(Question.id)
    )
    questions = q_result.scalars().all()
    if not questions:
        raise BusinessError(ERR_NO_QUESTIONS, "该岗位题库为空，无法开始面试")

    questions_data = [
        {
            "id": q.id,
            "content": q.content,
            "score_points": q.score_points,
            "follow_up_scripts": q.follow_up_scripts or "[]",
        }
        for q in questions
    ]

    # 初始化状态机
    sm = InterviewStateMachine()
    state = await sm.initialize(
        interview_id=interview.id,
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        questions=questions_data,
    )

    # 更新面试记录
    interview.status = 1
    interview.start_time = datetime.now().isoformat()
    interview.current_node = state.current_node
    interview.current_question_index = state.current_question_index
    interview.interview_data = state.to_json()
    await db.flush()

    return state


async def recover_interview(db: AsyncSession, interview_id: int) -> InterviewGraphState:
    """恢复中断的面试"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        raise BusinessError(404, "面试记录不存在")

    if interview.status != 3:
        raise BusinessError(ERR_INTERVIEW_STATUS, "只有已中断的面试才能恢复")

    # 检查恢复窗口
    if interview.updated_at:
        try:
            interrupted_time = datetime.fromisoformat(interview.updated_at)
            if datetime.now() - interrupted_time > timedelta(hours=settings.INTERVIEW_RECOVERY_HOURS):
                raise BusinessError(ERR_RECOVERY_EXPIRED, "面试恢复窗口已过期（24小时内可恢复）")
        except ValueError:
            pass

    if not interview.interview_data:
        raise BusinessError(ERR_INTERVIEW_STATUS, "无法恢复：面试状态数据丢失")

    state = InterviewGraphState.from_json(interview.interview_data)
    state.status = "in_progress"

    interview.status = 1
    interview.interview_data = state.to_json()
    await db.flush()

    return state


async def process_answer(db: AsyncSession, interview_id: int, answer_text: str) -> InterviewGraphState:
    """处理回答"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        raise BusinessError(404, "面试记录不存在")
    if interview.status != 1:
        raise BusinessError(ERR_INTERVIEW_STATUS, "面试未在进行中")

    state = InterviewGraphState.from_json(interview.interview_data)
    sm = InterviewStateMachine()
    state = await sm.advance(state, "answer_received", {"answer_text": answer_text})

    # 持久化
    await _persist_state(db, interview, state)
    return state


async def handle_timeout(db: AsyncSession, interview_id: int) -> InterviewGraphState:
    """处理超时"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        raise BusinessError(404, "面试记录不存在")
    if interview.status != 1:
        raise BusinessError(ERR_INTERVIEW_STATUS, "面试未在进行中")

    state = InterviewGraphState.from_json(interview.interview_data)
    sm = InterviewStateMachine()
    state = await sm.advance(state, "timeout")

    await _persist_state(db, interview, state)
    return state


async def abort_interview(db: AsyncSession, interview_id: int) -> InterviewGraphState:
    """中断面试"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None:
        raise BusinessError(404, "面试记录不存在")
    if interview.status != 1:
        raise BusinessError(ERR_INTERVIEW_STATUS, "面试未在进行中")

    state = InterviewGraphState.from_json(interview.interview_data)
    sm = InterviewStateMachine()
    state = await sm.advance(state, "abort")

    interview.status = 3  # 已中断
    interview.current_node = state.current_node
    interview.interview_data = state.to_json()
    await db.flush()

    return state


async def get_interview_state(db: AsyncSession, interview_id: int) -> InterviewGraphState | None:
    """获取面试状态"""
    result = await db.execute(select(Interview).where(Interview.id == interview_id))
    interview = result.scalar_one_or_none()
    if interview is None or not interview.interview_data:
        return None
    return InterviewGraphState.from_json(interview.interview_data)


async def _persist_state(db: AsyncSession, interview: Interview, state: InterviewGraphState) -> None:
    """持久化状态到数据库"""
    interview.current_node = state.current_node
    interview.current_question_index = state.current_question_index
    interview.interview_data = state.to_json()
    interview.score = state.total_score

    if state.is_finished:
        interview.status = 2  # 已完成
        interview.end_time = datetime.now().isoformat()

        # 保存每题回答到interview_answer表
        for ans in state.answers:
            answer = InterviewAnswer(
                interview_id=interview.id,
                question_id=ans["question_id"],
                question_order=ans["question_order"],
                answer_text=ans.get("answer_text", ""),
                follow_up_count=ans.get("follow_up_count", 0),
                score=ans.get("score", 0),
                score_detail=json.dumps(ans.get("score_detail", {}), ensure_ascii=False),
            )
            db.add(answer)

        # 生成评估报告
        llm = get_llm_service()
        candidate_result = await db.execute(select(Candidate).where(Candidate.id == interview.candidate_id))
        candidate = candidate_result.scalar_one_or_none()
        job_result = await db.execute(select(Job).where(Job.id == interview.job_id))
        job = job_result.scalar_one_or_none()

        report = await llm.generate_report({
            "candidate_name": candidate.name if candidate else "未知",
            "job_name": job.name if job else "未知",
            "total_score": state.total_score,
            "answers": state.answers,
        })
        interview.report_content = report

        # 更新评分池面试分
        from app.services.score_pool_service import update_interview_score
        await update_interview_score(db, interview.candidate_id, interview.job_id, state.total_score)

    await db.flush()
