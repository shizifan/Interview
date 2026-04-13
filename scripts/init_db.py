"""数据库初始化脚本"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, async_session_factory
from app.db.seed import seed_data


async def main():
    print("正在初始化数据库...")
    await init_db()
    print("数据库表创建完成")

    async with async_session_factory() as session:
        await seed_data(session)
    print("种子数据填充完成")
    print("数据库初始化成功！")


if __name__ == "__main__":
    asyncio.run(main())
