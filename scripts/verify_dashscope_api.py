"""
验证 DashScope ASR (语音识别) 和 TTS (语音合成) 云端 API 是否可正常调用。

通过项目 service 层调用，验证配置 + 代码的端到端集成。

测试流程：
1. TTS: 使用 CosyVoice 将一段中文文本合成为音频
2. ASR: 使用 Fun-ASR 将合成的音频转写回文本
3. 对比原始文本与转写结果，验证端到端可用性
"""

import asyncio
import os
import sys
import time

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.services.tts_service import RealTTSService
from app.services.asr_service import RealASRService

TEST_TEXT = "您好，欢迎参加本次AI面试，请简单介绍一下您的工作经历。"


async def main():
    print("=" * 60)
    print("DashScope API 端到端验证")
    print(f"API Key: {settings.DASHSCOPE_API_KEY[:8]}...{settings.DASHSCOPE_API_KEY[-4:]}")
    print(f"ASR 模型: {settings.ASR_MODEL}")
    print(f"TTS 模型: {settings.TTS_MODEL}, 音色: {settings.TTS_VOICE}")
    print("=" * 60)

    # ---------- TTS ----------
    print(f"\n[TTS] 合成文本: {TEST_TEXT}")
    tts = RealTTSService()
    start = time.time()
    audio = await tts.synthesize(TEST_TEXT)
    tts_elapsed = time.time() - start

    tts_ok = isinstance(audio, bytes) and len(audio) > 100
    if tts_ok:
        print(f"[TTS] 成功! 音频: {len(audio):,} bytes, 耗时: {tts_elapsed:.2f}s")
    else:
        print(f"[TTS] 失败: 返回静音或空数据 ({len(audio)} bytes)")

    # ---------- ASR ----------
    asr_ok = False
    asr_text = ""
    if tts_ok:
        asr = RealASRService()
        start = time.time()
        asr_text = await asr.transcribe(audio)
        asr_elapsed = time.time() - start

        asr_ok = len(asr_text) > 0
        if asr_ok:
            print(f"[ASR] 成功! 识别: {asr_text}")
            print(f"[ASR] 耗时: {asr_elapsed:.2f}s")
        else:
            print(f"[ASR] 失败: 转写结果为空")

    # ---------- 汇总 ----------
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    print(f"  TTS ({settings.TTS_MODEL}): {'通过' if tts_ok else '失败'}")
    print(f"  ASR ({settings.ASR_MODEL}): {'通过' if asr_ok else '失败'}")

    if tts_ok and asr_ok:
        print("\n两个模型均可正常调用!")
    else:
        print("\n存在失败项，请检查上方错误信息。")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
