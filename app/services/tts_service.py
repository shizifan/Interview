import asyncio
import struct
from abc import ABC, abstractmethod

import dashscope
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def _generate_silent_wav(duration_seconds: float = 1.0) -> bytes:
    """生成静音WAV文件"""
    sample_rate = 16000
    bits_per_sample = 16
    channels = 1
    num_samples = int(sample_rate * duration_seconds)
    data_size = num_samples * channels * (bits_per_sample // 8)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # chunk size
        1,   # PCM format
        channels,
        sample_rate,
        sample_rate * channels * (bits_per_sample // 8),
        channels * (bits_per_sample // 8),
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + b"\x00" * data_size


class TTSService(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        ...


class MockTTSService(TTSService):
    """Mock TTS服务，返回最小静音WAV文件"""

    def __init__(self):
        self._silent_wav = _generate_silent_wav()

    async def synthesize(self, text: str) -> bytes:
        await asyncio.sleep(0.5)  # 模拟合成延迟
        return self._silent_wav


class RealTTSService(TTSService):
    """真实TTS服务，使用DashScope CosyVoice语音合成"""

    def __init__(self):
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        self._silent_wav = _generate_silent_wav()

    def _sync_synthesize(self, text: str) -> bytes:
        """同步调用DashScope TTS SDK"""
        from dashscope.audio.tts_v2 import SpeechSynthesizer

        synthesizer = SpeechSynthesizer(
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE,
        )
        audio = synthesizer.call(text)

        if isinstance(audio, bytes) and len(audio) > 0:
            return audio
        logger.warning("tts_empty_result", text_length=len(text))
        return self._silent_wav

    async def synthesize(self, text: str) -> bytes:
        if not text or not text.strip():
            return self._silent_wav

        try:
            audio = await asyncio.to_thread(self._sync_synthesize, text)
            logger.info("tts_result", text_length=len(text), audio_bytes=len(audio))
            return audio
        except Exception as e:
            logger.error("tts_synthesize_error", error=str(e))
            return self._silent_wav


_real_tts_instance: RealTTSService | None = None


def get_tts_service() -> TTSService:
    if settings.AI_SERVICE_MODE == "mock":
        return MockTTSService()
    global _real_tts_instance
    if _real_tts_instance is None:
        _real_tts_instance = RealTTSService()
    return _real_tts_instance
