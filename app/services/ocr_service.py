import base64
import json
import os
import re
import time
from abc import ABC, abstractmethod

import aiofiles
import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

_MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

_PROMPTS: dict[int, str] = {
    1: (
        "请识别这张身份证图片，提取以下信息并以JSON格式输出：\n"
        '{"name": "姓名", "id_number": "身份证号", "gender": "性别", '
        '"birth_date": "出生日期(YYYY-MM-DD格式)", "address": "住址"}'
    ),
    2: (
        "请识别这张驾驶证图片，提取以下信息并以JSON格式输出：\n"
        '{"name": "姓名", "license_number": "证号", "class": "准驾车型", '
        '"valid_from": "有效期起始日期(YYYY-MM-DD格式)", '
        '"valid_until": "有效期截止日期(YYYY-MM-DD格式)", '
        '"issue_authority": "发证机关"}'
    ),
    3: (
        "请识别这张从业资格证图片，提取以下信息并以JSON格式输出：\n"
        '{"name": "姓名", "cert_number": "证书编号", '
        '"cert_type": "证书类型", '
        '"valid_until": "有效期截止日期(YYYY-MM-DD格式)"}'
    ),
    4: (
        "请识别这张图片中的所有文字信息，以JSON格式输出：\n"
        '{"raw_text": "识别出的完整文字内容"}'
    ),
}

_SYSTEM_PROMPT = (
    "你是一个专业的证件OCR识别助手。请仔细分析图片中的证件信息，提取所有关键字段。\n"
    "请严格按照JSON格式输出，不要输出其他内容。如果某个字段无法识别，设为空字符串。"
)


class OCRService(ABC):
    @abstractmethod
    async def recognize(self, file_path: str, doc_type: int) -> dict:
        ...


class MockOCRService(OCRService):
    """Mock OCR服务，按材料类型返回预定义结果"""

    async def recognize(self, file_path: str, doc_type: int) -> dict:
        if doc_type == 1:  # 身份证
            return {
                "name": "张三",
                "id_number": "110101199001011234",
                "gender": "男",
                "birth_date": "1990-01-01",
                "address": "北京市朝阳区建国路88号",
            }
        elif doc_type == 2:  # 驾驶证
            return {
                "name": "张三",
                "license_number": "110101199001011234",
                "class": "A2",
                "valid_from": "2020-01-01",
                "valid_until": "2026-12-01",
                "issue_authority": "北京市公安局交通管理局",
            }
        elif doc_type == 3:  # 从业资格证
            return {
                "name": "张三",
                "cert_number": "CYRY202301001",
                "cert_type": "道路运输从业资格证",
                "valid_until": "2027-06-01",
            }
        else:
            return {"raw_text": "Mock OCR识别结果"}


class RealOCRService(OCRService):
    """真实OCR服务，调用Qwen2-VL-72B多模态模型"""

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.OCR_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def _read_image_base64(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        mime = _MIME_MAP.get(ext, "image/jpeg")
        async with aiofiles.open(file_path, "rb") as f:
            data = await f.read()
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"

    @staticmethod
    def _extract_json(text: str) -> dict:
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        md_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
        if md_match:
            cleaned = md_match.group(1).strip()
        brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if brace_match:
            return json.loads(brace_match.group())
        raise ValueError(f"无法从OCR响应中提取JSON: {text[:200]}")

    async def recognize(self, file_path: str, doc_type: int) -> dict:
        image_url = await self._read_image_base64(file_path)
        user_prompt = _PROMPTS.get(doc_type, _PROMPTS[4])

        payload = {
            "model": settings.OCR_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            "temperature": 0,
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {settings.OCR_API_KEY}",
            "Content-Type": "application/json",
        }

        start = time.monotonic()
        try:
            resp = await self._client.post(
                settings.OCR_API_URL, json=payload, headers=headers
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code != 200:
                logger.error(
                    "ocr_api_error",
                    status_code=resp.status_code,
                    body=resp.text[:500],
                    latency_ms=latency_ms,
                )
                raise RuntimeError(f"OCR API 返回 {resp.status_code}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info("ocr_response", doc_type=doc_type, latency_ms=latency_ms)
            return self._extract_json(content)
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.error("ocr_network_error", error=str(e))
            raise RuntimeError(f"OCR服务网络异常: {e}") from e
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("ocr_parse_fallback", error=str(e))
            return {"error": "OCR识别失败，请重新上传清晰图片"}


_real_ocr_instance: RealOCRService | None = None


def get_ocr_service() -> OCRService:
    if settings.AI_SERVICE_MODE == "mock":
        return MockOCRService()
    global _real_ocr_instance
    if _real_ocr_instance is None:
        _real_ocr_instance = RealOCRService()
    return _real_ocr_instance
