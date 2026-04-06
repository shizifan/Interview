# AI 面试官系统

蓝领岗位（卡车司机、港区拖车司机等）AI 语音面试系统 MVP 版本。通过 AI 实现从资质材料初筛到语音面试的全流程自动化。

## 项目概况

- **目标用户**：HR 招聘人员 + 蓝领候选人
- **核心能力**：OCR 证件识别 -> 资质校验打分 -> AI 语音面试 -> 自动评分报告
- **当前阶段**：MVP（本地单机部署，验证核心流程）

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.13 + FastAPI + SQLAlchemy (async) + SQLite (WAL) |
| 前端 | React 19 + TypeScript + Vite + Tailwind CSS + Ant Design |
| 状态管理 | Zustand（前端） |
| 面试引擎 | 自研状态机（6 节点：intro -> ask_question -> wait_asr -> process_answer -> judge_followup -> finish） |
| 实时通信 | FastAPI WebSocket（音频流 + 状态推送） |
| AI 服务 | LLM: Qwen3-235B (中移香港LMMP)、OCR: Qwen2-VL-72B (LMMP)、ASR: FunASR (DashScope)、TTS: CosyVoice (DashScope) |
| 包管理 | uv（后端）、npm（前端） |

## 目录结构

```
.
├── app/                      # FastAPI 后端
│   ├── main.py               # 应用入口，CORS、路由注册、lifespan
│   ├── api/                  # 路由层
│   │   ├── router.py         # 路由汇总：/api/v1/candidate, /api/v1/hr, /api/v1/interview, /api/v1/files
│   │   ├── candidate.py      # 候选人接口（注册、材料上传、面试）
│   │   ├── hr.py             # HR 接口（岗位、题库、候选人、面试管理）
│   │   ├── interview.py      # 面试流程接口（状态查询、提交回答、超时、中断）
│   │   ├── files.py          # 文件访问接口
│   │   └── ws.py             # WebSocket 面试实时通信
│   ├── services/             # 业务逻辑层
│   │   ├── interview_state_machine.py  # 面试状态机（核心）
│   │   ├── interview_service.py        # 面试业务逻辑
│   │   ├── candidate_service.py        # 候选人业务逻辑
│   │   ├── hr_service.py               # HR 业务逻辑
│   │   ├── document_service.py         # 材料审核逻辑
│   │   ├── score_pool_service.py       # 评分池管理
│   │   ├── llm_service.py              # LLM 调用（意图理解、评分、报告生成）
│   │   ├── asr_service.py              # 语音识别服务
│   │   ├── tts_service.py              # 语音合成服务
│   │   └── ocr_service.py              # OCR 证件识别服务
│   ├── models/               # SQLAlchemy 数据模型
│   │   ├── candidate.py      # 候选人
│   │   ├── job.py            # 岗位
│   │   ├── interview.py      # 面试记录
│   │   ├── question.py       # 题目
│   │   ├── document.py       # 证件材料
│   │   ├── score_pool.py     # 评分池
│   │   ├── interview_answer.py  # 面试回答
│   │   └── system_settings.py   # 系统设置
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── core/                 # 配置、异常、依赖注入
│   │   └── config.py         # 环境变量配置（读 .env）
│   └── db/                   # 数据库初始化 + 种子数据
│       ├── database.py       # 异步引擎、session 工厂、SQLite PRAGMA
│       └── seed.py           # 种子数据（卡车司机岗位 + 5 道面试题）
├── web/                      # React 前端 (Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── candidate/    # 候选人端：Enter, Home, Profile, Documents, Interviews, InterviewRoom, InterviewResult
│   │   │   └── hr/           # HR 端：Dashboard, Jobs, JobDetail, Candidates, HRInterviews, ScorePool, Settings
│   │   ├── layouts/          # CandidateLayout, HRLayout
│   │   ├── api/              # Axios 请求封装
│   │   ├── stores/           # Zustand 状态管理
│   │   ├── types/            # TypeScript 类型定义
│   │   └── router.tsx        # 路由配置
│   └── vite.config.ts        # Vite 配置（含 API 代理）
├── spec/                     # 需求规格说明书
├── scripts/                  # 工具脚本
│   └── init_db.py            # 手动初始化数据库 + 种子数据
├── data/                     # SQLite 数据库文件（.gitignore）
├── uploads/                  # 上传文件存储
├── logs/                     # 应用日志
├── tests/                    # 测试用例
├── pyproject.toml            # Python 项目配置
├── uv.lock                   # uv 锁文件
└── .env.example              # 环境变量模板
```

## 快速启动

### 前置要求

- Python 3.13+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）

### 1. 克隆仓库

```bash
git clone https://github.com/shizifan/Interview.git
cd Interview
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写 AI 服务密钥：

| 变量 | 用途 | 获取方式 |
|------|------|---------|
| `LLM_API_KEY` | Qwen3-235B 推理（意图理解、评分、报告） | 中移香港 LMMP 平台 |
| `OCR_API_KEY` | Qwen2-VL-72B 证件识别 | 中移香港 LMMP 平台 |
| `DASHSCOPE_API_KEY` | FunASR 语音识别 + CosyVoice 语音合成 | 阿里云百炼 DashScope |

> 如果暂时没有密钥，可以保持 `AI_SERVICE_MODE=mock`（默认值），系统将使用 mock 数据运行，方便前后端联调。

### 3. 启动后端

```bash
# 安装依赖
uv sync

# 启动服务（首次启动会自动创建数据库和种子数据）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 4. 启动前端

```bash
cd web
npm install
npm run dev
```

前端启动后访问 http://localhost:5173 ：
- 候选人入口：`/`
- 候选人中心：`/candidate`
- HR 管理后台：`/hr`

> Vite 已配置代理，`/api` 和 `/ws` 请求会自动转发到后端 `localhost:8000`。

### 5. 手动初始化数据库（可选）

应用首次启动时会自动建表并填充种子数据。如需手动重新初始化：

```bash
uv run python scripts/init_db.py
```

## 核心流程

### 面试状态机

```
intro（开场白）
  -> ask_question（TTS 播报题目）
    -> wait_asr（VAD 检测 + ASR 转写）
      -> process_answer（意图分发）
        -> [空回答] 提示重说 -> wait_asr
        -> [请求重播] 重播题目 -> wait_asr
        -> [正常回答] -> judge_followup（LLM 评分 + 追问决策）
          -> [得分点全覆盖 or 已追问2次] 记录得分 -> ask_question（下一题）
          -> [需追问] 播放追问话术 -> wait_asr
      -> [超时30s] 记0分 -> ask_question（下一题）
  -> finish（全部题目完成，生成评估报告）
```

### WebSocket 通信

面试间通过 `ws://localhost:8000/ws/interview/{interview_id}` 进行实时通信：

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| 二进制帧（音频） | 前端 -> 后端 | MediaRecorder 录制的音频数据块（WebM/WAV） |
| `audio_end` | 前端 -> 后端 | 录音结束信号，触发 ASR 转写 |
| `text_input` | 前端 -> 后端 | 文字输入模式的候选人回答 |
| `tts_played` | 前端 -> 后端 | TTS 播放完成确认 |
| `timeout` | 前端 -> 后端 | 30s 超时通知 |
| `abort` | 前端 -> 后端 | 主动中断面试 |
| `asr_result` | 后端 -> 前端 | ASR 转写结果文本 |
| `state_update` | 后端 -> 前端 | 状态机节点变化 + TTS 文本 |
| 二进制帧（音频） | 后端 -> 前端 | TTS 合成的语音音频（WAV 格式） |
| `interview_end` | 后端 -> 前端 | 面试结束 + 总分 |

### API 路由

| 模块 | 前缀 | 说明 |
|------|------|------|
| 候选人 | `/api/v1/candidate` | 注册、登录、个人信息、材料上传、面试 |
| HR | `/api/v1/hr` | 岗位管理、题库、候选人管理、面试结果、系统设置 |
| 面试流程 | `/api/v1/interview` | 面试状态查询、提交回答、超时、中断 |
| 文件 | `/api/v1/files` | 鉴权文件访问 |

## AI 服务架构

系统采用 **策略模式 + 工厂函数** 管理 AI 服务，每个服务包含：
- 抽象基类（`LLMService` / `OCRService` / `ASRService` / `TTSService`）
- Mock 实现（用于联调，返回模拟数据）
- Real 实现（对接真实 AI API）
- 工厂函数（根据 `AI_SERVICE_MODE` 配置返回对应实例，单例缓存）

### LLM 服务 (Qwen3-235B)

通过 OpenAI 兼容 API 调用，使用 httpx 异步客户端：
- `judge_score_points()` - 候选人回答评分，逐项判断得分点覆盖情况
- `detect_intent()` - 意图识别（正常回答 / 空白 / 请求重播），内置关键词快速路径 + LLM 兜底
- `generate_report()` - 生成面试评估报告（Markdown 格式）
- 内置 `_extract_json()` 方法，处理 Qwen3 的 `<think>` 标签和 Markdown 代码块

### OCR 服务 (Qwen2-VL-72B)

通过 OpenAI Vision 兼容 API 调用，支持 4 种证件类型：
- 身份证：提取姓名、身份证号、地址、出生日期
- 驾驶证：提取准驾车型、有效期、初次领证日期
- 从业资格证：提取资格类别、有效期、发证机关
- 其他证件：通用信息提取

### ASR 服务 (FunASR via DashScope)

使用 DashScope SDK `Recognition` 类：
- 支持 WAV / WebM / MP3 格式自动检测（magic bytes）
- 同步 SDK 通过 `asyncio.to_thread()` 包装为异步调用
- 临时文件写入 + 自动清理

### TTS 服务 (CosyVoice via DashScope)

使用 DashScope SDK `SpeechSynthesizer` 类：
- 默认音色：longxiaochun
- 输出格式：WAV
- 后端合成后通过 WebSocket 二进制帧发送给前端

### 前端面试间

InterviewRoom 组件实现完整的语音面试交互：
- **设备检测**：面试前检查麦克风权限和网络连接状态
- **语音录制**：基于 MediaRecorder API，录音数据通过 WebSocket 二进制帧发送
- **TTS 播放**：接收后端 WebSocket 二进制音频帧，通过 HTML5 Audio API 播放
- **双模式输入**：支持语音录制和文字输入两种方式
- **实时状态**：连接状态指示、录音/播放动画、面试计时器

## 开发说明

### Mock 模式 vs Real 模式

`AI_SERVICE_MODE=mock`（`.env` 默认值）时，所有 AI 服务返回模拟数据：
- LLM：返回预设评分结果（满分）
- ASR：返回模拟转写文本
- TTS：返回静音 WAV 音频
- OCR：返回模拟识别结果

`AI_SERVICE_MODE=real` 时，连接真实 AI 服务：
- LLM / OCR 通过 httpx 调用 OpenAI 兼容 API（中移香港 LMMP 平台）
- ASR / TTS 通过 DashScope Python SDK 调用阿里云百炼服务
- 所有服务实例采用单例模式缓存，复用连接池
- 异常时自动降级（评分返回 0 分、ASR 返回空文本、TTS 返回静音音频）

### 数据库

- 使用 SQLite WAL 模式，数据库文件位于 `data/ai_interviewer.db`
- SQLAlchemy async 模式（aiosqlite 驱动）
- 启动时自动执行 `create_all` 建表 + 种子数据填充
- 已配置 PRAGMA 优化（WAL、foreign_keys、cache_size 等）

### 关键配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `AI_SERVICE_MODE` | `mock` | AI 服务模式：`mock`（模拟数据）或 `real`（真实 API） |
| `LLM_API_URL` | - | Qwen3-235B API 地址（OpenAI 兼容） |
| `LLM_API_KEY` | - | Qwen3-235B API 密钥 |
| `LLM_TIMEOUT` | 60 | LLM 请求超时（秒） |
| `LLM_MAX_TOKENS` | 2048 | LLM 最大输出 token 数 |
| `OCR_API_URL` | - | Qwen2-VL-72B Vision API 地址 |
| `OCR_API_KEY` | - | Qwen2-VL-72B API 密钥 |
| `DASHSCOPE_API_KEY` | - | 阿里云 DashScope API 密钥（ASR + TTS 共用） |
| `ASR_MODEL` | `paraformer-v2` | ASR 模型名称 |
| `TTS_MODEL` | `cosyvoice-v2` | TTS 模型名称 |
| `TTS_VOICE` | `longxiaochun` | TTS 音色 |
| `MAX_DAILY_INTERVIEWS` | 3 | 同一候选人同一岗位每日最大面试次数 |
| `MAX_FOLLOW_UP_COUNT` | 2 | 单题最大追问次数 |
| `ANSWER_TIMEOUT_SECONDS` | 30 | 回答超时时间（秒） |
| `INTERVIEW_RECOVERY_HOURS` | 24 | 面试中断后可恢复的时间窗口（小时） |

## 后续工作（TODO）

以下是 MVP 阶段尚未完成或需要完善的工作，按优先级排列：

### P0 - 核心流程完善

- [ ] JWT 认证完整实现（候选人手机号+验证码登录、HR 用户名密码登录）
- [x] OCR 证件识别对接真实 Qwen2-VL-72B API，实现证件信息提取
- [ ] 资质校验规则引擎实现（一票否决、准驾车型匹配、有效期校验）
- [ ] 评分池综合得分计算（基础资质 40% + 驾龄 25% + 附加证件 20% + 准驾类型 15%）
- [x] LLM 评分逻辑对接真实 Qwen3-235B API（意图理解、得分点判断、报告生成）
- [x] ASR/TTS 对接真实 DashScope API
- [x] 前端面试间 InterviewRoom 完整实现（VAD 录音 + WebSocket 通信 + TTS 播放）
- [ ] 前端候选人材料上传 + OCR 结果核对页面
- [ ] HR 后台岗位管理、题库管理的完整 CRUD
- [ ] 面试中断恢复功能（24小时内从断点继续）
- [x] 前端设备检测（麦克风权限 + 网络状态）

### P1 - 体验增强

- [ ] 面试过程录音保存，HR 可复听
- [ ] 模拟面试功能（不计分练习）
- [ ] HR 数据看板（招聘漏斗、通过率等）
- [ ] 批量候选人导入（CSV + 图片包）
- [ ] 消息通知（材料审核结果、面试邀请）

### 演进路线

MVP 验证通过后有两条演进方向：
- **Track A - 客户端软件**：Tauri + Python Sidecar，离线可用，企业本地部署
- **Track B - 微信 H5**：云部署 FastAPI + PostgreSQL，微信生态，候选人自助

详细需求参考 `spec/` 目录下的需求规格说明书。

## 相关文档

- `spec/AI面试官系统需求规格说明书V6_0-MVP版.md` - V6.0 需求规格说明书
- `spec/AI面试官系统需求规格说明书V6_1-MVP版.md` - V6.1 需求规格说明书（含种子数据设计）
