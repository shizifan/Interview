import asyncio
import struct
import threading
import time
from abc import ABC, abstractmethod

import dashscope
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ASRService(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        ...


class MockASRService(ASRService):
    """Mock ASR服务，轮转返回预定义中文面试回答"""

    _responses = [
        "我会先靠边停车，然后打双闪灯，在车后放三角警示牌，检查刹车情况，再打电话给调度报告",
        "遇到大雾天气我会减速慢行，打开雾灯，保持足够车距，如果能见度太低就找安全地方停车等待",
        "出车前我会检查轮胎气压和磨损情况，看看刹车是否正常，检查灯光、油水，还有货物是否固定好",
        "我有五年的货车驾驶经验，主要跑长途运输，对路况比较熟悉",
        "如果感到疲劳我会找最近的服务区停车休息，绝对不会疲劳驾驶，一般开两三个小时就会休息一次",
    ]
    _index = 0

    async def transcribe(self, audio_data: bytes) -> str:
        if len(audio_data) < 100:
            return ""
        await asyncio.sleep(0.3)
        response = self._responses[MockASRService._index % len(self._responses)]
        MockASRService._index += 1
        return response


class RealASRService(ASRService):
    """真实ASR服务，使用DashScope Fun-ASR流式语音识别"""

    def __init__(self):
        dashscope.api_key = settings.DASHSCOPE_API_KEY

    @staticmethod
    def _parse_wav_header(audio_data: bytes) -> dict:
        """解析WAV头获取音频元信息，同时返回PCM数据偏移量"""
        info = {"valid": False}
        if len(audio_data) < 44 or audio_data[:4] != b"RIFF":
            return info
        info["valid"] = True
        info["channels"] = struct.unpack_from("<H", audio_data, 22)[0]
        info["sample_rate"] = struct.unpack_from("<I", audio_data, 24)[0]
        info["bits_per_sample"] = struct.unpack_from("<H", audio_data, 34)[0]
        info["data_size"] = struct.unpack_from("<I", audio_data, 40)[0]
        info["pcm_offset"] = 44
        sr = info["sample_rate"]
        ch = info["channels"]
        bps = info["bits_per_sample"]
        if sr > 0 and ch > 0 and bps > 0:
            info["duration_s"] = round(
                info["data_size"] / (sr * ch * bps // 8), 2
            )
        # 计算 PCM 峰值电平（抽样前 4000 样本）
        if bps == 16 and len(audio_data) > 44:
            pcm_bytes = audio_data[44 : 44 + 8000]  # 前 4000 个 int16 样本
            max_val = 0
            for i in range(0, len(pcm_bytes) - 1, 2):
                val = abs(struct.unpack_from("<h", pcm_bytes, i)[0])
                if val > max_val:
                    max_val = val
            info["peak_level"] = max_val
        return info

    def _sync_transcribe(self, audio_data: bytes) -> str:
        """使用DashScope流式ASR识别音频（start → send_audio_frame → stop）"""
        from dashscope.audio.asr import (
            Recognition,
            RecognitionCallback,
            RecognitionResult,
        )

        # 解析WAV获取采样率和PCM数据
        wav_info = self._parse_wav_header(audio_data)
        if wav_info["valid"]:
            sample_rate = wav_info["sample_rate"]
            pcm_data = audio_data[wav_info["pcm_offset"] :]
            audio_format = "pcm"
            logger.info(
                "asr_wav_info",
                sample_rate=sample_rate,
                channels=wav_info.get("channels"),
                bits=wav_info.get("bits_per_sample"),
                duration_s=wav_info.get("duration_s"),
                peak_level=wav_info.get("peak_level"),
                pcm_bytes=len(pcm_data),
            )
        else:
            # 非WAV格式，整段发送
            sample_rate = 16000
            pcm_data = audio_data
            audio_format = "wav"
            logger.warning("asr_non_wav_input", data_len=len(audio_data))

        # 收集识别结果
        sentences: list[str] = []
        done_event = threading.Event()
        asr_error: list[str] = []

        class _Callback(RecognitionCallback):
            def on_event(self, result: RecognitionResult) -> None:
                sentence = result.get_sentence()
                if isinstance(sentence, dict):
                    if RecognitionResult.is_sentence_end(sentence):
                        text = sentence.get("text", "")
                        if text:
                            sentences.append(text)
                            logger.info("asr_sentence", text=text)

            def on_complete(self) -> None:
                logger.info("asr_stream_complete", sentence_count=len(sentences))
                done_event.set()

            def on_error(self, result: RecognitionResult) -> None:
                msg = getattr(result, "message", str(result))
                asr_error.append(msg)
                logger.error("asr_stream_error", message=msg)
                done_event.set()

        callback = _Callback()
        recognition = Recognition(
            model=settings.ASR_MODEL,
            format=audio_format,
            sample_rate=sample_rate,
            callback=callback,
        )

        recognition.start()

        # 分块发送 PCM 数据（每块 3200 字节 ≈ 200ms @16kHz 16bit mono）
        chunk_size = 3200
        offset = 0
        while offset < len(pcm_data):
            chunk = pcm_data[offset : offset + chunk_size]
            recognition.send_audio_frame(chunk)
            offset += chunk_size
            time.sleep(0.05)

        recognition.stop()

        # 等待识别完成
        done_event.wait(timeout=30)

        if asr_error:
            raise RuntimeError(f"ASR API 错误: {asr_error[0]}")

        return "".join(sentences)

    async def transcribe(self, audio_data: bytes) -> str:
        if len(audio_data) < 1000:
            return ""

        try:
            text = await asyncio.to_thread(self._sync_transcribe, audio_data)
            logger.info("asr_result", text=text[:200] if text else "(empty)")
            return text
        except Exception as e:
            logger.error("asr_transcribe_error", error=str(e))
            return ""


_real_asr_instance: RealASRService | None = None


def get_asr_service() -> ASRService:
    if settings.AI_SERVICE_MODE == "mock":
        return MockASRService()
    global _real_asr_instance
    if _real_asr_instance is None:
        _real_asr_instance = RealASRService()
    return _real_asr_instance
