import asyncio
import os
import struct
import tempfile
from abc import ABC, abstractmethod
from http import HTTPStatus

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
        # 模拟少量音频数据=无效输入
        if len(audio_data) < 100:
            return ""

        await asyncio.sleep(0.3)  # 模拟处理延迟
        response = self._responses[MockASRService._index % len(self._responses)]
        MockASRService._index += 1
        return response


class RealASRService(ASRService):
    """真实ASR服务，使用DashScope Fun-ASR语音识别"""

    def __init__(self):
        dashscope.api_key = settings.DASHSCOPE_API_KEY

    @staticmethod
    def _detect_audio_format(audio_data: bytes) -> tuple[str, str]:
        """根据magic bytes检测音频格式，返回(后缀, format参数)"""
        if audio_data[:4] == b"RIFF":
            return ".wav", "wav"
        if audio_data[:4] == b"\x1a\x45\xdf\xa3":
            return ".webm", "webm"
        if audio_data[:3] == b"ID3" or audio_data[:2] == b"\xff\xfb":
            return ".mp3", "mp3"
        # 默认当作 wav
        return ".wav", "wav"

    @staticmethod
    def _detect_sample_rate(audio_data: bytes, fmt: str) -> int:
        """从音频数据中检测采样率，检测失败时返回16000"""
        if fmt == "wav" and len(audio_data) >= 28:
            return struct.unpack_from("<I", audio_data, 24)[0]
        if fmt == "mp3":
            sample_rates_v1 = [44100, 48000, 32000]
            sample_rates_v2 = [22050, 24000, 16000]
            offset = 0
            if audio_data[:3] == b"ID3" and len(audio_data) >= 10:
                sz = audio_data[6:10]
                offset = 10 + (sz[0] << 21 | sz[1] << 14 | sz[2] << 7 | sz[3])
            while offset < len(audio_data) - 4:
                if audio_data[offset] == 0xFF and (audio_data[offset + 1] & 0xE0) == 0xE0:
                    version_bits = (audio_data[offset + 1] >> 3) & 0x03
                    sr_index = (audio_data[offset + 2] >> 2) & 0x03
                    if sr_index < 3:
                        if version_bits == 3:
                            return sample_rates_v1[sr_index]
                        if version_bits in (0, 2):
                            return sample_rates_v2[sr_index]
                    break
                offset += 1
        return 16000

    def _sync_transcribe(self, audio_data: bytes) -> str:
        """同步调用DashScope ASR SDK"""
        from dashscope.audio.asr import Recognition

        suffix, fmt = self._detect_audio_format(audio_data)
        sample_rate = self._detect_sample_rate(audio_data, fmt)

        # 写入临时文件
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(audio_data)

            recognition = Recognition(
                model=settings.ASR_MODEL,
                format=fmt,
                sample_rate=sample_rate,
                language_hints=["zh", "en"],
                callback=None,
            )
            result = recognition.call(tmp_path)

            if result.status_code == HTTPStatus.OK:
                sentences = result.get_sentence()
                if sentences:
                    # get_sentence() 返回句子列表，拼接所有文本
                    texts = []
                    for s in sentences:
                        text = s.get("text", "") if isinstance(s, dict) else str(s)
                        if text:
                            texts.append(text)
                    return "".join(texts)
                return ""
            else:
                logger.error(
                    "asr_api_error",
                    status_code=result.status_code,
                    message=getattr(result, "message", ""),
                )
                raise RuntimeError(f"ASR API 错误: {result.status_code}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def transcribe(self, audio_data: bytes) -> str:
        if len(audio_data) < 1000:
            return ""

        try:
            text = await asyncio.to_thread(self._sync_transcribe, audio_data)
            logger.info("asr_result", text_length=len(text))
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
