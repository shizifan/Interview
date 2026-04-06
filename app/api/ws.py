import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.database import async_session_factory
from app.services import interview_service

logger = structlog.get_logger(__name__)

router = APIRouter()

# 活跃WebSocket连接注册表
_active_connections: dict[int, WebSocket] = {}


@router.websocket("/ws/interview/{interview_id}")
async def interview_websocket(websocket: WebSocket, interview_id: int):
    """面试实时通信WebSocket"""
    await websocket.accept()
    _active_connections[interview_id] = websocket

    # 音频缓冲区：收集前端发送的二进制音频块
    audio_buffer: bytearray = bytearray()

    try:
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "data": {"interview_id": interview_id},
        })

        # 消息处理循环
        while True:
            message = await websocket.receive()

            if "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                async with async_session_factory() as db:
                    try:
                        if msg_type == "audio_end":
                            # 音频结束 → ASR → 状态机
                            from app.services.asr_service import get_asr_service
                            asr = get_asr_service()

                            if audio_buffer:
                                # 有实际音频数据，进行ASR识别
                                audio_data = bytes(audio_buffer)
                                audio_buffer.clear()
                                text = await asr.transcribe(audio_data)
                            else:
                                # 兼容文本模式（前端直接传answer_text）
                                text = data.get("answer_text", "")
                                if not text:
                                    text = await asr.transcribe(b"")

                            logger.info(
                                "asr_complete",
                                interview_id=interview_id,
                                text_length=len(text),
                            )

                            await websocket.send_json({
                                "type": "asr_result",
                                "data": {"text": text},
                            })

                            # 提交回答
                            state = await interview_service.process_answer(db, interview_id, text)
                            await db.commit()

                            await websocket.send_json({
                                "type": "state_update",
                                "data": {
                                    "current_node": state.current_node,
                                    "current_question_index": state.current_question_index,
                                    "total_questions": len(state.questions),
                                    "tts_text": state.tts_text,
                                    "status": state.status,
                                    "score": state.total_score,
                                    "message": state.message,
                                },
                            })

                            if state.is_finished:
                                await websocket.send_json({
                                    "type": "interview_end",
                                    "data": {
                                        "total_score": state.total_score,
                                        "status": "completed",
                                    },
                                })

                        elif msg_type == "timeout":
                            state = await interview_service.handle_timeout(db, interview_id)
                            await db.commit()

                            await websocket.send_json({
                                "type": "state_update",
                                "data": {
                                    "current_node": state.current_node,
                                    "current_question_index": state.current_question_index,
                                    "total_questions": len(state.questions),
                                    "tts_text": state.tts_text,
                                    "status": state.status,
                                    "score": state.total_score,
                                    "message": state.message,
                                },
                            })

                        elif msg_type == "abort":
                            state = await interview_service.abort_interview(db, interview_id)
                            await db.commit()

                            await websocket.send_json({
                                "type": "state_update",
                                "data": {
                                    "current_node": "finish",
                                    "status": "interrupted",
                                    "message": "面试已中断",
                                },
                            })

                        elif msg_type == "tts_played":
                            # 前端TTS播放完毕确认，无需特殊处理
                            pass

                    except Exception as e:
                        await db.rollback()
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": str(e)},
                        })

            elif "bytes" in message:
                # 二进制音频数据，追加到缓冲区
                audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        # 连接断开，保存状态
        _active_connections.pop(interview_id, None)
        async with async_session_factory() as db:
            try:
                await interview_service.abort_interview(db, interview_id)
                await db.commit()
            except Exception:
                pass
    finally:
        _active_connections.pop(interview_id, None)
