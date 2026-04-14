"""
模拟测试：面试评分全链路
验证面试完成后 interview_score 和 total_score 被正确写入评分池
"""
import asyncio
import json
import os
import sys

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("AI_SERVICE_MODE", "mock")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.question import Question
from app.models.score_pool import ScorePool
from app.services.interview_service import create_and_start_interview, process_answer
from app.services.score_pool_service import update_interview_score


async def run_test():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        # 1. 创建岗位
        job = Job(
            name="测试司机岗位",
            description="测试",
            requirements="测试",
            quota=5,
            status=1,
            required_license_type=json.dumps(["A2"]),
        )
        db.add(job)
        await db.flush()
        print(f"[OK] 创建岗位: id={job.id}, name={job.name}")

        # 2. 创建题目 (2道简单题目)
        q1 = Question(
            job_id=job.id,
            content="您在行驶途中发现刹车异常怎么处理？",
            type=1,
            difficulty=1,
            score_points=json.dumps(["靠边停车", "打双闪", "放三角牌"]),
            follow_up_scripts=json.dumps([]),
            is_active=True,
        )
        q2 = Question(
            job_id=job.id,
            content="遇到大雾天气如何应对？",
            type=1,
            difficulty=1,
            score_points=json.dumps(["减速慢行", "开雾灯", "保持车距"]),
            follow_up_scripts=json.dumps([]),
            is_active=True,
        )
        db.add_all([q1, q2])
        await db.flush()
        print(f"[OK] 创建题目: q1.id={q1.id}, q2.id={q2.id}")

        # 3. 创建候选人
        candidate = Candidate(
            name="张三",
            phone="13800138001",
            work_experience=3,
            status=1,
        )
        db.add(candidate)
        await db.flush()
        print(f"[OK] 创建候选人: id={candidate.id}, name={candidate.name}")

        # 4. 预先在评分池中创建材料分记录 (模拟材料审核后的结果)
        pool_entry = ScorePool(
            candidate_id=candidate.id,
            job_id=job.id,
            doc_score=75.0,
            interview_score=0.0,
            total_score=round(75.0 * 0.4, 1),  # 30.0
        )
        db.add(pool_entry)
        await db.flush()
        print(f"[OK] 评分池初始状态: doc_score={pool_entry.doc_score}, "
              f"interview_score={pool_entry.interview_score}, "
              f"total_score={pool_entry.total_score}")

        # 5. 开始面试
        state = await create_and_start_interview(db, candidate.id, job.id)
        interview_id = state.interview_id
        print(f"[OK] 面试开始: interview_id={interview_id}, "
              f"node={state.current_node}, "
              f"questions={len(state.questions)}")

        # 6. 回答第1题 - 命中所有得分点
        state = await process_answer(
            db, interview_id,
            "我会先靠边停车，然后打双闪警示灯，再在车后放三角牌"
        )
        print(f"[OK] 回答第1题: node={state.current_node}, "
              f"answers={len(state.answers)}, "
              f"msg={state.message}")

        # 7. 回答第2题 - 命中部分得分点
        state = await process_answer(
            db, interview_id,
            "我会减速慢行，然后开雾灯提醒前后车辆，并保持车距"
        )
        print(f"[OK] 回答第2题: node={state.current_node}, "
              f"answers={len(state.answers)}, "
              f"msg={state.message}")

        # 8. 检查面试是否完成
        assert state.is_finished, f"面试应该已完成，但 is_finished={state.is_finished}"
        assert state.total_score > 0, f"总分应该 > 0，但 total_score={state.total_score}"
        print(f"[OK] 面试完成: total_score={state.total_score}, status={state.status}")

        # 打印每题得分详情
        for i, ans in enumerate(state.answers, 1):
            print(f"     第{i}题得分: {ans['score']}/10, "
                  f"覆盖: {ans['score_detail'].get('covered_points', [])}")

        await db.commit()

    # 9. 重新查询评分池，验证面试分已更新
    async with session_factory() as db:
        result = await db.execute(
            select(ScorePool).where(ScorePool.candidate_id == candidate.id, ScorePool.job_id == job.id)
        )
        entry = result.scalar_one_or_none()

        assert entry is not None, "评分池记录应该存在"
        print(f"\n=== 评分池最终结果 ===")
        print(f"  doc_score       = {entry.doc_score}")
        print(f"  interview_score = {entry.interview_score}")
        print(f"  total_score     = {entry.total_score}")
        print(f"  rank            = {entry.rank}")

        assert entry.interview_score > 0, \
            f"[FAIL] interview_score 应该 > 0，实际为 {entry.interview_score}"
        assert entry.total_score > entry.doc_score * 0.4, \
            f"[FAIL] total_score ({entry.total_score}) 应该 > doc_score*0.4 ({entry.doc_score * 0.4})"

        expected_total = round(entry.doc_score * 0.4 + entry.interview_score * 0.6, 1)
        assert abs(entry.total_score - expected_total) < 0.2, \
            f"[FAIL] total_score={entry.total_score}, expected={expected_total}"

        print(f"\n[PASS] 所有断言通过！面试评分链路正常工作。")
        print(f"  interview_score = {entry.interview_score} (> 0)")
        print(f"  total_score = {entry.total_score} = doc*0.4 + interview*0.6 = {expected_total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_test())
