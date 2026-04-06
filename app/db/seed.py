import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.question import Question
from app.models.system_settings import SystemSettings
from app.models.hr_user import HRUser
from app.core.security import hash_password


async def seed_data(db: AsyncSession) -> None:
    """填充示例数据（仅在表为空时执行）"""
    # HR 管理员
    result = await db.execute(select(HRUser).limit(1))
    if result.scalar_one_or_none() is None:
        admin = HRUser(
            username="admin",
            hashed_password=hash_password("admin123"),
            display_name="管理员",
            role="admin",
        )
        db.add(admin)

    # 系统设置
    result = await db.execute(select(SystemSettings).limit(1))
    if result.scalar_one_or_none() is None:
        default_settings = [
            SystemSettings(key="max_daily_interviews", value="3", description="每日每人每岗最大面试次数"),
            SystemSettings(key="answer_timeout_seconds", value="30", description="回答超时时间（秒）"),
            SystemSettings(key="follow_up_limit", value="2", description="单题最大追问次数"),
            SystemSettings(key="interview_recovery_hours", value="24", description="面试中断恢复窗口（小时）"),
            SystemSettings(key="default_start_coefficient", value="1.2", description="默认面试启动系数"),
        ]
        db.add_all(default_settings)

    # 示例岗位
    result = await db.execute(select(Job).limit(1))
    if result.scalar_one_or_none() is None:
        job = Job(
            name="卡车司机",
            description="负责长途货物运输，要求持有A2驾照",
            requirements="- A2及以上驾照\n- 3年以上驾驶经验\n- 无重大交通事故记录",
            quota=10,
            start_coefficient=1.2,
            min_interview_count=5,
            required_license_type=json.dumps(["A2", "A1"]),
            status=1,
        )
        db.add(job)
        await db.flush()

        # 示例题目
        questions = [
            Question(
                job_id=job.id,
                content="师傅您好，请问您在行驶途中发现车辆刹车出现异常，您会怎么处理？",
                type=3,
                difficulty=2,
                score_points=json.dumps(["靠边停车", "打双闪", "放三角牌", "检查刹车", "报告调度"]),
                follow_up_scripts=json.dumps([
                    "那如果当时在高速公路上呢？您还会怎么做？",
                    "停车之后，您会做哪些安全措施？",
                ]),
            ),
            Question(
                job_id=job.id,
                content="请问您在驾驶过程中遇到恶劣天气，比如大雾或暴雨，您通常怎么应对？",
                type=3,
                difficulty=2,
                score_points=json.dumps(["减速慢行", "开雾灯", "保持车距", "必要时停车等待"]),
                follow_up_scripts=json.dumps([
                    "如果能见度非常低，不到50米，您会怎么办？",
                    "在这种情况下，您会如何提醒后方车辆？",
                ]),
            ),
            Question(
                job_id=job.id,
                content="师傅，请您介绍一下每次出车前您通常会做哪些车辆检查？",
                type=1,
                difficulty=1,
                score_points=json.dumps(["检查轮胎", "检查刹车", "检查灯光", "检查油水", "检查货物固定"]),
                follow_up_scripts=json.dumps([
                    "那轮胎方面您一般检查哪些内容？",
                    "货物固定方面您有什么经验？",
                ]),
            ),
            Question(
                job_id=job.id,
                content="请问您有遇到过货物在运输途中出现损坏的情况吗？您是怎么处理的？",
                type=2,
                difficulty=2,
                score_points=json.dumps(["及时停车检查", "拍照记录", "联系调度", "做好记录"]),
                follow_up_scripts=json.dumps([
                    "那您在装货时会做哪些预防措施？",
                    "如果客户对损坏提出投诉，您会怎么沟通？",
                ]),
            ),
            Question(
                job_id=job.id,
                content="师傅，如果在长途驾驶中您感到疲劳了，您会怎么做？",
                type=1,
                difficulty=1,
                score_points=json.dumps(["停车休息", "不疲劳驾驶", "找安全地点", "活动身体"]),
                follow_up_scripts=json.dumps([
                    "您一般开多长时间会休息一次？",
                    "您有什么防疲劳驾驶的好方法吗？",
                ]),
            ),
        ]
        db.add_all(questions)

    await db.commit()
