# FR-HR-004 智能筛选候选人 — 实现逻辑

## 功能概述

HR 可通过自然语言描述筛选意图，系统借助大语言模型（LLM）解析描述，自动生成候选人筛选规则。HR 确认规则后，系统对候选人库执行筛选，将结果呈现给 HR。

---

## 整体数据流

```
┌─────────────────┐    POST /parse     ┌─────────────────┐    LLM API        ┌──────────────────┐
│   前端 React      │ ─────────────────→ │   FastAPI 后端    │ ────────────────→ │   Qwen3-235B      │
│   Candidates.tsx  │ ←───────────────── │   hr.py          │ ←──────────────── │   (解析规则)       │
│                  │    JSON 规则        │                  │   JSON 规则       │                  │
└────────┬─────────┘                    └────────┬─────────┘                   └──────────────────┘
         │                                       │
         │  POST /execute (规则 JSON)              │
         │ ──────────────────────────────────────→│
         │                                       │  hr_service.filter_candidates()
         │                                       │  → candidate_filter_service.execute_filter()
         │                                       │        ↓
         │                                       │  SQLAlchemy 查询 Candidate 表
         │  候选人列表 + total                     │
         │ ←──────────────────────────────────────│
         ▼
  显示筛选结果表格（支持查看详情、邀约面试）
```

---

## 核心文件清单

| 文件 | 职责 |
|------|------|
| `web/src/pages/hr/Candidates.tsx` | 前端 UI：输入框、解析/执行按钮、规则展示、结果表格 |
| `web/src/api/hr.ts` | 前端 API 封装：`parseFilterRule()`、`executeIntelligentFilter()` |
| `app/api/hr.py` | 后端路由：`POST /parse`（LLM 解析）、`POST /execute`（执行筛选） |
| `app/services/llm_service.py` | LLM 服务：`RealLLMService`（真实 API）+ `MockLLMService`（关键词匹配） |
| `app/services/hr_service.py` | 业务服务层：`filter_candidates()` 桥接 |
| `app/services/candidate_filter_service.py` | 核心查询引擎：`build_condition()`、`execute_filter()`、`_build_qualification_condition()` |
| `app/models/candidate.py` | Candidate 数据模型定义 |

---

## 详细步骤

### 步骤 1：前端输入与提交

**入口**：候选人管理页面的「智能筛选」按钮

```tsx
// web/src/pages/hr/Candidates.tsx

// 1. HR 输入自然语言
<Input.TextArea
  placeholder="例如：找出驾龄3年以上、持有A2驾照且资格证在有效期内的候选人"
  value={filterInput}
/>

// 2. 点击「解析条件」→ 调用 LLM
const handleParseFilter = async () => {
  const result = await hrApi.parseFilterRule(filterInput);
  if (result.error) {
    setFilterError(result.error);
  } else {
    setFilterRules(result as FilterRule);
  }
};
```

```typescript
// web/src/api/hr.ts

export async function parseFilterRule(naturalLanguage: string) {
  const res = await request.post<ApiResponse<ParseFilterResponse>>(
    '/hr/candidates/intelligent-filter/parse',
    null,
    { params: { natural_language: naturalLanguage } }
  );
  return res.data.data;
}
```

**API 调用**：`POST /api/v1/hr/candidates/intelligent-filter/parse?natural_language=...`

---

### 步骤 2：后端 LLM 解析规则

```python
# app/api/hr.py

@router.post("/candidates/intelligent-filter/parse")
async def parse_filter_rule(
    natural_language: str = Query(..., description="自然语言筛选描述"),
    _user: HRUser = Depends(get_current_hr_user),
):
    llm = get_llm_service()                       # 根据 AI_SERVICE_MODE 选择
    rules = await llm.parse_candidate_filter(natural_language)
    return success(rules)
```

#### 2.1 真实 LLM 模式（RealLLMService）

```python
# app/services/llm_service.py

async def parse_candidate_filter(self, natural_language: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个蓝领岗位候选人筛选规则解析助手..."
                "候选人表字段包括：\n"
                "- id, name, phone, id_card, gender(1=男,2=女), age\n"
                "- education, work_experience(驾龄), address, status, total_score\n"
                "- qualification_detail: JSON格式(license_type准驾车型、license_date初次领证日期、qualification_date资格证有效期)\n\n"
                "支持的比较操作符：eq, ne, gt, gte, lt, lte, contains, in_list\n"
            ),
        },
        {"role": "user", "content": f"自然语言筛选条件：{natural_language}\n请输出JSON格式的筛选规则："},
    ]
    raw = await self._chat(messages)
    result = self._extract_json(raw)  # 处理 <think> 标签和 markdown 代码块
    return {
        "conditions": result.get("conditions", []),
        "logic": result.get("logic", "AND"),
        "description": result.get("description", ""),
    }
```

#### 2.2 Mock 模式（MockLLMService）

基于关键词匹配，支持以下检测：

| 关键词 | 检测逻辑 | 生成的规则字段 |
|--------|----------|---------------|
| `驾龄X年`、`驾驶经验` | 正则 `(\d+)\s*年` | `work_experience >= X` |
| `a1/a2/b1/b2/c1...` | 子串匹配 | `qualification_detail.license_type contains X` |
| `资格证` + `有效期` | 关键词组合 | `qualification_detail.qualification_valid` |
| `男`/`女` | 关键词匹配 | `gender = 1/2` |
| `本科`、`大专`、`高中`... | 关键词匹配 | `education = X` |
| `X岁` | 正则 `(\d+)\s*岁` | `age >=/<= X` |

---

### 步骤 3：LLM 返回的 JSON 规则结构

```json
{
  "conditions": [
    {
      "field": "gender",
      "operator": "eq",
      "value": 1,
      "description": "性别为男性"
    },
    {
      "field": "work_experience",
      "operator": "gt",
      "value": 3,
      "description": "驾龄大于3年"
    },
    {
      "field": "qualification_detail.license_type",
      "operator": "contains",
      "value": "A2",
      "description": "准驾车型包含A2"
    }
  ],
  "logic": "AND",
  "description": "筛选驾龄3年以上、持有A2驾照的男性候选人"
}
```

---

### 步骤 4：前端展示规则 → HR 确认

```tsx
// Candidates.tsx — 筛选规则已生成，请确认

<Alert
  type="info"
  message="筛选规则已生成，请确认"
  description={
    <div>
      <p><strong>逻辑：</strong>{filterRules.logic === 'AND' ? '所有条件都满足' : '满足任一条件'}</p>
      <p><strong>筛选说明：</strong>{filterRules.description}</p>
      <div>
        <strong>条件列表：</strong>
        <ul>
          {filterRules.conditions.map((cond, idx) => (
            <li key={idx}>{cond.description}</li>
          ))}
        </ul>
      </div>
    </div>
  }
/>

// 操作按钮
<Button onClick={() => setFilterRules(null)}>修改条件</Button>
<Button type="primary" onClick={handleExecuteFilter}>执行筛选</Button>
```

---

### 步骤 5：执行筛选

```python
# app/api/hr.py

@router.post("/candidates/intelligent-filter/execute")
async def execute_intelligent_filter(
    filter_rules: dict,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: HRUser = Depends(get_current_hr_user),
    db: AsyncSession = Depends(get_db),
):
    candidates, total = await hr_service.filter_candidates(
        db, filter_rules, page=page, page_size=page_size
    )
    return success({
        "items": [CandidateProfile.model_validate(c) for c in candidates],
        "total": total,
        "page": page,
        "page_size": page_size,
    })
```

---

### 步骤 6：核心查询构建引擎

```python
# app/services/candidate_filter_service.py

ALLOWED_FIELDS = {
    "id", "name", "phone", "id_card", "gender", "age",
    "education", "work_experience", "address", "status", "total_score"
}

ALLOWED_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "contains", "in_list"}
```

#### 6.1 条件构建：`build_condition()`

```python
def build_condition(field: str, operator: str, value: Any):
    """构建单个筛选条件，返回 SQLAlchemy ColumnElement 或 None"""

    # 分支1：qualification_detail JSON 子字段
    if field.startswith("qualification_detail."):
        sub_field = field.split(".", 1)[1]
        return _build_qualification_condition(sub_field, operator, value)

    # 分支2：普通表字段
    if field not in ALLOWED_FIELDS:
        raise ValueError(f"不允许的字段: {field}")
    if operator not in ALLOWED_OPERATORS:
        raise ValueError(f"不支持的操作符: {operator}")

    column = getattr(Candidate, field)

    # 构建 SQLAlchemy 表达式
    if operator == "eq":       return column == value
    elif operator == "ne":     return column != value
    elif operator == "gt":     return column > value
    elif operator == "gte":    return column >= value
    elif operator == "lt":     return column < value
    elif operator == "lte":    return column <= value
    elif operator == "contains": return column.contains(str(value))
    elif operator == "in_list":  return column.in_(value)
    return None
```

#### 6.2 JSON 子字段条件：`_build_qualification_condition()`

```python
def _build_qualification_condition(field: str, operator: str, value: Any):
    """构建 qualification_detail JSON 字段内的筛选条件"""

    # 准驾车型筛选：直接 contains 匹配 JSON 文本
    if field == "license_type":
        if operator == "contains":
            return Candidate.qualification_detail.contains(val_str)
        elif operator == "eq":
            return Candidate.qualification_detail.contains(f'"license_type":"{val_str}"')

    # 驾龄筛选：通过 json_extract 提取 license_date 计算年份
    elif field == "license_years":
        target_date = date.today() - timedelta(days=years * 365 + years // 4)
        return text(
            f"json_extract(candidate.qualification_detail, '$.license_date') <= '{target_str}'"
        )

    # 资格证有效期：json_extract 比较日期
    elif field == "qualification_valid":
        return text(
            f"json_extract(candidate.qualification_detail, '$.qualification_date') >= '{today_str}'"
        )
```

#### 6.3 查询执行与分页：`execute_filter()`

```python
async def execute_filter(db, filter_rules, page=1, page_size=20):
    """执行智能筛选，返回 (候选人列表, 总数)"""

    conditions = filter_rules.get("conditions", [])
    logic = filter_rules.get("logic", "AND").upper()

    # 1. 逐条件构建 SQLAlchemy 表达式
    query_conditions = []
    for cond in conditions:
        condition = build_condition(cond["field"], cond["operator"], cond["value"])
        if condition is not None:
            query_conditions.append(condition)

    # 2. 组合条件
    query = select(Candidate)
    if query_conditions:
        if logic == "OR":
            query = query.where(or_(*query_conditions))
        else:
            query = query.where(and_(*query_conditions))

    # 3. 计数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 4. 分页 + 排序
    query = query.order_by(Candidate.total_score.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return list(result.scalars().all()), total
```

---

### 步骤 7：前端展示结果

```tsx
{/* 筛选结果展示 */}
{filterResult && (
  <div style={{ marginTop: 16 }}>
    <Alert type="success" message={`筛选完成，共找到 ${filterResult.length} 位候选人`} />
    <Table
      size="small"
      rowKey="id"
      pagination={{ pageSize: 5 }}
      columns={columns}        // 复用主列表的列定义（含操作列）
      dataSource={filterResult}
    />
  </div>
)}
```

结果表格支持：
- **查看**：跳转到候选人详情页
- **邀约面试**：弹出岗位选择 Modal 发起面试邀请

---

## 安全措施

| 措施 | 实现 |
|------|------|
| 字段白名单 | `ALLOWED_FIELDS` 限制只能查询预定义字段，防止 SQL 注入 |
| 操作符白名单 | `ALLOWED_OPERATORS` 限制只能使用预定操作符 |
| 异常安全 | 无效字段/操作符抛出 `ValueError`，`execute_filter` 中捕获并跳过 |
| HR 确认步骤 | LLM 规则先展示给 HR 确认，确认后才执行，防止 LLM 幻觉风险 |
| 认证鉴权 | 两个端点都需要 `get_current_hr_user` 依赖注入 |

---

## LLM Prompt 设计

**System Prompt 核心内容**：

1. 角色定位：蓝领岗位候选人筛选规则解析助手
2. 上下文注入：完整的 Candidate 表字段列表及含义
3. 规则定义：允许的比较操作符及含义
4. 输出格式：严格的 JSON 模板
5. `qualification_detail` 特别说明：JSON 子字段（license_type、license_date、qualification_date）

```
"候选人表字段包括：
- id, name, phone, id_card, gender(1=男,2=女), age
- education(学历), work_experience(工作经验年数/驾龄)
- address, status, total_score
- qualification_detail(资质详情JSON，包含license_type准驾车型、license_date初次领证日期、qualification_date资格证有效期)

支持的比较操作符：eq(等于), ne(不等于), gt(大于), gte(大于等于), lt(小于), lte(小于等于), contains(包含), in_list(在列表中)

请严格按照以下JSON格式输出：
{"conditions": [{"field": "字段名", "operator": "操作符", "value": "值", "description": "条件中文说明"}], "logic": "AND或OR", "description": "筛选逻辑的中文解释"}"
```

---

## 查询 SQL 示例

输入：`"驾龄3年以上、持有A2驾照且资格证在有效期内的男性候选人"`

LLM 解析后生成的 SQL（逻辑等价）：

```sql
SELECT * FROM candidate
WHERE gender = 1                                    -- 男性
  AND work_experience > 3                           -- 驾龄>3年
  AND qualification_detail LIKE '%A2%'              -- 准驾车型包含A2
  AND json_extract(qualification_detail, '$.qualification_date') >= '2026-04-30'  -- 资格证有效
ORDER BY total_score DESC
LIMIT 20 OFFSET 0;
```
