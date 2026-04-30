import json
from typing import Any

from sqlalchemy import and_, or_, Column
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate

ALLOWED_FIELDS = {
    "id", "name", "phone", "id_card", "gender", "age",
    "education", "work_experience", "address", "status", "total_score"
}

ALLOWED_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "contains", "in_list"}


def parse_qualification_detail(detail: str | None) -> dict:
    if not detail:
        return {}
    try:
        return json.loads(detail)
    except (json.JSONDecodeError, TypeError):
        return {}


def build_condition(field: str, operator: str, value: Any):
    """构建单个筛选条件，返回SQLAlchemy ColumnElement或None"""
    if field.startswith("qualification_detail."):
        sub_field = field.split(".", 1)[1]
        return _build_qualification_condition(sub_field, operator, value)

    if field not in ALLOWED_FIELDS:
        raise ValueError(f"不允许的字段: {field}")
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"不支持的操作符: {operator}")

    column = getattr(Candidate, field)

    if operator == "eq":
        return column == value
    elif operator == "ne":
        return column != value
    elif operator == "gt":
        return column > value
    elif operator == "gte":
        return column >= value
    elif operator == "lt":
        return column < value
    elif operator == "lte":
        return column <= value
    elif operator == "contains":
        return column.contains(str(value))
    elif operator == "in_list":
        return column.in_(value)
    return None


async def execute_filter(
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

    # 从规则中提取 limit_percent（百分比，如 10 表示前10%）
    limit_percent = filter_rules.get("limit_percent")
    if limit_percent is not None:
        try:
            limit_percent = int(limit_percent)
            if not (1 <= limit_percent <= 100):
                limit_percent = None
        except (TypeError, ValueError):
            limit_percent = None

    conditions = filter_rules.get("conditions", [])
    logic = filter_rules.get("logic", "AND").upper()

    query_conditions = []
    for cond in conditions:
        field = cond.get("field")
        operator = cond.get("operator")
        value = cond.get("value")

        try:
            condition = build_condition(field, operator, value)
            if condition is not None:
                query_conditions.append(condition)
        except (ValueError, KeyError) as e:
            logger = __import__("structlog").get_logger(__name__)
            logger.warning("filter_condition_skip", field=field, error=str(e))
            continue

    query = select(Candidate)
    if query_conditions:
        if logic == "OR":
            query = query.where(or_(*query_conditions))
        else:
            query = query.where(and_(*query_conditions))

    # 子查询用于计数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 百分比 → 绝对数量转换（优先于固定 limit）
    if limit_percent is not None and limit is None:
        import math
        limit = math.ceil(total * limit_percent / 100)

    # 分页 + 排序（limit 优先级高于 page/page_size）
    query = query.order_by(Candidate.total_score.desc())
    if limit is not None and limit > 0:
        query = query.limit(limit)
    else:
        query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


def _build_qualification_condition(field: str, operator: str, value: Any):
    """构建 qualification_detail JSON 字段内的筛选条件"""
    from datetime import date
    from sqlalchemy import cast, String, text

    if field == "license_type":
        val_str = ""
        if isinstance(value, dict):
            val_str = value.get("license_type", "")
        elif isinstance(value, str):
            val_str = value
        if not val_str:
            return None
        if operator == "contains":
            return Candidate.qualification_detail.contains(val_str)
        elif operator == "eq":
            return Candidate.qualification_detail.contains(f'"license_type":"{val_str}"')

    elif field == "license_years":
        # 驾龄：从第一次领证日期计算距今的年数
        years = 0
        if isinstance(value, dict):
            years = value.get("license_years", value.get("years", 0))
        elif isinstance(value, (int, float)):
            years = int(value)
        if years <= 0:
            return None
        # 计算目标日期（今天 - years年），初次领证日期应早于此日期
        from datetime import timedelta
        target_date = date.today() - timedelta(days=years * 365 + years // 4)
        target_str = target_date.isoformat()
        if operator in ("gt", "gte"):
            # qualification_detail中的license_date < target_date 意味着驾龄 >= years
            return text(
                f"json_extract(candidate.qualification_detail, '$.license_date') <= '{target_str}'"
            )
        else:
            return text(
                f"json_extract(candidate.qualification_detail, '$.license_date') <= '{target_str}'"
            )

    elif field == "qualification_valid":
        # 资格证有效期 > 当前日期
        today_str = date.today().isoformat()
        return text(
            f"json_extract(candidate.qualification_detail, '$.qualification_date') >= '{today_str}'"
        )

    return None
