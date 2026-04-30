p = 'app/services/candidate_filter_service.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# Insert limit_percent extraction after limit extraction, before conditions
old_limit_extract = '''        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = None

    conditions = filter_rules.get("conditions", [])'''

new_limit_extract = '''        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                limit = None

    # 从规则中提取 limit_percent（百分比，如 10 表示前10%）
    limit_percent = filter_rules.get("limit_percent")
    if limit_percent is not None:
        try:
            limit_percent = int(limit_percent)
            if not (1 <= limit_percent <= 100):
                limit_percent = None
        except (TypeError, ValueError):
            limit_percent = None

    conditions = filter_rules.get("conditions", [])'''

c = c.replace(old_limit_extract, new_limit_extract)

# Insert limit_percent → limit conversion after total count, before pagination
old_total_block = '''    total = total_result.scalar() or 0

    # 分页 + 排序（limit 优先级高于 page/page_size）'''

new_total_block = '''    total = total_result.scalar() or 0

    # 百分比 → 绝对数量转换（优先于固定 limit）
    if limit_percent is not None and limit is None:
        import math
        limit = math.ceil(total * limit_percent / 100)

    # 分页 + 排序（limit 优先级高于 page/page_size）'''

c = c.replace(old_total_block, new_total_block)

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)
print('OK')
