import asyncio
import json
import re
import time
from abc import ABC, abstractmethod

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class LLMService(ABC):
    @abstractmethod
    async def judge_score_points(
        self, question_content: str, score_points: list[str], answer_text: str
    ) -> dict:
        ...

    @abstractmethod
    async def detect_intent(self, answer_text: str) -> str:
        ...

    @abstractmethod
    async def generate_report(self, interview_data: dict) -> str:
        ...


class MockLLMService(LLMService):
    """Mock LLM服务，使用关键词匹配和模板"""

    async def judge_score_points(
        self, question_content: str, score_points: list[str], answer_text: str
    ) -> dict:
        await asyncio.sleep(0.3)

        answer_lower = answer_text.lower()
        covered = []
        uncovered = []

        for point in score_points:
            # 将得分点拆分为关键词进行匹配
            keywords = [kw.strip() for kw in point.replace("、", ",").split(",") if kw.strip()]
            if not keywords:
                keywords = [point]

            matched = any(kw in answer_lower for kw in keywords)
            if matched:
                covered.append(point)
            else:
                uncovered.append(point)

        total = len(score_points)
        score = round(len(covered) / total * 10, 1) if total > 0 else 0

        return {
            "covered_points": covered,
            "uncovered_points": uncovered,
            "score": score,
            "reasoning": f"回答覆盖了{len(covered)}/{total}个评分关键点",
        }

    async def detect_intent(self, answer_text: str) -> str:
        if not answer_text or len(answer_text.strip()) < 5:
            return "empty"

        replay_keywords = ["没听清", "再说一遍", "重复一遍", "没有听清", "再说一次", "什么"]
        if any(kw in answer_text for kw in replay_keywords):
            return "replay_request"

        return "normal"

    async def generate_report(self, interview_data: dict) -> str:
        candidate_name = interview_data.get("candidate_name", "候选人")
        job_name = interview_data.get("job_name", "岗位")
        total_score = interview_data.get("total_score", 0)
        answers = interview_data.get("answers", [])

        # 计算各维度分数
        total_questions = len(answers) if answers else 5
        avg_score = total_score / total_questions if total_questions > 0 else 0

        skill_score = min(avg_score * 1.2, 10)
        exp_score = min(avg_score * 1.0, 10)
        comm_score = min(avg_score * 0.8, 10)

        answer_details = ""
        for i, ans in enumerate(answers, 1):
            answer_details += f"\n### 第{i}题\n"
            answer_details += f"- **回答内容**: {ans.get('answer_text', '未作答')}\n"
            answer_details += f"- **得分**: {ans.get('score', 0)}/10\n"

        report = f"""# 面试评估报告

## 基本信息
- **候选人**: {candidate_name}
- **应聘岗位**: {job_name}
- **面试总分**: {total_score:.1f}/100
- **评估结果**: {"通过" if total_score >= 60 else "未通过"}

## 多维度评估

### 专业技能 ({skill_score:.1f}/10)
候选人在专业知识和操作技能方面{"表现良好" if skill_score >= 6 else "有待提升"}。

### 工作经验 ({exp_score:.1f}/10)
根据回答内容判断，候选人{"具备相关工作经验" if exp_score >= 6 else "经验相对不足"}。

### 沟通表达 ({comm_score:.1f}/10)
候选人的表达能力{"清晰流畅" if comm_score >= 6 else "需要加强"}。

## 各题详情
{answer_details}

## 综合建议
{"建议录用，候选人综合表现良好。" if total_score >= 60 else "建议再次评估或安排其他岗位。"}
"""
        return report


class RealLLMService(LLMService):
    """真实LLM服务，调用Qwen3-235B OpenAI兼容API"""

    def __init__(self):
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.LLM_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    async def _chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }
        headers = {
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        start = time.monotonic()
        resp = await self._client.post(
            settings.LLM_API_URL, json=payload, headers=headers
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        if resp.status_code != 200:
            logger.error(
                "llm_api_error",
                status_code=resp.status_code,
                body=resp.text[:500],
                latency_ms=latency_ms,
            )
            raise RuntimeError(f"LLM API 返回 {resp.status_code}")

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        logger.info("llm_response", latency_ms=latency_ms, length=len(content))
        return content

    @staticmethod
    def _extract_json(text: str) -> dict:
        """从LLM响应中提取JSON，处理<think>标签和markdown代码块"""
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        md_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
        if md_match:
            cleaned = md_match.group(1).strip()
        brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if brace_match:
            return json.loads(brace_match.group())
        raise ValueError(f"无法从LLM响应中提取JSON: {text[:200]}")

    async def judge_score_points(
        self, question_content: str, score_points: list[str], answer_text: str
    ) -> dict:
        points_str = "\n".join(f"{i+1}. {p}" for i, p in enumerate(score_points))
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个蓝领岗位面试评分助手。你的任务是对候选人的回答进行评分。\n"
                    "你需要判断候选人的回答覆盖了哪些评分要点，哪些未覆盖。\n"
                    "含义相近即可视为覆盖，不需要完全一致。\n"
                    "请严格按照JSON格式输出结果，不要输出任何其他内容。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"面试题目：{question_content}\n\n"
                    f"评分要点（共{len(score_points)}个）：\n{points_str}\n\n"
                    f"候选人回答：\n{answer_text}\n\n"
                    '请输出JSON：{{"covered_points": ["已覆盖的要点"], '
                    '"uncovered_points": ["未覆盖的要点"], '
                    '"score": 分数(0-10按覆盖比例), '
                    '"reasoning": "简要评分理由"}}'
                ),
            },
        ]
        try:
            raw = await self._chat(messages, temperature=0.1)
            result = self._extract_json(raw)
            return {
                "covered_points": result.get("covered_points", []),
                "uncovered_points": result.get("uncovered_points", score_points),
                "score": float(result.get("score", 0)),
                "reasoning": result.get("reasoning", ""),
            }
        except Exception as e:
            logger.warning("llm_judge_fallback", error=str(e))
            return {
                "covered_points": [],
                "uncovered_points": score_points,
                "score": 0,
                "reasoning": "AI评分服务异常，使用默认评分",
            }

    async def detect_intent(self, answer_text: str) -> str:
        if not answer_text or len(answer_text.strip()) < 5:
            return "empty"
        replay_keywords = ["没听清", "再说一遍", "重复一遍", "没有听清", "再说一次", "什么"]
        if any(kw in answer_text for kw in replay_keywords):
            return "replay_request"

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个语音意图识别助手。请判断用户语音转文字的结果属于以下哪种意图：\n"
                    '- "empty"：无有效内容（空白、噪音、无意义的语气词）\n'
                    '- "replay_request"：请求重复问题（没听清、再说一遍等）\n'
                    '- "normal"：正常回答\n\n'
                    "只输出意图标签，不要解释。"
                ),
            },
            {"role": "user", "content": f"语音识别文本：{answer_text}\n\n意图："},
        ]
        try:
            raw = await self._chat(messages, temperature=0, max_tokens=10)
            cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip().lower()
            if cleaned in ("empty", "replay_request", "normal"):
                return cleaned
            return "normal"
        except Exception as e:
            logger.warning("llm_intent_fallback", error=str(e))
            return "normal"

    async def generate_report(self, interview_data: dict) -> str:
        candidate_name = interview_data.get("candidate_name", "候选人")
        job_name = interview_data.get("job_name", "岗位")
        total_score = interview_data.get("total_score", 0)
        answers = interview_data.get("answers", [])

        answers_str = ""
        for i, ans in enumerate(answers, 1):
            answers_str += (
                f"第{i}题：\n"
                f"  回答：{ans.get('answer_text', '未作答')}\n"
                f"  得分：{ans.get('score', 0)}/10\n"
                f"  追问次数：{ans.get('follow_up_count', 0)}\n\n"
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专业的蓝领岗位招聘面试评估师。请根据面试数据生成一份详细的Markdown格式面试评估报告。\n"
                    "报告应包含：基本信息、各题表现分析、多维度评估（专业技能、安全意识、工作经验、沟通表达）、综合建议。\n"
                    "语言风格要专业、客观、有建设性。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"面试数据：\n"
                    f"- 候选人：{candidate_name}\n"
                    f"- 应聘岗位：{job_name}\n"
                    f"- 面试总分：{total_score}/100\n\n"
                    f"各题回答详情：\n{answers_str}\n"
                    "请生成完整的面试评估报告（Markdown格式）。"
                ),
            },
        ]
        try:
            raw = await self._chat(messages, temperature=0.3, max_tokens=2048)
            return re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        except Exception as e:
            logger.warning("llm_report_fallback", error=str(e))
            return (
                f"# 面试评估报告\n\n"
                f"- **候选人**: {candidate_name}\n"
                f"- **应聘岗位**: {job_name}\n"
                f"- **面试总分**: {total_score}/100\n\n"
                f"*注：AI报告生成服务异常，此为简要报告。*\n"
            )


_real_llm_instance: RealLLMService | None = None


def get_llm_service() -> LLMService:
    if settings.AI_SERVICE_MODE == "mock":
        return MockLLMService()
    global _real_llm_instance
    if _real_llm_instance is None:
        _real_llm_instance = RealLLMService()
    return _real_llm_instance
