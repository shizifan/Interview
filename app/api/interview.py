from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.response import success
from app.schemas.interview import InterviewState, StartInterviewRequest, SubmitAnswerRequest
from app.services import interview_service

router = APIRouter(tags=["面试流程"])


@router.post("/start")
async def create_and_start(data: StartInterviewRequest, db: AsyncSession = Depends(get_db)):
    """创建并开始面试（前端通过candidate_id+job_id发起）"""
    state = await interview_service.create_and_start_interview(db, data.candidate_id, data.job_id)
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


@router.get("/{interview_id}/state")
async def get_state(interview_id: int, db: AsyncSession = Depends(get_db)):
    """获取面试当前状态"""
    state = await interview_service.get_interview_state(db, interview_id)
    if state is None:
        return {"code": 404, "message": "面试状态不存在", "data": None}
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


@router.post("/{interview_id}/start")
async def start_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    """开始面试"""
    state = await interview_service.start_interview(db, interview_id)
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


@router.post("/{interview_id}/recover")
async def recover_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    """恢复中断面试"""
    state = await interview_service.recover_interview(db, interview_id)
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


@router.post("/{interview_id}/submit-answer")
async def submit_answer(
    interview_id: int, data: SubmitAnswerRequest, db: AsyncSession = Depends(get_db)
):
    """提交回答"""
    state = await interview_service.process_answer(db, interview_id, data.answer_text)
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


@router.post("/{interview_id}/timeout")
async def timeout(interview_id: int, db: AsyncSession = Depends(get_db)):
    """超时通知"""
    state = await interview_service.handle_timeout(db, interview_id)
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


@router.post("/{interview_id}/abort")
async def abort(interview_id: int, db: AsyncSession = Depends(get_db)):
    """中断面试"""
    state = await interview_service.abort_interview(db, interview_id)
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
