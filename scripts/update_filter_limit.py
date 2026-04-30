p = 'app/services/candidate_filter_service.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Replace execute_filter function header
old_header = '''async def execute_filter(
    db: AsyncSession,
    filter_rules: dict,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Candidate], int]:
    """执行智能筛选，返回(候选人列表, 总数)"""
    from sqlalchemy import select, func

    conditions = filter_rules.get("conditions", [])
'''

new_header = '''async def execute_filter(
    db: AsyncSession,
    filter_rules: dict,
    page: int = 1,
    page_size: int = 20,
    limit: int | None = None,
) -> tuple[list[Candidate], int]:
    """执行智能筛选，返回(候选人列表, 总数)

    当 limit 有值时，忽略 page/page_size，直接返回前 limit 条结果。
    """
    from sqlalchemy import select, func

    # 从规则中提取 limit（LLM解析的或手动传入的）
    if limit is None:
        limit = filter_rules.get("limit")
        if isinstance(limit, dict):
            limit = limit.get("limit", limit.get("value", None))
        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = None

    conditions = filter_rules.get("conditions", [])
'''

c = c.replace(old_header, new_header)

# Replace pagination section
old_pag = '''    # 分页 + 排序
    query = query.order_by(Candidate.total_score.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)'''

new_pag = '''    # 分页 + 排序（limit 优先级高于 page/page_size）
    query = query.order_by(Candidate.total_score.desc())
    if limit is not None and limit > 0:
        query = query.limit(limit)
    else:
        query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)'''

c = c.replace(old_pag, new_pag)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
