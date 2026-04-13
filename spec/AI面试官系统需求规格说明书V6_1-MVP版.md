# AI面试官系统需求规格说明书

**文档版本**：V6.1  
**编制日期**：2026-04-06  
**项目名称**：AI面试官系统  
**目标用户**：HR招聘人员、候选人（蓝领岗位）  
**本版说明**：在V6.0基础上新增第15章——系统初始化数据，以卡车司机岗位为基准设计完整的种子数据（岗位配置、题库、资质规则、HR账号、系统参数），支持系统开箱即用。

---

## 目录

1. [项目概述](#1-项目概述)
2. [业务背景与痛点分析](#2-业务背景与痛点分析)
3. [系统整体架构](#3-系统整体架构)
4. [功能需求](#4-功能需求)
5. [非功能需求](#5-非功能需求)
6. [业务规则](#6-业务规则)
7. [数据模型](#7-数据模型)
8. [接口需求](#8-接口需求)
9. [验收标准](#9-验收标准)
10. [测试策略](#10-测试策略)
11. [项目实施计划](#11-项目实施计划)
12. [系统部署与维护](#12-系统部署与维护)
13. [演进路线图](#13-演进路线图)
14. [附录](#14-附录)
15. [系统初始化数据](#15-系统初始化数据)

---

## 1. 项目概述

### 1.1 项目背景

本系统面向蓝领岗位（如卡车司机、集装箱操作工、叉车司机等）的招聘面试场景，通过AI技术实现从资质材料初筛到语音面试的全流程自动化。

### 1.2 项目目标

| 目标 | 描述 | 量化指标 |
|------|------|----------|
| 提升筛选效率 | 自动化简历筛选与初筛 | 替代80%HR人工初筛工作 |
| 降低招聘成本 | 减少重复性劳动 | 招聘成本降低30%以上 |
| 标准化评估 | 统一面试评估标准 | 评估一致性达95%以上 |
| 7×24服务 | 全天候AI面试能力 | 支持候选人随时参与 |

### 1.3 阶段规划

```
┌─────────────────────────────────────────────────────┐
│                    产品演进路线                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Phase 1: MVP（当前）                                │
│  Python + React + SQLite 本地单机部署                │
│  验证核心面试流程、积累数据、打磨产品逻辑              │
│                      │                              │
│         ┌────────────┴────────────┐                 │
│         ▼                        ▼                  │
│  Track A: 客户端软件             Track B: 微信H5      │
│  Tauri + Python Sidecar         云部署 FastAPI       │
│  离线可用，企业本地部署           微信生态，候选人自助  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**MVP阶段目标**：以最小开发成本验证以下核心假设：
- AI语音面试流程的可行性与候选人接受度
- LangGraph状态机对面试流程的控制有效性
- OCR + 规则引擎对蓝领资质材料的适配性

### 1.4 核心流程概览

```
┌─────────────────────────────────────────────────────────────┐
│                         AI面试官系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  资质材料   │───▶│  语音面试   │───▶│  结果评估   │      │
│  │   初筛模块  │    │   流程模块  │    │    模块     │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
│        │                  │                  │               │
│        ▼                  ▼                  ▼               │
│  • 材料提交          • LangGraph状态机   • 多维度评分        │
│  • OCR识别           • ASR语音识别       • 综合报告生成      │
│  • 规则校验          • LLM意图理解       • 决策建议          │
│  • 综合打分          • 智能追问                              │
│  • 评分池管理        • 异常处理                              │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │                    HR管理后台                        │     │
│  │  岗位管理 | 题库管理 | 候选人管理 | 结果查看 | 决策  │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 业务背景与痛点分析

### 2.1 传统招聘流程痛点

| 痛点 | 描述 | 影响 |
|------|------|------|
| **筛选效率低** | 手动筛选大量重复简历 | 增加人力成本 |
| **推进困难** | 业务部门反馈候选人评价主观性强 | 候选人质量参差不齐 |
| **面试官能力参差** | 不同岗位、层级的提问缺乏针对性 | 评价标准不统一 |
| **候选人体验差** | 面试官提问造成紧张感，蓝领岗位尤为突出 | 影响面试质量与到面率 |
| **流程周期长** | 受时间、空间限制，约面难度大 | 候选人流失率高 |

### 2.2 目标用户分析

#### 2.2.1 HR用户

| 角色 | 需求 | 痛点 |
|------|------|------|
| HR专员 | 快速筛选候选人、批量发起面试 | 手动筛选工作量大 |
| HR主管 | 统一招聘标准、管控招聘质量 | 评价标准不统一 |

#### 2.2.2 候选人（蓝领）

| 需求 | 描述 |
|------|------|
| 操作简单 | 界面大字、流程引导，无需专业技能 |
| 便捷面试 | 随时随地参加，无需到场 |
| 即时反馈 | 面试结束后可查看结果 |
| 减少等待 | 无需等待HR安排，自助完成 |

---

## 3. 系统整体架构

### 3.1 MVP技术架构

MVP阶段采用单体架构，本地运行，无需云服务。

```
┌────────────────────────────────────────────────────────────┐
│                       MVP 技术架构                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   前端层（React）                      │  │
│  │   候选人端（H5-ready）    HR管理后台（桌面优先）        │  │
│  │   Vite + React + Tailwind CSS + Axios               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │ HTTP / WebSocket                 │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  后端层（FastAPI）                     │  │
│  │                                                      │  │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │  │
│  │  │  候选人API │ │   HR API  │ │   面试流程API      │  │  │
│  │  └───────────┘ └───────────┘ └───────────────────┘  │  │
│  │                                                      │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │          LangGraph 面试状态机                  │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────┘  │  │
│                          │                                  │
│           ┌──────────────┼──────────────┐                  │
│           ▼              ▼              ▼                   │
│  ┌──────────────┐ ┌───────────┐ ┌──────────────────────┐   │
│  │   SQLite DB  │ │ 本地文件  │ │    外部AI API         │   │
│  │  (核心数据)  │ │ (证件/录音)│ │ LLM + ASR + TTS      │   │
│  └──────────────┘ └───────────┘ └──────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 MVP技术选型

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| 前端框架 | React 18 + Vite | H5/桌面双端兼容 |
| 前端样式 | Tailwind CSS | 快速响应式开发 |
| 后端框架 | FastAPI (Python 3.11+) | 异步支持好，适合AI集成 |
| 状态机 | LangGraph | 管理面试流程状态转换 |
| 数据库 | SQLite (WAL模式) | 零配置，本地部署，MVP首选 |
| 文件存储 | 本地 `uploads/` 目录 | 按 `{date}/{candidate_id}/` 分层组织 |
| OCR识别 | Qwen2-VL-72B 多模态大模型 | 通过视觉理解直接解析证件，无需单独OCR服务 |
| 语音识别(ASR) | 阿里云百炼 FunASR API | DashScope托管，支持中文方言，无需本地部署模型 |
| 语音合成(TTS) | 阿里云百炼 CosyVoice-v3-Flash | DashScope托管，音色自然，低延迟 |
| 大语言模型 | Qwen3-235B-Instruct | 中移香港LMMP私有化部署，意图理解与追问生成 |
| 认证 | JWT (python-jose) | 简单JWT，无需复杂RBAC |
| 实时通信 | FastAPI WebSocket | 语音流传输 |
| 前后端通信 | Axios + REST | 标准HTTP接口 |

> **MVP选型原则**：统一使用企业已有AI平台资源，LLM/Vision走中移香港LMMP接口，ASR/TTS走阿里云百炼DashScope，减少多厂商账号管理成本。

### 3.3 AI能力层详细说明

| 能力 | 服务 | 模型 | 接口地址 |
|------|------|------|---------|
| LLM（意图理解/追问/报告生成） | 中移香港 LMMP | Qwen3-235B | `https://opensseapi.cmhk.com/CMHK-LMMP-PRD_Qwen3_235B_Ins/CMHK-LMMP-PRD/v1/chat/completions` |
| Vision OCR（证件识别） | 中移香港 LMMP | Qwen2-VL-72B | `https://opensseapi.cmhk.com/CMHK-LMMP-PRD_Qwen2_VL_72B/CMHK-LMMP-PRD/v1/chat/completions` |
| ASR（语音识别） | 阿里云百炼 DashScope | FunASR | `https://dashscope.aliyuncs.com/api/v1/services/audio/asr/...` |
| TTS（语音合成） | 阿里云百炼 DashScope | CosyVoice-v3-Flash | `https://dashscope.aliyuncs.com/api/v1/services/audio/tts/...` |
| VAD（说话检测） | 前端 JS | @ricky0123/vad-react | 浏览器端实时检测，无需后端 |

#### API密钥配置

| 变量名 | 用途 | 对应服务 |
|--------|------|---------|
| `LLM_API_KEY` | LLM文本推理鉴权 | 中移香港 LMMP |
| `VISION_API_KEY` | 多模态Vision鉴权 | 中移香港 LMMP |
| `DASHSCOPE_API_KEY` | ASR + TTS鉴权 | 阿里云百炼（一个Key同时覆盖） |

> **注意**：LLM和Vision使用同一平台（中移香港LMMP）但接口地址不同，需分别配置。ASR和TTS共用同一个`DASHSCOPE_API_KEY`。

### 3.4 用户界面设计规范

| 规范 | 说明 |
|------|------|
| 设计风格 | 简洁、专业，蓝领候选人端大字体、大按钮 |
| 主色调 | 蓝色系 (#1890FF)，辅助绿 (#52C41A)、橙 (#FAAD14) |
| 候选人端字号 | 正文≥16px，按钮≥18px，关键提示≥20px |
| HR端布局 | PC多列（数据密集），移动端单列降级 |
| 响应式 | 候选人端优先 375px 移动视口；HR端优先 1200px桌面视口 |
| 无障碍 | 操作提示配语音播报，减少候选人认知负担 |

---

## 4. 功能需求

### 功能优先级说明

- **P0（MVP必做）**：核心流程跑通，缺少则产品无法使用
- **P1（MVP可选）**：增强体验，待核心流程稳定后迭代
- **P2（演进阶段）**：生产级特性，在Track A/B中实现

### 4.1 资质材料初筛模块

#### 4.1.1 功能概述

候选人提交证件材料，系统通过OCR识别 + 规则校验自动完成资质审核，并按综合得分进行排名。

#### 4.1.2 功能清单

| 功能编号 | 功能名称 | 功能描述 | 优先级 |
|----------|----------|----------|--------|
| F01-01 | 材料上传 | 支持身份证、驾驶证、从业资格证拍照/文件上传 | P0 |
| F01-02 | Vision OCR识别 | 调用Qwen2-VL-72B解析证件图片，提取关键字段（姓名/证号/有效期/准驾车型等），支持人工核对修正 | P0 |
| F01-03 | 规则校验 | 校验证件有效期、准驾车型与岗位匹配 | P0 |
| F01-04 | 综合打分 | 根据材料完整度与资质计算综合得分 | P0 |
| F01-05 | 评分池管理 | 维护候选人得分排名，支持动态阈值触发面试 | P0 |
| F01-06 | 审核状态追踪 | 候选人可查看材料审核进度和结果 | P0 |
| F01-07 | 批量材料处理 | 支持批量导入候选人材料（CSV+图片包） | P1 |
| F01-08 | 证件有效期监控 | 自动标记即将过期的证件，提醒候选人更新 | P2 |

#### 4.1.3 页面设计要求

| 页面 | 功能 | 核心要素 |
|------|------|----------|
| 材料上传页（候选人） | 提交资质材料 | 拍照/选文件、格式提示、上传进度条、格式示例图 |
| 材料列表页（候选人） | 查看审核状态 | 材料类型、状态标签、审核时间、得分提示 |
| OCR核对页（候选人） | 核对识别信息 | 识别结果对照原图展示、可编辑字段、确认提交 |
| 候选人管理页（HR） | 候选人列表与状态 | 列表+筛选、综合得分排名、一键邀请面试 |

---

### 4.2 语音面试模块

#### 4.2.1 功能概述

系统核心模块，通过LangGraph状态机管理面试全流程，实现智能语音面试与实时评分。

#### 4.2.2 功能清单

| 功能编号 | 功能名称 | 功能描述 | 优先级 |
|----------|----------|----------|--------|
| F02-01 | 身份核验 | 面试开始前手机号+验证码核验身份 | P0 |
| F02-02 | 设备检测 | 检测麦克风权限和网络状态 | P0 |
| F02-03 | 开场介绍 | TTS播放面试开场白，说明流程和注意事项 | P0 |
| F02-04 | 题目播报 | TTS合成语音播放面试题目 | P0 |
| F02-05 | 实时语音识别 | VAD检测说话起止，WebSocket传输，ASR转写 | P0 |
| F02-06 | 意图理解与评分 | LLM分析回答内容，判断得分点覆盖情况 | P0 |
| F02-07 | 智能追问 | 未覆盖得分点时从话术库选择追问 | P0 |
| F02-08 | 状态机控制 | LangGraph管理面试节点状态流转 | P0 |
| F02-09 | 异常处理 | 空回答/噪音/超时的兜底处理 | P0 |
| F02-10 | 面试中断恢复 | 支持24小时内恢复中断的面试 | P0 |
| F02-11 | 评估报告生成 | 面试结束后自动生成多维度评估报告 | P0 |
| F02-12 | 防刷题机制 | 限制同一候选人每天最多3次面试 | P0 |
| F02-13 | 面试过程录音 | 保存面试录音供HR复听 | P1 |
| F02-14 | 模拟面试 | 提供不计分的模拟面试熟悉流程 | P1 |
| F02-15 | 语音情绪分析 | 分析候选人情绪状态辅助评估 | P2 |

#### 4.2.3 LangGraph状态机设计

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph 面试状态机                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌──────────────┐                         │
│                    │   Node A     │                         │
│                    │   Intro      │ ← TTS播放开场白          │
│                    └──────┬───────┘                         │
│                           │ 播放完毕                         │
│                           ▼                                 │
│                    ┌──────────────┐                         │
│                    │   Node B     │                         │
│                    │ Ask_Question │ ← 从题库抽题，TTS播放    │
│                    └──────┬───────┘                         │
│                           │ 播放完毕，开启麦克风              │
│                           ▼                                 │
│                    ┌──────────────┐                         │
│                    │   Node C     │                         │
│                    │Wait_and_ASR  │ ← VAD + WebSocket + ASR │
│                    └──────┬───────┘                         │
│                           │ 获取语音输入 / 超时(30s)          │
│                           ▼                                 │
│                    ┌──────────────┐                         │
│                    │   Node D     │                         │
│                    │Process_Answer│ ← 意图分发               │
│                    └──────┬───────┘                         │
│          ┌────────────────┼────────────┐                    │
│          ▼                ▼            ▼                    │
│  [分支1:异常]       [分支2:重播]  [分支3:正常]              │
│  空/极少/噪音        没听清请求    正常回答文本               │
│       │                  │            │                    │
│       ▼                  ▼            ▼                    │
│  播放fallback        重播当前题    进入Node E               │
│  返回Node C          返回Node C    LLM判断得分点             │
│                                       │                    │
│                          ┌────────────┤                    │
│                          ▼            ▼                    │
│                   [覆盖得分点]   [未覆盖得分点]              │
│                   记录满分       追问计数<2?                  │
│                   进入Node F          │                    │
│                                  ┌───┴────┐               │
│                                  ▼        ▼               │
│                              [是:追问]  [否:跳题]           │
│                              返回Node C  进入Node F         │
│                                                             │
│                    ┌──────────────┐                         │
│                    │   Node F     │                         │
│                    │    Finish    │ ← 题目完成判断           │
│                    └──────┬───────┘                         │
│          ┌────────────────┼────────────┐                    │
│          ▼                ▼            ▼                    │
│   [题目未完成]      [全部完成]     [异常中断]                │
│   返回Node B        生成报告      保存进度                   │
│                                   24h可恢复                 │
└─────────────────────────────────────────────────────────────┘
```

#### 4.2.4 各节点详细说明

##### Node A: Intro（开场）

| 属性 | 说明 |
|------|------|
| 功能描述 | TTS合成开场白，说明面试规则、题目数量、注意事项 |
| 音频来源 | Edge-TTS实时生成（MVP）/ 预录音频（演进） |
| 状态转移 | 播放完毕自动进入Node B |
| 异常处理 | 音频加载失败时显示文字开场白，用户点击确认继续 |

##### Node B: Ask_Question（出题）

| 属性 | 说明 |
|------|------|
| 功能描述 | 从题库按岗位、题型随机抽取题目，TTS播报 |
| 题目数据 | 题目文本 + 考核关键点列表 + 追问话术池 |
| 考核关键点示例 | "换人"、"打双闪"、"检查刹车"、"记录行程" |
| 防刷题 | 同一候选人同一题目本日已答则换题 |
| 状态转移 | TTS播放完毕后开启麦克风，进入Node C |

##### Node C: Wait_and_ASR（收音与转写）

| 属性 | 说明 |
|------|------|
| 功能描述 | 前端VAD检测说话起止，WebSocket传输音频，DashScope FunASR转写 |
| VAD方案 | @ricky0123/vad-react（浏览器端实时检测） |
| 超时设置 | 30秒无输入触发超时处理 |
| 超时话术 | "师傅，没听到您的回答，我们进入下一题" |
| 状态转移 | 说话结束→Node D；超时→Node F；主动挂断→保存退出 |

##### Node D: Process_Answer（意图解析与分发）

| 分支 | 触发条件 | 处理方式 | 状态转移 |
|------|----------|----------|----------|
| 分支1（异常） | ASR结果为空或字数<5 | 播放："师傅，刚刚没听清，能再说一遍吗？" | 返回Node C |
| 分支2（重播请求） | 检测到"没听清/再说一遍/重复一遍" | 重新播报当前题目 | 返回Node C |
| 分支3（超时） | 超过30秒无输入 | 记录超时，播放提示 | 进入Node F |
| 分支4（正常） | 有效回答文本（≥5字） | 回答+考核关键点→LLM判断 | 进入Node E |

##### Node E: Judge_Follow_up（追问决策）

| 条件 | 处理方式 | 追问计数器 | 状态转移 |
|------|----------|------------|----------|
| 覆盖全部得分点 | 记录满分 | 重置为0 | 返回Node B（下一题） |
| 未覆盖且计数<2 | 从话术库选追问话术，TTS播放 | 计数+1 | 返回Node C |
| 未覆盖且计数≥2 | 记录当前部分得分，不再追问 | 结束 | 进入Node F |

##### Node F: Finish（结束判断）

| 条件 | 处理方式 |
|------|----------|
| 题目未完成且可继续 | 返回Node B（下一题） |
| 所有题目已完成 | 调用LLM生成评估报告，结束面试 |
| 用户主动挂断 | 保存当前进度到SQLite，允许24小时内恢复 |
| 异常中断（网络等） | WebSocket断开时服务端保存最后状态 |

#### 4.2.5 追问话术管理

| 功能 | 说明 |
|------|------|
| 话术库存储 | 按岗位+题目类型分类，存于SQLite `follow_up_scripts` 表 |
| 智能选择 | LLM根据已覆盖/未覆盖的得分点自动选择合适话术 |
| MVP默认话术 | 预置3-5套通用追问话术，HR可在后台维护 |

---

### 4.3 HR管理后台

#### 4.3.1 功能概述

HR的操作中台，负责岗位配置、题库维护、候选人管理、面试结果查看与决策。

#### 4.3.2 功能清单

| 功能编号 | 功能名称 | 功能描述 | 优先级 |
|----------|----------|----------|--------|
| F03-01 | 岗位管理 | 创建/编辑岗位，设置录取名额、启动系数、资质要求 | P0 |
| F03-02 | 题库管理 | 管理面试题目、考核关键点、追问话术 | P0 |
| F03-03 | 候选人管理 | 查看候选人信息、材料审核状态、综合得分排名 | P0 |
| F03-04 | 面试管理 | 查看面试状态、结果、评估报告 | P0 |
| F03-05 | 系统设置 | 配置面试启动系数、每日限制次数等参数 | P0 |
| F03-06 | 数据看板 | 招聘漏斗、面试通过率、岗位填充进度 | P1 |
| F03-07 | 用户管理 | 管理HR账号（MVP阶段仅超管+专员两级） | P1 |
| F03-08 | 批量操作 | 批量导入候选人、批量发送面试邀请 | P1 |
| F03-09 | 操作日志 | 关键操作记录（材料审核、面试发起等） | P2 |

#### 4.3.3 权限说明（MVP简化版）

| 角色 | 权限范围 |
|------|---------|
| 超级管理员 | 全部功能 + 系统设置 + 用户管理 |
| HR专员 | 候选人管理 + 面试管理 + 结果查看（无系统设置） |

> **MVP说明**：暂不实现细粒度RBAC，超管/专员两级即可满足验证需求。

#### 4.3.4 页面设计要求

| 页面 | 功能 | 核心要素 |
|------|------|----------|
| 登录页 | HR认证 | 用户名+密码，JWT鉴权 |
| 仪表盘 | 系统概览 | 今日面试数、通过率、待审核材料数、评分池状态 |
| 岗位管理 | 岗位CRUD | 列表+新增/编辑表单，启动系数配置 |
| 题库管理 | 题目维护 | 题目列表、考核点编辑、追问话术管理 |
| 候选人管理 | 候选人列表 | 得分排名、状态筛选、材料预览、一键邀请 |
| 面试管理 | 面试记录 | 面试列表、状态、得分、报告查看 |

---

### 4.4 候选人端

#### 4.4.1 功能概述

候选人参与面试的入口，设计重点是操作简单、引导清晰，适配蓝领用户。

#### 4.4.2 功能清单

| 功能编号 | 功能名称 | 功能描述 | 优先级 |
|----------|----------|----------|--------|
| F04-01 | 注册登录 | 手机号+验证码注册（MVP阶段短信用测试码） | P0 |
| F04-02 | 个人信息完善 | 姓名、身份证号、工作经验等基本信息填写 | P0 |
| F04-03 | 材料上传 | 拍照/选文件上传证件材料 | P0 |
| F04-04 | 材料状态查询 | 查看审核进度和结果 | P0 |
| F04-05 | 面试邀请查看 | 接收并查看面试邀请详情 | P0 |
| F04-06 | 设备检测 | 麦克风权限检测、网络检测 | P0 |
| F04-07 | 正式面试 | 参与AI语音面试全流程 | P0 |
| F04-08 | 面试结果查看 | 查看得分和评估报告摘要 | P0 |
| F04-09 | 模拟面试 | 不计分的模拟练习 | P1 |
| F04-10 | 历史记录 | 查看历史面试记录 | P1 |
| F04-11 | 消息通知 | 材料审核结果、面试邀请推送 | P1 |

#### 4.4.3 候选人端关键设计原则

- **引导式交互**：每步操作有明确文字+图标引导，减少迷失感
- **宽容输入**：OCR识别错误可人工修正，语音识别不清可重说
- **进度可见**：面试中实时显示题目进度（第X题/共Y题）
- **容错友好**：网络断开有明确提示和恢复指引，不丢失作答进度

---

## 5. 非功能需求

### 5.1 性能需求（MVP阶段）

| 需求 | 描述 | MVP指标 | 演进目标 |
|------|------|---------|---------|
| 响应时间 | API响应时间 | ≤800ms（本地） | ≤500ms（云端） |
| 并发支持 | 同时在线用户 | 50人 | 1000人以上 |
| ASR延迟 | 语音转写延迟 | ≤800ms（DashScope FunASR，含网络往返） | ≤300ms（专线/内网） |
| LLM响应 | 意图理解耗时 | ≤3秒（含API网络延迟） | ≤1.5秒 |
| 文件上传 | 证件图片上传 | ≤5秒（本地网络） | ≤3秒 |
| SQLite并发 | 写操作性能 | WAL模式支持读写并发 | 迁移至PostgreSQL |

> **MVP说明**：不做压测，不追求万人并发。MVP目标是单企业/小团队验证流程，50并发足够。

### 5.2 可靠性需求（MVP阶段）

| 需求 | MVP要求 |
|------|---------|
| 面试数据持久化 | 每次状态变更立即写SQLite，防止中断丢失 |
| 文件备份 | 上传文件目录每日备份到指定位置（脚本实现） |
| 错误日志 | Python logging写入 `logs/` 目录，按日滚动 |
| 进程守护 | 生产环境用 systemd 或 pm2 守护FastAPI进程 |
| 前端离线 | React build为静态文件，FastAPI同时 serve静态资源 |

### 5.3 安全性需求（MVP阶段）

| 需求 | 实现方式 |
|------|---------|
| 接口认证 | JWT（HS256），候选人/HR分别签发，token 24小时有效 |
| 密码存储 | bcrypt哈希，不存明文 |
| 证件图片访问 | 文件路径不直接暴露，通过 `/api/file/{token}` 鉴权访问 |
| SQLite保护 | 数据库文件存于 `data/` 目录，配置系统级读写权限 |
| CORS | FastAPI 配置白名单域名 |
| 输入校验 | Pydantic模型校验所有API输入 |

> **MVP说明**：不做细粒度审计日志，不做多因素认证，不做RBAC细化。安全达到"防误用"级别即可，生产级安全在演进阶段补齐。

### 5.4 兼容性需求

| 端 | MVP要求 |
|----|---------|
| 候选人端浏览器 | Chrome 90+、微信内置浏览器（为H5演进做准备） |
| HR端浏览器 | Chrome 90+、Edge 90+ |
| 移动端 | iOS 14+、Android 9+（微信H5演进路线必须） |
| 操作系统（本地部署） | Windows 10+、macOS 12+、Ubuntu 20.04+ |

---

## 6. 业务规则

### 6.1 资质审核规则

| 规则 | 描述 | 适用场景 |
|------|------|----------|
| 一票否决制 | 缺少必填材料或材料不符合要求则直接标记拒绝 | 资质材料初筛 |
| 有效期校验 | 驾驶证/从业资格证必须在有效期内（或距过期>30天） | 驾驶类岗位 |
| 准驾车型匹配 | 驾驶证准驾车型必须覆盖岗位要求车型 | 司机岗位 |
| 重复投递处理 | 同一候选人同一岗位仅保留最新投递记录 | 材料提交 |
| 综合得分构成 | 基础资质分（60%）+ 经验年限分（20%）+ 附加材料分（20%） | 评分池排名 |

### 6.2 面试触发规则

| 规则 | 描述 |
|------|------|
| 动态阈值计算 | 触发面试邀请的最低分 = 历史面试通过分线 × 启动系数（默认1.2） |
| 最低面试人数 | 即使达到阈值，单批次面试人数不低于配置的最小人数（默认5人） |
| 批次触发时机 | HR手动触发或达到阈值自动触发（可配置） |

### 6.3 面试流程规则

| 规则 | 描述 |
|------|------|
| 每日限次 | 同一候选人同一岗位每天最多参加3次面试 |
| 追问限次 | 单题最多追问2次，避免面试时间过长 |
| 超时处理 | 连续30秒无输入，播放提示并跳转下一题 |
| 中断恢复 | 面试中断后24小时内可从上次断点恢复 |
| 题目顺序 | 固定顺序出题（MVP），演进阶段支持随机抽题 |

### 6.4 评分规则

| 规则 | 描述 |
|------|------|
| 单题得分 | LLM按覆盖得分点数量计算，满分10分 |
| 总分计算 | 各题得分加权求和，满分100分 |
| 超时题目 | 超时未回答记0分 |
| 报告生成 | 面试结束后LLM综合所有回答生成评估报告（技能、经验、沟通三维度） |

---

## 7. 数据模型

### 7.1 核心实体

| 实体 | 描述 | 关键字段 |
|------|------|----------|
| 候选人 (candidate) | 面试候选人信息 | 姓名、手机号、身份证号、综合得分、状态 |
| 岗位 (job) | 招聘岗位配置 | 岗位名称、录取名额、启动系数、资质要求 |
| 面试 (interview) | 面试记录 | 候选人ID、岗位ID、状态、当前节点、得分 |
| 题目 (question) | 面试题目库 | 题目内容、考核关键点(JSON)、追问话术(JSON) |
| 材料 (document) | 候选人证件材料 | 候选人ID、类型、文件路径、OCR结果(JSON)、得分 |
| HR用户 (user) | HR账号 | 用户名、密码(哈希)、角色 |
| 评分池 (score_pool) | 候选人资质排名 | 候选人ID、岗位ID、综合得分、排名、是否已邀请 |

### 7.2 关系模型

```
candidate ──< document (1:N)
candidate ──< interview (1:N)
candidate ──< score_pool (1:N)
job       ──< interview (1:N)
job       ──< question  (1:N)
job       ──< score_pool (1:N)
interview ──< interview_answer (1:N)
question  ──< interview_answer (N:M, through interview)
user      (独立，HR账号体系)
```

### 7.3 数据存储方案（MVP）

| 数据类型 | 存储方式 | 说明 |
|----------|----------|------|
| 所有结构化数据 | SQLite（WAL模式） | 候选人、岗位、面试、题目等全部核心数据 |
| 面试过程数据 | SQLite JSON字段 | `interview.interview_data` 存储LangGraph状态快照 |
| 评估报告 | SQLite TEXT字段 | `interview.report_content` 存储Markdown格式报告 |
| 证件图片/录音 | 本地文件 `uploads/` | 按 `{YYYY-MM}/{candidate_id}/` 层级组织 |
| 应用日志 | 本地文件 `logs/` | 按日滚动，保留30天 |

> **演进说明**：Track B（微信H5）上云时，SQLite → PostgreSQL；本地文件 → 对象存储（阿里OSS/腾讯COS）。迁移脚本在演进阶段提供。

### 7.4 SQLite表结构设计

#### 7.4.1 候选人表 (candidate)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 候选人ID |
| name | TEXT | NOT NULL | 姓名 |
| phone | TEXT | NOT NULL UNIQUE | 手机号 |
| id_card | TEXT | NOT NULL UNIQUE | 身份证号 |
| gender | INTEGER | DEFAULT 1 | 性别(1-男,2-女) |
| age | INTEGER | | 年龄 |
| education | TEXT | | 学历 |
| work_experience | INTEGER | DEFAULT 0 | 工作年限 |
| address | TEXT | | 居住地址 |
| status | INTEGER | NOT NULL DEFAULT 0 | 0-未审核,1-审核中,2-通过,3-拒绝 |
| total_score | REAL | DEFAULT 0 | 综合得分 |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |
| updated_at | TEXT | DEFAULT (datetime('now')) | 更新时间 |

#### 7.4.2 岗位表 (job)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 岗位ID |
| name | TEXT | NOT NULL | 岗位名称 |
| description | TEXT | | 岗位描述 |
| requirements | TEXT | | 岗位要求(Markdown) |
| quota | INTEGER | NOT NULL DEFAULT 1 | 录取名额 |
| start_coefficient | REAL | NOT NULL DEFAULT 1.2 | 启动系数 |
| min_interview_count | INTEGER | DEFAULT 5 | 最小面试人数 |
| required_license_type | TEXT | | 要求准驾车型(JSON数组) |
| status | INTEGER | NOT NULL DEFAULT 0 | 0-草稿,1-发布中,2-已结束 |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |
| updated_at | TEXT | DEFAULT (datetime('now')) | 更新时间 |

#### 7.4.3 面试表 (interview)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 面试ID |
| candidate_id | INTEGER | NOT NULL, FK→candidate | 候选人ID |
| job_id | INTEGER | NOT NULL, FK→job | 岗位ID |
| start_time | TEXT | | 开始时间 |
| end_time | TEXT | | 结束时间 |
| status | INTEGER | NOT NULL DEFAULT 0 | 0-待开始,1-进行中,2-已完成,3-已中断,4-已取消 |
| score | REAL | DEFAULT 0 | 面试总得分 |
| current_question_index | INTEGER | DEFAULT 0 | 当前题目索引 |
| current_node | TEXT | DEFAULT 'Intro' | 当前状态机节点 |
| interview_data | TEXT | | LangGraph状态快照(JSON) |
| report_content | TEXT | | 评估报告(Markdown) |
| today_count | INTEGER | DEFAULT 0 | 当日面试次数（防刷题） |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |
| updated_at | TEXT | DEFAULT (datetime('now')) | 更新时间 |

#### 7.4.4 题目表 (question)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 题目ID |
| job_id | INTEGER | NOT NULL, FK→job | 关联岗位 |
| content | TEXT | NOT NULL | 题目内容 |
| type | INTEGER | NOT NULL DEFAULT 1 | 1-基础,2-专业,3-情景 |
| difficulty | INTEGER | DEFAULT 2 | 1-简单,2-中等,3-困难 |
| score_points | TEXT | NOT NULL | 评分关键点(JSON数组) |
| follow_up_scripts | TEXT | | 追问话术(JSON数组) |
| tts_audio_path | TEXT | | 预生成TTS音频路径（可选） |
| is_active | INTEGER | DEFAULT 1 | 是否启用 |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |

#### 7.4.5 材料表 (document)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 材料ID |
| candidate_id | INTEGER | NOT NULL, FK→candidate | 候选人ID |
| type | INTEGER | NOT NULL | 1-身份证,2-驾驶证,3-从业资格证,4-其他 |
| file_path | TEXT | NOT NULL | 相对文件路径 |
| file_name | TEXT | NOT NULL | 原始文件名 |
| file_size | INTEGER | | 文件大小(字节) |
| ocr_result | TEXT | | OCR识别结果(JSON) |
| status | INTEGER | DEFAULT 0 | 0-待审核,1-审核中,2-通过,3-拒绝 |
| reject_reason | TEXT | | 拒绝原因 |
| score | REAL | DEFAULT 0 | 材料得分 |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |

#### 7.4.6 HR用户表 (user)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户ID |
| username | TEXT | NOT NULL UNIQUE | 用户名 |
| password_hash | TEXT | NOT NULL | bcrypt哈希密码 |
| name | TEXT | NOT NULL | 真实姓名 |
| phone | TEXT | | 手机号 |
| role | TEXT | NOT NULL DEFAULT 'specialist' | admin/specialist |
| is_active | INTEGER | DEFAULT 1 | 是否启用 |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |

#### 7.4.7 评分池表 (score_pool)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 记录ID |
| candidate_id | INTEGER | NOT NULL, FK→candidate, UNIQUE(candidate_id, job_id) | 候选人ID |
| job_id | INTEGER | NOT NULL, FK→job | 岗位ID |
| doc_score | REAL | DEFAULT 0 | 材料得分 |
| rank | INTEGER | | 当前排名 |
| is_invited | INTEGER | DEFAULT 0 | 是否已邀请面试 |
| updated_at | TEXT | DEFAULT (datetime('now')) | 最后更新时间 |

#### 7.4.8 面试回答表 (interview_answer)

| 字段名 | 类型 | 约束 | 描述 |
|--------|------|------|------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 回答ID |
| interview_id | INTEGER | NOT NULL, FK→interview | 面试ID |
| question_id | INTEGER | NOT NULL, FK→question | 题目ID |
| question_order | INTEGER | NOT NULL | 题目顺序 |
| answer_text | TEXT | | ASR转写文本 |
| answer_audio_path | TEXT | | 录音文件路径（P1功能） |
| follow_up_count | INTEGER | DEFAULT 0 | 追问次数 |
| score | REAL | DEFAULT 0 | 本题得分 |
| score_detail | TEXT | | 得分明细(JSON) |
| created_at | TEXT | DEFAULT (datetime('now')) | 创建时间 |

#### 7.4.9 SQLite配置建议

```sql
-- 初始化时执行
PRAGMA journal_mode = WAL;      -- 支持读写并发
PRAGMA synchronous = NORMAL;    -- 性能与安全平衡
PRAGMA foreign_keys = ON;       -- 启用外键约束
PRAGMA temp_store = MEMORY;     -- 临时表放内存
PRAGMA cache_size = -64000;     -- 64MB缓存
```

---

## 8. 接口需求

### 8.1 API设计原则

| 原则 | 说明 |
|------|------|
| RESTful风格 | 资源导向URL设计 |
| 版本前缀 | 所有接口以 `/api/v1/` 开头 |
| 统一响应格式 | `{"code": 200, "message": "success", "data": {...}}` |
| JWT认证 | 请求头 `Authorization: Bearer <token>` |
| Pydantic校验 | 所有请求体通过Pydantic模型校验 |
| 异步实现 | FastAPI async/await，避免阻塞 |

### 8.2 核心API接口清单

#### 8.2.1 候选人接口

| 接口路径 | 方法 | 功能描述 | 认证 |
|----------|------|----------|------|
| /api/v1/candidate/register | POST | 候选人注册（手机号+验证码） | 无 |
| /api/v1/candidate/login | POST | 候选人登录 | 无 |
| /api/v1/candidate/profile | GET | 获取个人信息 | 需要 |
| /api/v1/candidate/profile | PUT | 更新个人信息 | 需要 |
| /api/v1/candidate/documents | POST | 上传资质材料 | 需要 |
| /api/v1/candidate/documents | GET | 获取材料列表和状态 | 需要 |
| /api/v1/candidate/interviews | GET | 获取面试邀请列表 | 需要 |
| /api/v1/candidate/interviews/{id} | GET | 获取面试详情 | 需要 |
| /api/v1/candidate/interviews/{id}/start | POST | 开始面试 | 需要 |
| /api/v1/candidate/interviews/{id}/recover | POST | 恢复中断面试 | 需要 |
| /api/v1/candidate/interviews/{id}/result | GET | 获取面试结果 | 需要 |

#### 8.2.2 HR接口

| 接口路径 | 方法 | 功能描述 | 认证 |
|----------|------|----------|------|
| /api/v1/hr/login | POST | HR登录 | 无 |
| /api/v1/hr/dashboard | GET | 仪表盘数据 | 需要 |
| /api/v1/hr/jobs | GET/POST | 岗位列表/新增 | 需要 |
| /api/v1/hr/jobs/{id} | GET/PUT/DELETE | 岗位详情/编辑/删除 | 需要 |
| /api/v1/hr/questions | GET/POST | 题目列表/新增 | 需要 |
| /api/v1/hr/questions/{id} | PUT/DELETE | 题目编辑/删除 | 需要 |
| /api/v1/hr/candidates | GET | 候选人列表（含得分排名） | 需要 |
| /api/v1/hr/candidates/{id} | GET | 候选人详情 | 需要 |
| /api/v1/hr/candidates/{id}/invite | POST | 发起面试邀请 | 需要 |
| /api/v1/hr/interviews | GET | 面试列表 | 需要 |
| /api/v1/hr/interviews/{id} | GET | 面试详情+报告 | 需要 |
| /api/v1/hr/score-pool | GET | 评分池列表 | 需要 |
| /api/v1/hr/settings | GET/PUT | 系统参数配置 | 需要(admin) |

#### 8.2.3 面试流程接口

| 接口路径 | 方法 | 功能描述 | 认证 |
|----------|------|----------|------|
| /api/v1/interview/{id}/state | GET | 获取当前面试状态（支持恢复） | 需要 |
| /api/v1/interview/{id}/submit-answer | POST | 提交文本回答（ASR完成后） | 需要 |
| /api/v1/interview/{id}/timeout | POST | 通知超时事件 | 需要 |
| /api/v1/interview/{id}/abort | POST | 主动中断，保存进度 | 需要 |

#### 8.2.4 文件访问接口

| 接口路径 | 方法 | 功能描述 |
|----------|------|----------|
| /api/v1/files/{file_token} | GET | 鉴权后返回文件流（证件图片等） |

### 8.3 WebSocket接口

| 接口路径 | 功能描述 | 数据格式 |
|----------|----------|----------|
| /ws/interview/{interview_id} | 面试实时通信（音频流+状态推送） | 二进制(音频) + JSON(状态) |

#### WebSocket消息类型

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `audio_chunk` | 客户端→服务端 | 音频PCM数据块 |
| `audio_end` | 客户端→服务端 | 说话结束信号（VAD触发） |
| `timeout` | 客户端→服务端 | 30秒超时通知 |
| `state_update` | 服务端→客户端 | 状态机节点变化 |
| `tts_audio` | 服务端→客户端 | TTS音频数据 |
| `asr_result` | 服务端→客户端 | ASR转写结果 |
| `score_update` | 服务端→客户端 | 题目得分更新 |
| `interview_end` | 服务端→客户端 | 面试结束通知 |

### 8.4 通用响应格式

**成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**失败响应**：
```json
{
  "code": 400,
  "message": "参数错误：手机号格式不正确",
  "data": null
}
```

**错误码定义**：

| 错误码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或Token失效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 数据冲突（如手机号已注册） |
| 500 | 服务器内部错误 |
| 600 | 业务逻辑错误（如面试次数已达上限） |

---

## 9. 验收标准

### 9.1 MVP核心流程验收

| 验收场景 | 验收标准 |
|----------|----------|
| 候选人注册并上传材料 | 注册→上传→OCR识别→得分计算全链路跑通，耗时<30秒 |
| HR查看评分池并触发面试 | HR能看到候选人排名，一键发送面试邀请 |
| 候选人完成完整面试 | 设备检测→开场→5题面试→结束→报告生成，全程无需人工干预 |
| 智能追问生效 | 回答不完整时系统至少追问1次，且追问内容与缺失得分点相关 |
| 面试中断恢复 | 模拟断线后重新进入，从上次断点继续，已答题目不重复 |
| HR查看面试结果 | 能查看候选人得分、各题回答文本、三维度评估报告 |

### 9.2 功能验收明细

| 模块 | 验收项 | 验收标准 |
|------|--------|----------|
| 资质初筛 | OCR识别 | 证件文字识别准确率≥90%（清晰照片） |
| 资质初筛 | 规则校验 | 一票否决和准驾匹配逻辑执行正确 |
| 资质初筛 | 评分计算 | 综合得分计算公式执行一致 |
| 语音面试 | ASR转写 | 普通话环境下转写准确率≥85% |
| 语音面试 | 意图理解 | LLM对得分点覆盖判断准确率≥80%（人工抽查20题） |
| 语音面试 | 状态机流转 | 所有节点跳转逻辑符合设计，无死循环 |
| 语音面试 | 超时处理 | 30秒无输入正确触发超时流程 |
| HR后台 | 岗位管理 | CRUD正常，题目关联正确 |
| HR后台 | 候选人管理 | 得分排名实时更新，邀请操作正常 |
| 候选人端 | 设备检测 | 麦克风无权限时有清晰引导 |
| 候选人端 | 面试UI | 题目进度、录音状态、计时提示清晰可见 |

### 9.3 性能验收（MVP）

| 指标 | 验收标准 |
|------|----------|
| 页面加载 | 首屏加载≤3秒（本地localhost） |
| API响应 | 非AI接口P99≤800ms |
| ASR延迟 | 说话结束到文字显示≤1秒（FunASR本地） |
| LLM响应 | 意图判断返回≤5秒（含网络） |
| 数据库 | SQLite查询响应≤100ms（小于10万条数据） |

---

## 10. 测试策略

### 10.1 测试工具栈（Python生态）

| 测试类型 | 工具 | 说明 |
|----------|------|------|
| 后端单元测试 | pytest + pytest-asyncio | FastAPI路由、业务逻辑、数据库操作 |
| API集成测试 | httpx + TestClient（FastAPI内置） | 端到端API测试，含认证流程 |
| 前端组件测试 | Vitest + React Testing Library | React组件行为测试 |
| 状态机测试 | pytest + LangGraph测试工具 | 面试状态流转的路径覆盖测试 |
| 手工测试 | Postman / Bruno | 接口调试与验证 |
| Mock测试 | pytest-mock + responses | Mock外部AI API，避免测试消耗费用 |

### 10.2 测试重点

| 重点 | 说明 |
|------|------|
| LangGraph状态机路径覆盖 | 覆盖所有分支：正常回答、异常输入、超时、追问、中断恢复 |
| AI接口Mock | 所有LLM/ASR/TTS调用用Mock代替，确保测试速度和可重复性 |
| 并发写测试 | SQLite WAL模式下并发写入正确性测试 |
| 文件上传测试 | 各类图片格式、超大文件、恶意文件名的处理 |
| JWT安全测试 | Token过期、伪造Token、越权访问测试 |

### 10.3 测试阶段安排

| 阶段 | 内容 | 时机 |
|------|------|------|
| 单元测试 | 核心业务函数 | 开发同步进行，PR合并前必须通过 |
| 集成测试 | API端到端流程 | 每个功能模块完成后 |
| 冒烟测试 | 完整面试流程 | 每个Sprint结束时人工执行 |
| 回归测试 | 全量测试套件 | 版本发布前 |

---

## 11. 项目实施计划

### 11.1 MVP开发节奏（6周）

| Sprint | 周次 | 交付目标 |
|--------|------|----------|
| Sprint 0 | 第1周 | 项目脚手架：FastAPI + React + SQLite集成；数据库初始化；JWT认证框架 |
| Sprint 1 | 第2周 | 资质初筛模块：候选人注册、材料上传、OCR对接、规则校验、评分池 |
| Sprint 2 | 第3周 | 面试状态机：LangGraph状态机实现，TTS/ASR接口对接，WebSocket通信 |
| Sprint 3 | 第4周 | 完整面试流程：前端面试页面，追问逻辑，报告生成，中断恢复 |
| Sprint 4 | 第5周 | HR管理后台：岗位管理、题库管理、候选人管理、面试结果查看 |
| Sprint 5 | 第6周 | 集成联调：端到端流程测试、Bug修复、MVP验收、部署文档 |

### 11.2 资源配置（最小化）

| 角色 | 人数 | 职责 |
|------|------|------|
| 全栈开发（Python+React） | 1-2人 | 所有功能开发 |
| AI辅助 | Claude等工具 | 代码生成、测试用例、文档 |
| 产品/业务 | 1人（兼任） | 需求确认、验收测试 |

### 11.3 关键依赖与风险

| 风险 | 影响 | 应对 |
|------|------|------|
| DashScope FunASR方言识别效果差 | ASR准确率低，影响面试体验 | 切换 `paraformer-realtime-v2` 其他方言模型，或提供文字输入备用通道 |
| LMMP接口延迟高或限流 | 意图判断>5秒，面试体验差 | 设置3秒超时后给默认得分，异步补打分；与中移香港确认QPS配额 |
| 微信内置浏览器麦克风权限 | H5演进路线受阻 | MVP阶段Chrome验证，H5阶段专项测试微信权限 |
| SQLite并发写瓶颈 | 演进阶段多用户并发 | MVP不受影响；演进前按计划迁移PostgreSQL |

---

## 12. 系统部署与维护

### 12.1 MVP本地部署

#### 12.1.1 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20.04+ |
| 磁盘空间 | ≥5GB（含模型文件） |
| 内存 | ≥4GB（ASR/TTS走云端API，无本地模型） |

#### 12.1.2 本地启动流程

```bash
# 1. 克隆仓库并进入项目
git clone <repo_url> && cd ai-interviewer

# 2. 后端环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. 环境变量配置
cp .env.example .env
# 编辑 .env：配置 LLM_API_KEY, OCR_API_KEY 等

# 4. 数据库初始化
python scripts/init_db.py

# 5. 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 前端环境（新终端）
cd frontend
npm install
npm run dev  # 访问 http://localhost:5173
```

#### 12.1.3 目录结构

```
ai-interviewer/
├── app/                    # FastAPI后端
│   ├── main.py             # 应用入口
│   ├── api/                # 路由层
│   │   ├── candidate.py
│   │   ├── hr.py
│   │   └── interview.py
│   ├── services/           # 业务逻辑层
│   │   ├── interview_state_machine.py  # LangGraph状态机
│   │   ├── ocr_service.py
│   │   ├── asr_service.py
│   │   ├── tts_service.py
│   │   └── llm_service.py
│   ├── models/             # SQLite数据模型 (SQLAlchemy)
│   ├── schemas/            # Pydantic请求/响应模型
│   └── core/               # 配置、认证等
├── frontend/               # React前端 (Vite)
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── candidate/  # 候选人端
│   │   │   └── hr/         # HR后台
│   │   ├── components/     # 通用组件
│   │   └── services/       # API调用层
├── data/                   # SQLite数据库文件
│   └── ai_interviewer.db
├── uploads/                # 上传文件（证件、录音）
│   └── {YYYY-MM}/{candidate_id}/
├── logs/                   # 应用日志
├── scripts/                # 初始化/维护脚本
├── tests/                  # 测试用例
├── .env.example            # 环境变量模板
└── requirements.txt
```

### 12.2 MVP生产环境部署（单机）

适用于小规模内部使用（< 100 并发）：

```bash
# 后端：使用 gunicorn + uvicorn workers
gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --daemon

# 前端：构建静态文件，由FastAPI serve
cd frontend && npm run build
# FastAPI 中挂载 StaticFiles 到 /frontend/dist

# 进程守护（Linux）
# 创建 /etc/systemd/system/ai-interviewer.service
systemctl enable ai-interviewer
systemctl start ai-interviewer
```

### 12.3 环境变量配置说明

`.env` 文件完整模板：

```dotenv
# ── 基础配置 ──────────────────────────────────────────────
DATABASE_URL=sqlite:///./data/ai_interviewer.db
SECRET_KEY=<随机32位字符串>
UPLOAD_DIR=./uploads
MAX_DAILY_INTERVIEWS=3

# ── LLM：中移香港 LMMP - Qwen3-235B ──────────────────────
LLM_API_URL=https://opensseapi.cmhk.com/CMHK-LMMP-PRD_Qwen3_235B_Ins/CMHK-LMMP-PRD/v1/chat/completions
LLM_API_KEY=
LLM_MODEL=Qwen3-235B

# ── Vision OCR：中移香港 LMMP - Qwen2-VL-72B ─────────────
VISION_API_URL=https://opensseapi.cmhk.com/CMHK-LMMP-PRD_Qwen2_VL_72B/CMHK-LMMP-PRD/v1/chat/completions
VISION_API_KEY=
VISION_MODEL=Qwen2-VL-72B

# ── ASR + TTS：阿里云百炼 DashScope ──────────────────────
DASHSCOPE_API_KEY=
ASR_MODEL=paraformer-realtime-v2
TTS_MODEL=cosyvoice-v3-flash
TTS_VOICE=longxiaochun    # 可选音色，参考DashScope文档
```

| 变量名 | 说明 |
|--------|------|
| `LLM_API_URL` | Qwen3-235B推理接口地址（中移香港LMMP） |
| `LLM_API_KEY` | LLM接口鉴权Key |
| `LLM_MODEL` | 固定值 `Qwen3-235B` |
| `VISION_API_URL` | Qwen2-VL-72B视觉接口地址（中移香港LMMP） |
| `VISION_API_KEY` | Vision接口鉴权Key（与LLM_API_KEY可能相同，按实际填写） |
| `VISION_MODEL` | 固定值 `Qwen2-VL-72B` |
| `DASHSCOPE_API_KEY` | 阿里云百炼API Key，ASR和TTS共用 |
| `ASR_MODEL` | FunASR托管模型名，`paraformer-realtime-v2` 支持实时流式识别 |
| `TTS_MODEL` | CosyVoice低延迟版，`cosyvoice-v3-flash` |
| `TTS_VOICE` | TTS音色选择，建议选偏中性/温和的音色适配蓝领候选人 |

---

## 13. 演进路线图

### 13.1 演进决策矩阵

| 维度 | Track A：客户端软件 | Track B：微信H5 |
|------|-------------------|----------------|
| 目标场景 | 企业HR工具，本地/内网部署 | 候选人自助，C端大规模触达 |
| 核心优势 | 离线可用，数据本地，麦克风权限稳定 | 无需安装，微信直达，覆盖面广 |
| 核心挑战 | 分发安装麻烦，更新机制复杂 | 云部署成本，微信浏览器音频兼容性 |
| 音频方案 | 系统麦克风，无权限问题 | 微信JS-SDK授权 + WebRTC |
| 数据库 | SQLite保持本地 | 迁移至PostgreSQL（阿里云RDS） |
| 认证方式 | 本地JWT | 微信OAuth授权 + JWT |
| 预计启动时机 | MVP验证后1-2个月 | MVP验证后2-3个月 |

### 13.2 Track A：客户端软件演进

#### 技术方案

基于MVP的Python+React，用**Tauri**打包为桌面应用（Windows/macOS/Linux），Python后端作为**Sidecar进程**随应用启动。

```
┌─────────────────────────────────────────────────────────┐
│                   Tauri 客户端应用                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────┐   ┌───────────────────────┐   │
│  │   Tauri WebView      │   │   Python Sidecar      │   │
│  │   (React前端)        │──▶│   (FastAPI后端)        │   │
│  │                     │   │   + LangGraph          │   │
│  └─────────────────────┘   │   + SQLite              │   │
│                            │   (AI能力调用云端API)    │   │
│                            └───────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 改造要点

| 改造项 | 说明 |
|--------|------|
| Tauri集成 | `src-tauri/` 目录，配置sidecar启动FastAPI进程 |
| Python打包 | PyInstaller将FastAPI+依赖打包为单一可执行文件 |
| 自动更新 | Tauri updater + 私有update server |
| 本地模型 | 无需本地模型，AI能力全部调用云端API（LMMP + DashScope） |
| 安装包 | Windows NSIS安装包，macOS .dmg，Linux AppImage |
| 数据迁移 | SQLite数据库随客户端，可导出/备份 |

#### 关键文件调整

```
ai-interviewer/
├── src-tauri/              # 新增Tauri配置
│   ├── tauri.conf.json     # Tauri配置，声明sidecar
│   ├── src/main.rs         # Rust入口（Tauri boilerplate）
│   └── sidecar/            # Python sidecar可执行文件目录
├── app/                    # FastAPI后端（无需改动）
└── frontend/               # React前端（无需改动）
```

### 13.3 Track B：微信H5演进

#### 技术方案

MVP的React前端直接复用（需适配移动端），FastAPI后端迁移到云部署，数据库从SQLite迁移至PostgreSQL，增加微信OAuth登录。

```
┌─────────────────────────────────────────────────────────┐
│                   微信H5服务架构                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  微信用户 → 公众号/小程序 → H5链接                         │
│                    │                                    │
│                    ▼                                    │
│         ┌──────────────────┐                           │
│         │   CDN (静态资源)  │                           │
│         │   React Build    │                           │
│         └──────────────────┘                           │
│                    │                                    │
│                    ▼                                    │
│         ┌──────────────────┐                           │
│         │   FastAPI服务     │                           │
│         │   (ECS/容器)      │                           │
│         └──────────────────┘                           │
│                    │                                    │
│      ┌─────────────┼──────────────┐                    │
│      ▼             ▼              ▼                    │
│  PostgreSQL    对象存储         微信API                  │
│  (RDS)         (OSS/COS)       (OAuth+JS-SDK)          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 改造要点

| 改造项 | 说明 |
|--------|------|
| 微信授权登录 | 集成微信OAuth，获取openid作为候选人唯一标识；同时保留手机号注册 |
| 微信JS-SDK音频 | 调用 `wx.startRecord()` / `wx.stopRecord()` 录音接口；需公众号认证 |
| WebRTC音频兜底 | 非微信浏览器降级使用MediaRecorder API |
| 数据库迁移 | SQLite → PostgreSQL，提供一次性迁移脚本 |
| 文件存储迁移 | 本地目录 → 阿里OSS（保持接口不变，替换storage层实现） |
| 云部署配置 | Docker容器化，Nginx反向代理，Let's Encrypt HTTPS |
| 短信服务 | 集成阿里云SMS或腾讯云SMS（替换MVP测试验证码） |
| 消息推送 | 微信模板消息推送面试邀请和结果通知 |

#### 微信H5关键兼容性注意事项

```
微信内置浏览器音频限制：
1. 必须通过 wx.config() 注入授权，才能调用录音API
2. 录音时长单次最长60秒（需分段处理长回答）
3. 录音格式为AMR，需服务端转码为PCM后送ASR
4. iOS微信与Android微信行为略有差异，需分别测试

解决方案：
- 封装 WechatAudioService 和 WebRTCAudioService 两套实现
- 根据 navigator.userAgent 自动选择
- 提供文字输入作为音频失败的兜底方案
```

### 13.4 共享演进优先级

以下功能在两条演进路线中均需实现（先做）：

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 短信验证码 | 高 | 替换MVP测试码，接入真实短信服务 |
| 面试录音存储 | 高 | HR复听，争议处理依据 |
| 模拟面试 | 高 | 降低候选人首次使用门槛 |
| 批量候选人导入 | 中 | 企业大批量招聘场景 |
| 细粒度RBAC | 中 | 多HR协作时需要 |
| 数据看板 | 中 | HR决策支持 |
| 多方言ASR | 中 | 港口/物流场景方言较多 |
| 情绪分析 | 低 | 锦上添花，优先级低 |

---

## 14. 附录

### 14.1 术语定义

| 术语 | 解释 |
|------|------|
| ASR | 自动语音识别（Automatic Speech Recognition） |
| TTS | 文本转语音（Text-to-Speech） |
| OCR | 光学字符识别（Optical Character Recognition） |
| VAD | 语音活动检测（Voice Activity Detection），检测说话起止 |
| LangGraph | LangChain生态的AI工作流/状态机框架 |
| FunASR | 阿里达摩院开源ASR框架，已集成至阿里云百炼DashScope平台，支持中文方言 |
| CosyVoice | 阿里通义实验室TTS模型，`v3-flash` 为低延迟版本，集成至DashScope |
| DashScope | 阿里云AI大模型服务平台，统一提供FunASR/CosyVoice等模型API |
| LMMP | 中移香港大模型管理平台（Large Model Management Platform），托管Qwen3和Qwen2-VL |
| Qwen3-235B | 通义千问3代混合专家模型，235B参数，用于LLM推理 |
| Qwen2-VL-72B | 通义千问2代视觉语言模型，72B参数，用于证件图片理解（替代传统OCR） |
| Tauri | 基于Rust的轻量级跨平台桌面应用框架 |
| Sidecar | Tauri中与前端一同打包的后端可执行进程 |
| WAL | SQLite的Write-Ahead Logging模式，支持读写并发 |
| JWT | JSON Web Token，无状态认证令牌 |
| 启动系数 | 面试邀请触发阈值倍数，默认1.2（录取名额×1.2人触发面试） |
| 评分池 | 按综合材料得分对候选人排名的数据结构 |
| 得分点 | 题目中期望候选人提及的关键内容点 |

### 14.2 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| V1.0 | 2026-01-15 | 初始版本 |
| V2.0 | 2026-02-10 | 功能扩展 |
| V3.0 | 2026-03-15 | 流程优化 |
| V4.0 | 2026-03-25 | 全面升级，补充详细设计 |
| V5.0 | 2026-03-31 | 精简版，去除非直接相关章节 |
| V6.0 | 2026-04-05 | **重构版**：架构对齐MVP（Python+React+SQLite），新增两条演进路线图，剔除企业级过度设计；AI能力统一采用中移香港LMMP（Qwen3-235B/Qwen2-VL-72B）+ 阿里云百炼DashScope（FunASR/CosyVoice-v3-Flash） |
| V6.1 | 2026-04-06 | 新增第15章系统初始化数据：卡车司机岗位种子数据（3个岗位、30题题库含得分点与追问话术、资质校验规则、HR账号、系统参数） |

### 14.3 V5.0 → V6.0 主要变更对照

| 变更项 | V5.0 | V6.0 |
|--------|------|------|
| 架构 | 微服务 + API网关 + 多数据库 | 单体 FastAPI + SQLite |
| OCR | 百度OCR API | Qwen2-VL-72B 多模态理解（中移香港LMMP） |
| LLM | DeepSeek API | Qwen3-235B（中移香港LMMP私有化接口） |
| ASR | FunASR本地部署 | 阿里云百炼 DashScope FunASR API |
| TTS | Edge-TTS本地 | 阿里云百炼 DashScope CosyVoice-v3-Flash |
| 性能指标 | 万人并发，99.9% SLA | MVP：50并发，本地可靠运行 |
| 测试工具 | JUnit / JMeter（Java系） | pytest / httpx（Python系） |
| 项目计划 | 19周，13人团队 | 6周，1-2人+AI辅助 |
| 部署方式 | K8s容器集群 | 本地单进程 + systemd守护 |
| 演进路线 | 未定义 | Track A（客户端/Tauri）+ Track B（微信H5） |
| 权限系统 | 细粒度RBAC | MVP两级：admin/specialist |
| 短信验证 | 接入SMS服务 | MVP使用测试验证码 |

---

## 15. 系统初始化数据

本章定义系统首次部署时的种子数据，执行 `python scripts/init_seed_data.py` 即可自动写入 SQLite。所有数据以卡车司机招聘场景为基准设计，HR可在后台按需调整。

---

### 15.1 HR账号初始数据

| 字段 | 超级管理员 | HR专员示例 |
|------|-----------|----------|
| username | `admin` | `hr_zhang` |
| password | `Admin@2026`（首次登录强制修改） | `Hr@2026`（首次登录强制修改） |
| name | 系统管理员 | 张招聘 |
| role | `admin` | `specialist` |
| is_active | 1 | 1 |

> **安全提示**：初始密码仅用于首次登录，系统应在登录后强制跳转修改密码页面。

---

### 15.2 岗位初始数据

设计3个卡车司机细分岗位，覆盖港口物流最常见的招聘场景。

#### 岗位1：集装箱拖车司机（干线）

```json
{
  "name": "集装箱拖车司机（干线）",
  "description": "负责港口与内陆堆场/客户仓库之间的集装箱运输，驾驶半挂牵引车，单程距离50-300公里。",
  "requirements": "1. 持有A1或A2驾驶证，准驾车型含牵引车\n2. 持有道路运输从业资格证\n3. 3年以上大型货车驾驶经验\n4. 无重大交通违章记录（近3年）\n5. 能接受不规律出车时间",
  "quota": 10,
  "start_coefficient": 1.2,
  "min_interview_count": 5,
  "required_license_type": ["A1", "A2"],
  "required_certs": ["道路运输从业资格证"],
  "status": 1
}
```

#### 岗位2：港区内拖司机（短驳）

```json
{
  "name": "港区内拖司机（短驳）",
  "description": "在港口堆场内部及近港区域短距离驳运集装箱，驾驶港口专用内拖车，单程距离5公里以内，频次高。",
  "requirements": "1. 持有A2或B2驾驶证，准驾车型含大型货车\n2. 持有道路运输从业资格证\n3. 1年以上货车驾驶经验\n4. 熟悉港口作业流程者优先\n5. 能适应轮班作业（含夜班）",
  "quota": 20,
  "start_coefficient": 1.3,
  "min_interview_count": 8,
  "required_license_type": ["A2", "B2"],
  "required_certs": ["道路运输从业资格证"],
  "status": 1
}
```

#### 岗位3：危险品运输司机

```json
{
  "name": "危险品运输司机",
  "description": "负责港口进出口危险货物（化工品、易燃液体等）的公路运输，需持有危险货物运输资格，严格遵守危货运输规程。",
  "requirements": "1. 持有A1或A2驾驶证，准驾车型含牵引车\n2. 持有道路运输从业资格证\n3. 持有危险货物道路运输驾驶员证\n4. 5年以上大型货车驾驶经验\n5. 熟悉危货应急处置流程\n6. 近5年无重大交通事故记录",
  "quota": 5,
  "start_coefficient": 1.5,
  "min_interview_count": 5,
  "required_license_type": ["A1", "A2"],
  "required_certs": ["道路运输从业资格证", "危险货物道路运输驾驶员证"],
  "status": 1
}
```

---

### 15.3 资质审核规则配置

#### 15.3.1 通用规则（所有司机岗位）

| 规则ID | 规则名称 | 校验逻辑 | 不通过处理 |
|--------|---------|---------|-----------|
| R-01 | 身份证有效期 | 身份证到期日 > 今日 | 一票否决，提示更新证件 |
| R-02 | 驾驶证有效期 | 驾驶证到期日距今 > 30天 | 一票否决，提示续证 |
| R-03 | 驾驶证状态 | OCR识别"状态"字段不含"注销/扣留/吊销" | 一票否决 |
| R-04 | 从业资格证有效期 | 从业资格证到期日 > 今日 | 一票否决 |
| R-05 | 准驾车型匹配 | 驾驶证准驾车型 ∩ 岗位要求车型 ≠ 空集 | 一票否决，提示车型不符 |
| R-06 | 年龄限制 | 18岁 ≤ 候选人年龄 ≤ 60岁 | 一票否决 |

#### 15.3.2 危险品岗位追加规则

| 规则ID | 规则名称 | 校验逻辑 | 不通过处理 |
|--------|---------|---------|-----------|
| R-07 | 危险货物驾驶员证 | 必须上传且在有效期内 | 一票否决 |
| R-08 | 危驾证范围匹配 | 危驾证允许运输类别覆盖岗位要求类别 | 一票否决 |
| R-09 | 驾龄要求 | work_experience ≥ 5年 | 一票否决 |

#### 15.3.3 综合评分权重

| 评分维度 | 权重 | 计算方式 |
|---------|------|---------|
| 基础资质完整度 | 40% | 必备证件全部通过规则校验得满分；缺1项扣20分 |
| 驾龄经验 | 25% | 经验年限/岗位要求年限×100，上限100分 |
| 附加证件加分 | 20% | 每额外提供1项有效证件（行驶证/道路运输证/体检证明）+10分，上限40分 |
| 驾驶证准驾类型 | 15% | A1=100，A2=85，B2=70，其他=50 |

---

### 15.4 面试题库初始数据

题库按岗位分类，共3大类：**基础安全类**（所有岗位通用）、**港口作业类**（港区专用）、**危险品类**（危货岗位专用）。

每题包含：题目内容、考核关键点（`score_points`）、追问话术（`follow_up_scripts`）。

---

#### 15.4.1 基础安全类题目（10题，通用）

---

**Q-001｜行车前安全检查**

```json
{
  "job_id": null,
  "content": "师傅，您好！请问您每次出车前，都会对车辆做哪些安全检查？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "检查轮胎气压和磨损情况",
    "检查刹车系统（制动液/刹车片/气压）",
    "检查灯光（大灯/转向灯/刹车灯）",
    "检查后视镜角度和清洁度",
    "检查燃油/尿素液液位",
    "检查随车证件是否齐全（驾驶证/行驶证/从业资格证）"
  ],
  "follow_up_scripts": [
    "您刚才说了轮胎和灯光，那刹车系统您平时怎么检查呢？",
    "检查完车辆之后，出发前您还会确认哪些证件和文件吗？",
    "如果发现轮胎气压不足，您一般怎么处理？"
  ]
}
```

---

**Q-002｜恶劣天气行车**

```json
{
  "content": "遇到大雾或暴雨天气，您在驾驶重型货车时会采取哪些应对措施？",
  "type": 1,
  "difficulty": 2,
  "score_points": [
    "降低车速，保持比平时更长的跟车距离",
    "开启雾灯和危险警示灯（双闪）",
    "避免急刹车，提前预判减速",
    "能见度极低时靠边停车等待",
    "通过广播或导航了解路况信息",
    "通知调度说明情况，避免强行赶路"
  ],
  "follow_up_scripts": [
    "能见度不到50米的时候，您会怎么做？",
    "遇到大雾强行赶路会有什么风险，您怎么看？",
    "您遇到过最恶劣的天气是什么情况，当时您是怎么处理的？"
  ]
}
```

---

**Q-003｜疲劳驾驶处理**

```json
{
  "content": "如果在长途运输途中您感到疲劳、困倦，您会怎么做？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "找安全地点靠边停车休息，不强撑",
    "下车活动，不在驾驶室内打盹",
    "联系调度报告情况",
    "休息至少20-30分钟再出发",
    "不靠咖啡或药物强行驾驶",
    "连续驾驶不超过4小时必须休息"
  ],
  "follow_up_scripts": [
    "如果任务紧急，货主催促您赶路，您会怎么做？",
    "您知道规定连续驾驶多少小时必须休息吗？",
    "您平时有什么预防疲劳驾驶的好习惯吗？"
  ]
}
```

---

**Q-004｜超载处理**

```json
{
  "content": "如果装货时您发现货物重量超过了车辆核定载重，您会怎么处理？",
  "type": 1,
  "difficulty": 2,
  "score_points": [
    "拒绝超载出车，不以任何理由妥协",
    "立即告知货主或装货负责人",
    "联系公司调度反映情况",
    "要求卸下超出部分的货物",
    "说明超载的法律责任和安全风险"
  ],
  "follow_up_scripts": [
    "如果货主说只超了一点点，给您额外补贴，您会开吗？",
    "超载会有哪些具体的安全风险，您能说说吗？",
    "您之前遇到过这种情况吗？当时是怎么处理的？"
  ]
}
```

---

**Q-005｜交通事故处置**

```json
{
  "content": "如果您在运输途中发生了轻微的追尾事故，您的处置步骤是什么？",
  "type": 3,
  "difficulty": 2,
  "score_points": [
    "立即开启双闪，在车后方设置警示三角牌",
    "确认人员是否受伤，如有伤者立即拨打120",
    "拨打122报警或使用快处快赔流程",
    "拍照记录现场（车辆损伤、位置、路面情况）",
    "联系公司调度和保险公司",
    "不擅自移动车辆（特殊情况除外）"
  ],
  "follow_up_scripts": [
    "设置警示三角牌时，您知道应该放在车后多远的位置吗？",
    "如果对方坚持私了不报警，您会怎么做？",
    "事故处理完成后，您还需要做哪些后续工作？"
  ]
}
```

---

**Q-006｜车辆故障处置**

```json
{
  "content": "行驶途中车辆突然出现刹车失灵的情况，您会怎么应对？",
  "type": 3,
  "difficulty": 3,
  "score_points": [
    "保持冷静，不慌乱",
    "迅速踩下离合，换低挡利用发动机制动",
    "拉手刹进行辅助制动（非急速操作）",
    "开双闪，鸣喇叭示警",
    "利用路边护栏、沙堆等地形减速",
    "避开人群密集区域，寻找开阔地带停车"
  ],
  "follow_up_scripts": [
    "您说换低挡，能具体说说怎么操作吗？",
    "如果前方是下坡路，您会怎么利用地形？",
    "平时怎么保养刹车系统来预防这类情况发生？"
  ]
}
```

---

**Q-007｜违规行为态度**

```json
{
  "content": "您对酒后驾车和疲劳驾驶是什么态度？公司规定绝对不允许，您能做到吗？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "明确表示坚决不酒驾，无论任何理由",
    "了解酒驾的法律后果（吊销/拘留/刑责）",
    "对疲劳驾驶同样零容忍",
    "即使聚餐喝酒也不开车，会找代驾或休息"
  ],
  "follow_up_scripts": [
    "如果朋友聚会喝了一点点，您觉得开车没问题吗？",
    "您知道饮酒驾车和醉酒驾车在法律上有什么区别吗？",
    "您家人对您开车这份工作有什么看法？"
  ]
}
```

---

**Q-008｜货物损坏处理**

```json
{
  "content": "运输途中如果发现货物受损，您会怎么处理？",
  "type": 3,
  "difficulty": 2,
  "score_points": [
    "立即停车查看情况",
    "拍照留存损坏证据",
    "第一时间通知调度和货主",
    "填写货损记录单，记录时间地点情况",
    "不擅自丢弃或处理受损货物",
    "配合后续理赔流程"
  ],
  "follow_up_scripts": [
    "如果货物损坏不严重，您觉得可以不上报吗？",
    "货物受损通常是什么原因造成的，您有什么预防经验？",
    "理赔流程您了解吗？"
  ]
}
```

---

**Q-009｜路线规划与导航**

```json
{
  "content": "接到一个新的运输任务，目的地您没去过，您会怎么规划路线？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "使用导航软件提前规划，选货车专用路线",
    "查看是否有限高/限重/禁行路段",
    "了解沿途服务区和停车场位置",
    "出发前告知调度预计路线",
    "行驶中关注路况变化，必要时重新规划"
  ],
  "follow_up_scripts": [
    "您平时用什么导航软件？货车模式和普通模式有什么区别？",
    "遇到限高杆您怎么判断能不能通过？",
    "如果导航引导您走了限行路段怎么办？"
  ]
}
```

---

**Q-010｜沟通与服务意识**

```json
{
  "content": "送货时货主对交货时间不满意，情绪比较激动，您会怎么应对？",
  "type": 3,
  "difficulty": 2,
  "score_points": [
    "保持冷静，不与货主发生口角",
    "耐心倾听，先致歉稳定对方情绪",
    "如实说明延误原因（堵车/天气等客观因素）",
    "联系调度请求支持",
    "做好记录，反馈公司"
  ],
  "follow_up_scripts": [
    "如果对方态度非常蛮横，辱骂您，您会怎么做？",
    "您觉得在这份工作中，沟通能力重不重要？为什么？",
    "您有没有处理过类似的棘手情况，能举个例子吗？"
  ]
}
```

---

#### 15.4.2 港口作业类题目（12题，港区岗位专用）

---

**Q-101｜港区交通规则**

```json
{
  "content": "在港区内行驶，和公路上有哪些不一样的交通规则需要特别注意？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "港区限速通常10-20km/h，严格遵守",
    "在装卸作业区域必须服从指挥人员指挥",
    "龙门吊/桥吊作业半径内禁止停车和穿行",
    "铁路道口必须停车确认后通过",
    "倒车必须有专人引导（特别是集装箱区域）",
    "遇到叉车和内拖有路权优先规则需了解"
  ],
  "follow_up_scripts": [
    "您有在港区工作或者进出港区的经验吗？",
    "遇到桥吊在作业，您会怎么判断什么时候可以通过？",
    "港区为什么要限速这么低，您怎么理解这个规定？"
  ]
}
```

---

**Q-102｜集装箱交接流程**

```json
{
  "content": "请描述一下您到港口提箱的完整流程，从进港到离港，您会经历哪些步骤？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "进港前准备好提货单/箱号/封条信息",
    "在港门刷卡/扫码验证身份和证件",
    "按指示前往指定堆场等候指挥",
    "配合龙门吊/正面吊完成装箱作业",
    "核对箱号、封条完好性",
    "领取放行单，完成港门出闸手续"
  ],
  "follow_up_scripts": [
    "如果箱号对不上或者封条破损，您会怎么处理？",
    "您有没有遇到过提箱时等待时间很长的情况，您是怎么应对的？",
    "港区提箱时需要提前预约吗？您了解这个流程吗？"
  ]
}
```

---

**Q-103｜集装箱检查**

```json
{
  "content": "提到集装箱之后，您会对集装箱做哪些检查，才算可以安全上路？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "检查箱体外观有无明显破损、变形",
    "确认箱门封条完好，铅封号与单据一致",
    "检查集装箱锁具是否锁好",
    "确认集装箱在底盘上固定到位（锁销锁定）",
    "检查超出限高的风险（空集装箱高度）",
    "核对箱号与提货单一致"
  ],
  "follow_up_scripts": [
    "如果发现封条号码对不上，您会直接开车走吗？",
    "集装箱锁销没有锁好上路会有什么危险？",
    "您了解不同类型集装箱（冷藏箱/罐箱）有没有特殊注意事项？"
  ]
}
```

---

**Q-104｜夜间港区作业**

```json
{
  "content": "港区经常有夜间作业，您在夜间驾驶内拖或拖车时有哪些特别注意的事项？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "确保车辆所有灯光正常工作",
    "降低车速，视线不佳时更加谨慎",
    "特别注意徒步工人和信号灯指挥",
    "保持清醒，如困倦及时休息再作业",
    "经过照明盲区时减速鸣号",
    "与作业机械保持更大安全距离"
  ],
  "follow_up_scripts": [
    "您接受夜班或者轮班作业吗？",
    "夜间视线差，您怎么保证准确停靠到指定位置？",
    "您有丰富的夜间港区作业经验吗？"
  ]
}
```

---

**Q-105｜异常箱情况处理**

```json
{
  "content": "您在运输途中发现集装箱有异味，或者外箱有液体渗漏，您会怎么做？",
  "type": 3,
  "difficulty": 3,
  "score_points": [
    "立即靠边停车，不继续行驶",
    "人员远离车辆，在上风向等待",
    "联系调度报告情况",
    "拨打119/110请求支援（如有危险品风险）",
    "不擅自打开箱门查看",
    "等待专业人员处置"
  ],
  "follow_up_scripts": [
    "如果货主催您继续赶路，您怎么办？",
    "您怎么判断这个集装箱里可能装了危险品？",
    "这种情况您有没有遇到过，当时是怎么做的？"
  ]
}
```

---

**Q-106｜限高限宽通行**

```json
{
  "content": "您驾驶满载集装箱的拖车，遇到前方有限高4.5米的涵洞或立交桥，您的车高是4.2米，您会怎么判断和处理？",
  "type": 3,
  "difficulty": 2,
  "score_points": [
    "4.5米限高，车高4.2米，理论上可以通过",
    "但要考虑道路是否平整（颠簸会增加实际高度）",
    "低速缓慢通过，有人员在旁观察",
    "如有顾虑，宁可绕行不冒险",
    "绕行前重新规划路线并告知调度"
  ],
  "follow_up_scripts": [
    "限高标志上的高度是净高还是含路面厚度的？您知道吗？",
    "您的车辆具体高度，您清楚吗？怎么获取这个数据？",
    "如果硬通结果剐蹭了，责任怎么算？"
  ]
}
```

---

**Q-107｜与港区机械设备配合**

```json
{
  "content": "龙门吊要往您车上吊放集装箱，您在等待和配合过程中需要注意什么？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "按指挥员指示停到指定位置",
    "停车后下车离开驾驶室，站到安全区域",
    "不在集装箱正下方站立",
    "等龙门吊发出信号才能重新上车",
    "落箱后确认锁销是否正确锁定",
    "服从指挥员的所有指令"
  ],
  "follow_up_scripts": [
    "为什么落箱时司机必须离开驾驶室？",
    "如果龙门吊操作手让您往前挪一点，您怎么做？",
    "您了解龙门吊的作业信号有哪些吗？"
  ]
}
```

---

**Q-108｜超载超限管理**

```json
{
  "content": "您的集装箱拖车满载，在过地磅时发现重量超出了车辆核定载重，这时候您会怎么处理？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "不得继续出港，停在等待区",
    "立即联系调度和货主报告情况",
    "等待货主安排分拆货物或换车",
    "绝对不贿赂或绕行过磅",
    "配合港口工作人员处理"
  ],
  "follow_up_scripts": [
    "超载最高会被罚多少钱，您知道吗？",
    "如果调度让您走，说后面再说，您会走吗？",
    "超载对车辆和道路有什么危害？"
  ]
}
```

---

**Q-109｜轮班和出勤安排**

```json
{
  "content": "港区作业通常需要轮班，包括夜班和节假日值班，您对这种工作安排能接受吗？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "明确表示能接受轮班制度",
    "了解并接受节假日可能需要出勤",
    "家庭方面已做好协调或没有障碍",
    "了解倒班对身体的影响并有应对方法"
  ],
  "follow_up_scripts": [
    "您家里有没有需要照顾的老人或小孩，会影响上夜班吗？",
    "夜班津贴和节假日工资的标准，您有了解过我们公司的规定吗？",
    "您之前的工作是什么排班方式？"
  ]
}
```

---

**Q-110｜码头堵车等待**

```json
{
  "content": "港区高峰期排队等候提箱可能要等3-4个小时，您遇到这种情况一般怎么打发时间，怎么保持状态？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "在车内休息，为后续驾驶养精蓄锐",
    "不离开车辆太远，随时准备轮到自己",
    "联系调度汇报等候情况",
    "保持耐心，不因久等产生急躁情绪",
    "利用等待时间检查车辆状态"
  ],
  "follow_up_scripts": [
    "您等待时会玩手机看短视频吗？会不会影响您轮到时候的反应？",
    "长时间等待后继续上路，您有没有疲劳驾驶的顾虑？怎么应对？",
    "您有没有提前预约提箱时间的习惯？"
  ]
}
```

---

**Q-111｜信息化系统使用**

```json
{
  "content": "现在很多港口都用APP或者智能终端来接单和提交回单，您会使用这些系统吗？",
  "type": 1,
  "difficulty": 1,
  "score_points": [
    "会使用智能手机的基本功能",
    "能学习和使用公司指定的调度APP",
    "会拍照上传回单、签收单",
    "遇到系统问题知道联系谁处理"
  ],
  "follow_up_scripts": [
    "您现在用的什么手机，用过哪些货运或导航APP？",
    "如果APP出了问题，您会怎么办？",
    "您学新系统的速度怎么样？举个例子说说。"
  ]
}
```

---

**Q-112｜集装箱号识别**

```json
{
  "content": "您能解释一下集装箱箱号的格式吗？比如看到"CSNU1234567"，您能读懂它包含哪些信息？",
  "type": 2,
  "difficulty": 3,
  "score_points": [
    "前3位字母是船公司代码（如CSN=中远海运）",
    "第4位字母固定为U代表货运集装箱",
    "后6位是序列号",
    "最后1位是校验码",
    "能用校验码验证箱号是否正确"
  ],
  "follow_up_scripts": [
    "如果箱号里面有字母O，您怎么判断是字母O还是数字0？",
    "实际工作中您是怎么核对箱号准确性的？",
    "您了解不同集装箱类型的标识，比如冷藏箱和普通箱在箱号上有区别吗？"
  ]
}
```

---

#### 15.4.3 危险品运输类题目（8题，危货岗位专用）

---

**Q-201｜危险品分类**

```json
{
  "content": "道路危险货物运输规定将危险品分为9大类，您能说出几类，并举例说说各是什么？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "第1类：爆炸品（炸药、烟花）",
    "第2类：气体（液化石油气、压缩天然气）",
    "第3类：易燃液体（汽油、乙醇）",
    "第4类：易燃固体（赤磷、硫黄）",
    "第5类：氧化性物质和有机过氧化物",
    "第6类：毒性物质和感染性物质",
    "第8类：腐蚀性物质（硫酸、盐酸）",
    "第9类：杂项危险物质"
  ],
  "follow_up_scripts": [
    "您运输过哪几类危险品？印象最深的是哪次？",
    "第3类易燃液体和第2类气体在运输要求上有什么主要区别？",
    "如果不确定货物属于哪类危险品，您会怎么查询确认？"
  ]
}
```

---

**Q-202｜危货运输证件**

```json
{
  "content": "运输危险品出发前，您需要携带哪些必备文件和证件？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "驾驶员危险货物运输从业资格证",
    "押运员证（需配备押运员时）",
    "危险货物运单/货物清单",
    "道路运输证（车辆专用危货经营许可）",
    "应急救援卡/应急处置指南",
    "车辆危险货物标志牌（菱形标志）"
  ],
  "follow_up_scripts": [
    "危险货物标志牌应该贴在车辆的哪些位置？",
    "如果路上被交警查，发现押运员证过期了，会有什么后果？",
    "应急救援卡上主要包含什么信息，您用过吗？"
  ]
}
```

---

**Q-203｜危货装载要求**

```json
{
  "content": "运输危险化学品时，对货物的装载有哪些特殊要求？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "危险品包装必须完好，标签标识清晰",
    "不同类别危险品不得混装（有配装禁忌的）",
    "货物必须固定牢固，防止滑移碰撞",
    "易燃液体须用专用罐车运输",
    "装载完成后关好车厢，防止泄漏扩散",
    "远离火源和热源"
  ],
  "follow_up_scripts": [
    "您知道哪两类危险品绝对不能同车运输吗？举例说明。",
    "货物固定不好在行驶中发生碰撞，可能造成什么后果？",
    "危险品包装如果破损，您会怎么处理？"
  ]
}
```

---

**Q-204｜危货泄漏应急处置**

```json
{
  "content": "运输途中发现罐体有液体泄漏，您的应急处置步骤是什么？",
  "type": 3,
  "difficulty": 3,
  "score_points": [
    "立即靠边停车，熄火，禁止烟火",
    "在上风向疏散人员，隔离危险区域",
    "查看应急救援卡确认物质特性",
    "拨打119（消防）和120（急救）",
    "联系公司和货主",
    "不擅自处置，等待专业力量",
    "向现场警察/消防说明货物种类和数量"
  ],
  "follow_up_scripts": [
    "为什么要在上风向等待，能解释一下吗？",
    "如果泄漏物质是酸性腐蚀品，有人皮肤接触了，现场应急怎么做？",
    "您接受过危险品应急演练吗？频率是多久一次？"
  ]
}
```

---

**Q-205｜危货禁行路线**

```json
{
  "content": "运输危险品时，对行驶路线有哪些限制，您如何确保合规行驶？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "必须按审批的路线行驶，不擅自更改",
    "避开居民区、学校、医院等人员密集区域",
    "遵守危货车辆禁行时段规定",
    "过隧道前确认是否允许危货通行",
    "出发前向当地交管部门申请运输路线许可"
  ],
  "follow_up_scripts": [
    "如果审批路线因施工堵死了，您会怎么处理？",
    "您知道我们这边危货车辆的禁行时段吗？",
    "过某些隧道为什么要特别申请，您了解其中原因吗？"
  ]
}
```

---

**Q-206｜危货停车要求**

```json
{
  "content": "运输危险货物途中需要休息停车，对停车地点有哪些要求？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "不得在居民区、学校、市场等人员密集处停车",
    "不得在隧道、桥梁等限制区域停车",
    "应选择有危货停车标志的服务区或专用停车场",
    "停车时不得离开车辆太久，需要有人值守",
    "停车后检查货物状态确认无异常",
    "短暂休息后出发前重新检查车辆"
  ],
  "follow_up_scripts": [
    "如果找不到专用停车场，您会怎么选择停车地点？",
    "夜间停车需要特别注意什么吗？",
    "押运员和司机能同时离开车辆去吃饭吗？"
  ]
}
```

---

**Q-207｜危货事故报告义务**

```json
{
  "content": "在运输危险品过程中发生了事故，您有哪些必须履行的报告义务？",
  "type": 2,
  "difficulty": 2,
  "score_points": [
    "立即拨打110、119、120（视情况）",
    "第一时间向公司/调度报告",
    "向当地安监/应急管理部门报告",
    "如实提供货物种类、数量、危险特性信息",
    "保护现场，配合调查",
    "在规定时间内提交书面事故报告"
  ],
  "follow_up_scripts": [
    "如果你怕担责任，能不能先不上报，等看看情况再说？",
    "向应急管理部门报告和向公司报告，哪个更紧迫？",
    "隐瞒危货事故会有什么法律后果，您了解吗？"
  ]
}
```

---

**Q-208｜危货心理素质**

```json
{
  "content": "危险品运输压力比普通货运大，您觉得自己适合这份工作吗？您如何看待这份职业的风险？",
  "type": 1,
  "difficulty": 2,
  "score_points": [
    "正视风险，不回避，认为可以通过规范操作控制风险",
    "对规章制度有敬畏之心",
    "心理素质稳定，不因压力产生过激行为",
    "有家庭支持或已做好心理准备",
    "了解危货司机的薪资和职业发展"
  ],
  "follow_up_scripts": [
    "您家人支持您从事危货运输工作吗？",
    "您觉得危货司机最大的职业挑战是什么？",
    "您有没有考虑过如果发生严重事故的后果？"
  ]
}
```

---

### 15.5 系统参数初始配置

```json
{
  "system_settings": {
    "interview": {
      "max_daily_interviews": 3,
      "max_follow_up_per_question": 2,
      "answer_timeout_seconds": 30,
      "resume_window_hours": 24,
      "silence_hint_text": "师傅，没听到您的回答，请稍后我们进入下一题。",
      "fallback_hint_text": "师傅您好，刚刚没听清楚，能麻烦您再说一遍吗？",
      "replay_keywords": ["没听清", "再说一遍", "重复一下", "啥", "什么"]
    },
    "tts": {
      "voice": "longxiaochun",
      "speech_rate": 0.9,
      "intro_text": "您好师傅，欢迎参加我们公司的AI面试。本次面试共有{question_count}道题目，请用普通话回答。每道题目我会语音播报，如果没有听清楚，您可以说"再说一遍"，我会重新播报。准备好了吗？我们开始吧。"
    },
    "scoring": {
      "doc_score_weights": {
        "base_qualification": 0.40,
        "work_experience": 0.25,
        "extra_certs": 0.20,
        "license_type": 0.15
      },
      "interview_pass_threshold": 60,
      "experience_full_score_years": {
        "集装箱拖车司机（干线）": 5,
        "港区内拖司机（短驳）": 2,
        "危险品运输司机": 8
      }
    },
    "notification": {
      "invite_sms_template": "【AI面试】尊敬的{name}师傅，您已通过资质初筛，请点击链接参加{job_name}岗位的AI面试：{link}，有效期48小时。",
      "result_sms_template": "【AI面试】{name}师傅，您的面试结果已出，得分{score}分，请登录系统查看详细评估报告。"
    }
  }
}
```

---

### 15.6 初始化脚本说明

系统提供 `scripts/init_seed_data.py`，执行后完成以下初始化：

```
初始化顺序：
1. HR账号        → 创建 admin + hr_zhang 两个账号
2. 岗位数据      → 创建3个卡车司机岗位
3. 资质规则配置  → 写入 system_settings 表的 qualification_rules
4. 题库数据      → 写入30题（基础安全10题 + 港口作业12题 + 危货8题）
5. 岗位题目关联  → 按题型关联到对应岗位
6. 系统参数      → 写入 system_settings 表
```

```bash
# 执行初始化（幂等，重复执行不会产生重复数据）
python scripts/init_seed_data.py

# 输出示例：
# ✅ HR账号初始化完成（2个）
# ✅ 岗位初始化完成（3个）
# ✅ 题库初始化完成（30题）
#    - 基础安全类：10题（关联所有岗位）
#    - 港口作业类：12题（关联港区内拖、集装箱拖车）
#    - 危险品类：8题（关联危险品运输岗位）
# ✅ 系统参数初始化完成
# 🎉 初始化完成，系统可正常使用
```

#### 题目与岗位关联关系

| 题目范围 | 集装箱拖车司机 | 港区内拖司机 | 危险品运输司机 |
|---------|:------------:|:-----------:|:------------:|
| Q-001 ~ Q-010（基础安全） | ✅ | ✅ | ✅ |
| Q-101 ~ Q-112（港口作业） | ✅ | ✅ | ✅ |
| Q-201 ~ Q-208（危险品） | ❌ | ❌ | ✅ |

> **面试出题策略（MVP）**：每次面试从关联题库中随机抽取5题，基础安全类必抽2题，专业类抽3题。危货岗位危险品类至少抽2题。

---

### 15.7 Vision OCR 证件识别 Prompt 模板

系统调用 Qwen2-VL-72B 识别证件时使用以下标准 Prompt，确保返回结构化 JSON。

#### 身份证识别 Prompt

```
你是一个证件信息提取助手。请从图片中提取中国居民身份证的信息，严格按照JSON格式返回，不要输出任何其他内容。

返回格式：
{
  "id_type": "identity_card",
  "name": "姓名",
  "id_number": "18位身份证号",
  "gender": "男/女",
  "nationality": "民族",
  "birth_date": "YYYY-MM-DD",
  "address": "住址",
  "expire_date": "YYYY-MM-DD（长期则填2099-12-31）",
  "issue_authority": "签发机关",
  "confidence": 0.95
}

如果图片模糊或字段无法识别，对应字段填null，confidence填对应降低值。
```

#### 驾驶证识别 Prompt

```
你是一个证件信息提取助手。请从图片中提取中国机动车驾驶证的信息，严格按照JSON格式返回，不要输出任何其他内容。

返回格式：
{
  "id_type": "driving_license",
  "name": "姓名",
  "id_number": "身份证号",
  "license_number": "驾驶证档案编号",
  "vehicle_types": ["A1", "A2"],
  "issue_date": "YYYY-MM-DD",
  "expire_date": "YYYY-MM-DD",
  "status": "正常/注销/吊销/扣留",
  "address": "住址",
  "issuing_authority": "发证机关",
  "confidence": 0.95
}
```

#### 从业资格证识别 Prompt

```
你是一个证件信息提取助手。请从图片中提取道路运输从业资格证的信息，严格按照JSON格式返回，不要输出任何其他内容。

返回格式：
{
  "id_type": "transport_qualification",
  "name": "姓名",
  "cert_number": "证件编号",
  "cert_type": "道路运输从业资格证/危险货物道路运输驾驶员证/押运员证",
  "business_scope": "资质范围描述",
  "issue_date": "YYYY-MM-DD",
  "expire_date": "YYYY-MM-DD",
  "issuing_authority": "发证机关",
  "confidence": 0.95
}
```

> **使用说明**：以上 Prompt 存储于 `app/services/ocr_prompts.py`，Vision OCR Service 根据上传文件的 `type` 字段自动选择对应 Prompt。`confidence` 字段低于 0.7 时，系统标记为"需人工核对"，候选人端显示核对提示。
