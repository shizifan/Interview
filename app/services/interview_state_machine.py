"""
面试状态机 - 6个节点的纯Python实现

节点流转:
intro → ask_question → wait_asr → process_answer → judge_followup → finish
"""

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from app.services.llm_service import get_llm_service
from app.services.tts_service import get_tts_service


@dataclass
class QuestionData:
    id: int
    content: str
    score_points: list[str]
    follow_up_scripts: list[str]


@dataclass
class AnswerData:
    question_id: int
    question_order: int
    answer_text: str
    score: float
    score_detail: dict
    follow_up_count: int


@dataclass
class InterviewGraphState:
    interview_id: int
    candidate_id: int
    job_id: int
    current_node: str = "intro"
    questions: list[dict] = field(default_factory=list)
    current_question_index: int = 0
    current_answer_text: str = ""
    follow_up_count: int = 0
    answers: list[dict] = field(default_factory=list)
    total_score: float = 0.0
    status: str = "in_progress"  # in_progress | completed | interrupted
    tts_text: str | None = None
    message: str | None = None
    is_finished: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "InterviewGraphState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "InterviewGraphState":
        return cls.from_dict(json.loads(json_str))


class InterviewStateMachine:
    """面试状态机"""

    INTRO_TEXT = (
        "您好，师傅！欢迎参加AI面试。本次面试共有{total}道题目，"
        "每道题我会语音播报，请您听完后直接回答。"
        "如果没听清可以说「再说一遍」。准备好了我们就开始吧！"
    )

    async def initialize(
        self,
        interview_id: int,
        candidate_id: int,
        job_id: int,
        questions: list[dict],
    ) -> InterviewGraphState:
        """初始化面试状态"""
        state = InterviewGraphState(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_id=job_id,
            questions=questions,
        )
        return await self._run_node(state, "intro")

    async def advance(self, state: InterviewGraphState, event: str, data: dict | None = None) -> InterviewGraphState:
        """推进状态机

        event: "answer_received" | "timeout" | "abort"
        data: {"answer_text": "..."} for answer_received
        """
        if event == "abort":
            state.status = "interrupted"
            state.current_node = "finish"
            state.message = "面试已中断，进度已保存"
            return state

        if event == "timeout":
            state.current_answer_text = ""
            return await self._run_node(state, "process_answer_timeout")

        if event == "answer_received":
            state.current_answer_text = (data or {}).get("answer_text", "")
            return await self._run_node(state, "process_answer")

        return state

    async def _run_node(self, state: InterviewGraphState, node: str) -> InterviewGraphState:
        """执行指定节点"""
        if node == "intro":
            return await self._node_intro(state)
        elif node == "ask_question":
            return await self._node_ask_question(state)
        elif node == "process_answer":
            return await self._node_process_answer(state)
        elif node == "process_answer_timeout":
            return await self._node_process_timeout(state)
        elif node == "judge_followup":
            return await self._node_judge_followup(state)
        elif node == "finish":
            return await self._node_finish(state)
        return state

    async def _node_intro(self, state: InterviewGraphState) -> InterviewGraphState:
        """Node A: 开场介绍"""
        total = len(state.questions)
        state.tts_text = self.INTRO_TEXT.format(total=total)
        state.current_node = "ask_question"
        state.message = "面试开场"
        # 自动进入出题
        return await self._node_ask_question(state)

    async def _node_ask_question(self, state: InterviewGraphState) -> InterviewGraphState:
        """Node B: 出题"""
        idx = state.current_question_index
        if idx >= len(state.questions):
            return await self._node_finish(state)

        q = state.questions[idx]
        state.tts_text = q["content"]
        state.current_node = "wait_asr"
        state.follow_up_count = 0
        state.message = f"第{idx + 1}题（共{len(state.questions)}题）"
        return state

    async def _node_process_answer(self, state: InterviewGraphState) -> InterviewGraphState:
        """Node D: 处理回答"""
        llm = get_llm_service()
        answer_text = state.current_answer_text

        # 意图检测
        intent = await llm.detect_intent(answer_text)

        if intent == "empty":
            idx = state.current_question_index
            q = state.questions[idx]
            state.tts_text = f"师傅，刚刚没听清您的回答。问题是：{q['content']}，请您再说一遍好吗？"
            state.current_node = "wait_asr"
            state.message = f"未检测到有效回答，请重试。问题：{q['content']}"
            return state

        if intent == "replay_request":
            idx = state.current_question_index
            q = state.questions[idx]
            state.tts_text = q["content"]
            state.current_node = "wait_asr"
            state.message = "重新播放题目"
            return state

        # 正常回答 → 评分判断
        return await self._node_judge_followup(state)

    async def _node_process_timeout(self, state: InterviewGraphState) -> InterviewGraphState:
        """超时处理"""
        idx = state.current_question_index
        q = state.questions[idx]

        # 记录超时回答（0分）
        answer = {
            "question_id": q["id"],
            "question_order": idx + 1,
            "answer_text": "",
            "score": 0.0,
            "score_detail": {"reason": "超时未回答"},
            "follow_up_count": state.follow_up_count,
        }
        state.answers.append(answer)

        state.tts_text = "师傅，没听到您的回答，我们进入下一题"
        state.current_question_index += 1
        state.message = "回答超时，进入下一题"

        # 检查是否还有题目
        if state.current_question_index >= len(state.questions):
            return await self._node_finish(state)

        state.current_node = "ask_question"
        return await self._node_ask_question(state)

    async def _node_judge_followup(self, state: InterviewGraphState) -> InterviewGraphState:
        """Node E: 追问决策"""
        llm = get_llm_service()
        idx = state.current_question_index
        q = state.questions[idx]

        score_points = q.get("score_points", [])
        if isinstance(score_points, str):
            score_points = json.loads(score_points)

        follow_up_scripts = q.get("follow_up_scripts", [])
        if isinstance(follow_up_scripts, str):
            follow_up_scripts = json.loads(follow_up_scripts) if follow_up_scripts else []

        result = await llm.judge_score_points(q["content"], score_points, state.current_answer_text)
        uncovered = result.get("uncovered_points", [])
        score = result.get("score", 0)

        if not uncovered or state.follow_up_count >= 2:
            # 覆盖全部得分点 或 已追问2次 → 记录得分，下一题
            answer = {
                "question_id": q["id"],
                "question_order": idx + 1,
                "answer_text": state.current_answer_text,
                "score": score,
                "score_detail": result,
                "follow_up_count": state.follow_up_count,
            }
            state.answers.append(answer)
            state.current_question_index += 1

            if state.current_question_index >= len(state.questions):
                return await self._node_finish(state)

            state.current_node = "ask_question"
            state.message = f"得分: {score}/10"
            return await self._node_ask_question(state)

        # 需要追问
        state.follow_up_count += 1
        if follow_up_scripts and state.follow_up_count <= len(follow_up_scripts):
            state.tts_text = follow_up_scripts[state.follow_up_count - 1]
        else:
            state.tts_text = f"关于{uncovered[0]}，您能再详细说说吗？"

        state.current_node = "wait_asr"
        state.message = f"追问第{state.follow_up_count}次"
        return state

    async def _node_finish(self, state: InterviewGraphState) -> InterviewGraphState:
        """Node F: 结束"""
        # 计算总分
        if state.answers:
            total_questions = len(state.questions)
            raw_total = sum(a["score"] for a in state.answers)
            # 按百分制换算: 每题10分满，总题数*10为满分，换算到100分
            max_possible = total_questions * 10
            state.total_score = round(raw_total / max_possible * 100, 1) if max_possible > 0 else 0

        state.status = "completed"
        state.current_node = "finish"
        state.is_finished = True
        state.tts_text = "面试结束，感谢您的参与！我们将在3个工作日内通知您面试结果。"
        state.message = "面试已完成"
        return state
