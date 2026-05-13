# 法律咨询辅助 Multi-Agent 系统技术设计文档

## 1. 项目定位

本系统是一个面向普通用户的法律咨询辅助系统。首版聚焦**劳动争议场景**，围绕“用户描述纠纷 -> 系统追问补全信息 -> 检索法规和类案 -> 分析证据与时效 -> 生成处理建议和仲裁申请书初稿”的闭环来设计。

系统定位为“法律辅助决策系统”，不定位为“AI 律师”或“自动裁判系统”。系统输出只作为参考信息，法律分析、文书初稿和处理策略均需要用户或专业法律人士复核。

## 2. 首版推荐功能

首版只实现劳动争议方向，覆盖以下问题：

| 场景 | 支持问题 | 输出 |
|---|---|---|
| 拖欠工资 | 公司未支付工资、拖欠离职工资 | 仲裁路径、证据清单、风险提示 |
| 未签劳动合同 | 入职后未签书面劳动合同 | 事实要素、所需证据、可能请求 |
| 违法解除 | 被辞退、被迫离职、无赔偿 | 争议焦点、证据缺口、处理路径 |
| 加班费争议 | 加班未支付加班费 | 举证要点、证据清单、风险说明 |
| 离职证明 | 公司拒绝开具离职证明 | 处理建议、材料准备 |

首版核心功能：

1. **自然语言咨询**：用户描述劳动争议，系统给出结构化分析。
2. **案情采集与追问**：抽取入职时间、离职时间、工资标准、合同情况、社保情况、辞退方式、证据材料等。
3. **劳动争议案由识别**：识别追索劳动报酬、劳动合同纠纷、违法解除、未签合同等方向。
4. **法规检索**：基于 BM25 和 Milvus 混合检索劳动法律法规。
5. **类案检索**：检索劳动争议相似案例，辅助判断争议焦点和证据要求。
6. **证据分析**：分析劳动合同、工资流水、考勤记录、聊天记录、辞退通知等证据。
7. **时效提醒**：识别劳动仲裁时效风险和关键日期缺口。
8. **争议焦点分析**：生成待证明事实、举证责任和证据缺口。
9. **处理路径规划**：生成协商、投诉、劳动仲裁等步骤建议。
10. **仲裁申请书初稿**：生成 Markdown 格式的劳动仲裁申请书初稿。
11. **法律档案候选项**：抽取案件时间线、证据清单、待办事项，用户确认后写入档案。
12. **合规安全审核**：所有输出经过安全审核，避免虚构法条、虚构案例和确定性承诺。

## 3. 确定技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、Axios、TanStack Query、markdown-it、PDF.js |
| 服务端 | Python 3.11+、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、PyMySQL、Uvicorn |
| 算法端 | Python 3.11+、FastAPI、Pydantic v2、LangGraph、pymilvus、PyMuPDF、python-docx、PaddleOCR |
| 业务数据库 | MySQL |
| 向量数据库 | Milvus |
| 关键词检索 | BM25 |
| 模型接入 | OpenAI-compatible Chat / Embeddings / Rerank API |
| 缓存与会话状态 | Redis |
| 消息队列 | RabbitMQ |
| 异步处理 | Python async / await、asyncio Worker、RabbitMQ 消费者 |
| 文件存储 | MinIO |
| 日志与监控 | structlog、OpenTelemetry、Prometheus、Grafana |

## 4. 总体架构

系统采用前端、服务端、算法端三层架构。

```text
Vue3 前端
  -> FastAPI 服务端
     -> 用户认证
     -> 案件管理
     -> 证据管理
     -> 档案确认
     -> 文书保存
     -> 任务状态

  -> FastAPI 算法端
     -> LangGraph Agent DAG
     -> 内部数据访问层
     -> 必要 MCP 工具
     -> BM25 检索
     -> Milvus 检索
     -> Reranker 重排序
     -> 模型网关
     -> OCR / 文档解析
     -> 安全审核

  -> 基础设施
     -> MySQL
     -> Milvus
     -> BM25 倒排索引
     -> Redis
     -> RabbitMQ
     -> MinIO
```

服务端只处理业务态逻辑，不直接调用大模型。算法端只处理模型态逻辑，不保存长期用户业务数据。

## 5. 服务交互流程

### 5.1 在线咨询流程

```text
用户输入劳动争议描述
  -> 前端调用服务端 /api/chat/stream
  -> 服务端鉴权、校验 case_id、保存用户消息
  -> 服务端调用算法端 /internal/agent/analyze
  -> 算法端执行 Agent DAG
  -> 算法端通过内部数据访问层读取法规、类案、证据、档案和模型网关
  -> 算法端返回结构化结果
  -> 服务端保存分析结果和档案候选项
  -> 服务端通过 SSE 返回前端
```

### 5.2 文件分析流程

```text
用户上传证据文件
  -> 服务端写入 MinIO
  -> 服务端创建 evidence_items 记录
  -> 服务端将解析任务写入 RabbitMQ
  -> 算法端 Worker 消费任务
  -> 算法端执行 OCR / 文档解析 / 证据文本抽取
  -> 算法端返回抽取文本和证据分析结果
  -> 服务端更新 MySQL
```

### 5.3 文书生成流程

```text
用户请求生成劳动仲裁申请书
  -> 服务端读取案件结构化数据
  -> 服务端调用算法端 /internal/documents/generate
  -> 算法端检查必要字段
  -> 算法端调用内部法规检索能力
  -> 文书生成 Agent 生成 Markdown 初稿
  -> 安全审核 Agent 审核文书
  -> 服务端保存文书初稿
```

## 6. Agent 工具与 MCP 设计

Agent 运行在算法端，可以通过代码直接访问 MySQL、Milvus、BM25 索引、Redis、MinIO 和模型网关。数据库查询、向量检索、关键词检索、模板读取、档案读写、证据读取、时效计算、安全审核和审计日志都属于系统内部能力，不需要包装成 MCP 工具。

MCP 只用于首版中确实需要标准化工具协议、且可能由独立服务或第三方能力提供的工具。

### 6.1 内部能力清单

| 能力 | 调用方 | 说明 |
|---|---|---|
| `CaseRepository` | 案情采集 Agent、档案 Agent | 读取案件摘要、事实、证据、时间线，保存档案候选项 |
| `EvidenceRepository` | 证据分析 Agent、争议焦点 Agent | 读取证据元数据和证据解析文本 |
| `LaborLawRetriever` | 法规检索 Agent | 访问 BM25 和 Milvus，检索劳动法规 |
| `LaborPrecedentRetriever` | 类案检索 Agent | 访问 BM25 和 Milvus，检索劳动类案 |
| `RerankerClient` | 法规检索 Agent、类案检索 Agent | 对候选依据重排序 |
| `LaborDeadlineService` | 时效 Agent | 计算劳动仲裁时效和关键期限 |
| `TemplateRepository` | 文书生成 Agent | 读取劳动仲裁申请书 Markdown 模板 |
| `ModelGatewayClient` | 所有 LLM Agent | 调用 Chat、Embedding 和 Reranker 模型 |
| `SafetyPolicyService` | 安全审核 Agent | 执行安全规则、引用检查和高风险内容拦截 |
| `AuditLogger` | 所有 Agent | 记录工具调用、节点耗时、输入输出哈希和状态 |

### 6.2 必要 MCP 工具清单

| MCP 工具名 | 调用方 | 能力 | 输入 | 输出 |
|---|---|---|---|---|
| `document.parse` | 文件解析 Worker、证据分析 Agent | 解析 PDF、Word、图片中的文本和结构 | `file_id` / 临时 URL | 文本、页码、段落、表格片段 |
| `ocr.extract` | 文件解析 Worker、证据分析 Agent | 对扫描件、图片、聊天截图执行 OCR | `file_id` / 临时 URL | OCR 文本、坐标、置信度 |
| `source.verify` | 法规检索 Agent、类案检索 Agent、安全审核 Agent | 核验法规或类案来源是否可追溯 | `source_url` / `source_id` | 来源状态、标题、摘要、访问时间 |

### 6.3 MCP 工具调用原则

- MCP 工具只处理文件解析、OCR、来源核验这类外部或可替换能力。
- MySQL、Milvus、BM25、Redis、MinIO 和模型网关通过算法端内部代码访问。
- 每次 MCP 调用必须携带 `trace_id`、`case_id` 和调用节点名称。
- MCP 工具输入中的敏感信息需要脱敏或最小化传递。
- `source.verify` 的结果需要写入审计日志，用于证明法条和类案来源可追溯。
- MCP 工具异常不能直接中断主流程，应返回可识别错误，由 Agent 决定降级、重试或提示用户。

## 7. Agent DAG 编排

首版使用 LangGraph 编排 Agent。编排不是线性链路，而是 DAG：强依赖节点串行执行，互不依赖的节点并行执行。

### 7.1 主流程

```text
START
  -> input_normalize
  -> parallel_precheck
       -> pii_detect
       -> intent_detect
       -> unsafe_request_detect
  -> intake_extract
  -> need_more_info?
       yes -> ask_user -> END
       no  -> labor_cause_classify
  -> parallel_analysis
       -> law_bm25_search
       -> law_vector_search
       -> precedent_bm25_search
       -> precedent_vector_search
       -> evidence_analyze
       -> deadline_analyze
       -> profile_candidate_extract
       -> labor_specialist_pre_analyze
  -> retrieval_merge_and_rerank
  -> issue_analyze
  -> strategy_plan
  -> need_arbitration_document?
       yes -> arbitration_document_generate
       no  -> skip_document
  -> answer_compose
  -> safety_review
  -> final_response
END
```

### 7.2 并行节点

| 并行组 | 节点 | 依赖 | 调用能力 |
|---|---|---|---|
| parallel_precheck | pii_detect | input_normalize | `ModelGatewayClient` |
| parallel_precheck | intent_detect | input_normalize | `ModelGatewayClient` |
| parallel_precheck | unsafe_request_detect | input_normalize | `ModelGatewayClient`、`SafetyPolicyService` |
| parallel_analysis | law_bm25_search | labor_cause_classify | `LaborLawRetriever.search_bm25` |
| parallel_analysis | law_vector_search | labor_cause_classify | `ModelGatewayClient.embed`、`LaborLawRetriever.search_vector` |
| parallel_analysis | precedent_bm25_search | labor_cause_classify | `LaborPrecedentRetriever.search_bm25` |
| parallel_analysis | precedent_vector_search | labor_cause_classify | `ModelGatewayClient.embed`、`LaborPrecedentRetriever.search_vector` |
| parallel_analysis | evidence_analyze | intake_extract | `EvidenceRepository`、`document.parse`、`ocr.extract`、`ModelGatewayClient` |
| parallel_analysis | deadline_analyze | intake_extract | `LaborDeadlineService` |
| parallel_analysis | profile_candidate_extract | intake_extract | `CaseRepository`、`ModelGatewayClient` |
| parallel_analysis | labor_specialist_pre_analyze | labor_cause_classify | `ModelGatewayClient` |

### 7.3 串行汇总节点

| 节点 | 依赖 | 调用能力 | 说明 |
|---|---|---|---|
| retrieval_merge_and_rerank | 法规检索、类案检索 | `RerankerClient`、`source.verify` | 合并 BM25 和向量检索结果，并核验关键来源 |
| issue_analyze | 检索结果、证据结果、专业初判 | `ModelGatewayClient` | 提炼争议焦点和举证责任 |
| strategy_plan | 争议焦点、证据、期限 | `ModelGatewayClient` | 生成处理路径 |
| arbitration_document_generate | 结构化案情、法规依据 | `TemplateRepository`、`ModelGatewayClient` | 生成仲裁申请书 Markdown 初稿 |
| answer_compose | 全部分析结果 | `ModelGatewayClient` | 生成用户可读回答 |
| safety_review | 最终回答和文书初稿 | `SafetyPolicyService`、`source.verify` | 拦截或修正高风险输出，并核验引用来源 |

## 8. Agent 节点职责

### 8.1 案情采集 Agent

职责：

- 抽取劳动争议关键事实。
- 判断是否需要追问。
- 将自然语言转为结构化案情。

结构化输出：

```json
{
  "summary": "用户称公司拖欠三个月工资并拒绝开具离职证明。",
  "labor_relation": {
    "employer": "用人单位",
    "employee": "用户",
    "start_date": null,
    "end_date": null,
    "salary": null,
    "has_written_contract": null
  },
  "facts": [
    {
      "fact": "用人单位拖欠三个月工资",
      "time": null,
      "source": "user_message",
      "confidence": 0.9
    }
  ],
  "claims": ["支付拖欠工资", "开具离职证明"],
  "missing_questions": [
    "是否签订劳动合同？",
    "入职时间和离职时间分别是什么？",
    "每月工资标准是多少？",
    "是否有工资流水、考勤记录或聊天记录？"
  ]
}
```

### 8.2 劳动争议案由识别 Agent

职责：

- 判断劳动争议子类型。
- 输出候选请求事项。
- 标记是否属于首版支持范围。

输出：

```json
{
  "primary_domain": "劳动争议",
  "supported": true,
  "possible_causes": [
    {"cause": "追索劳动报酬", "confidence": 0.88},
    {"cause": "劳动合同纠纷", "confidence": 0.74}
  ],
  "procedure_hint": "劳动争议通常需先申请劳动仲裁。",
  "risk_flags": ["需关注劳动仲裁时效"]
}
```

### 8.3 法规检索 Agent

职责：

- 构造劳动法律法规检索 query。
- 并行调用 `LaborLawRetriever.search_bm25` 和 `LaborLawRetriever.search_vector`。
- 合并并调用 `RerankerClient`。
- 输出带来源的法条。

### 8.4 类案检索 Agent

职责：

- 检索劳动争议相似案例。
- 提取当前案情和类案的相似点、差异点。
- 只给出参考倾向，不做胜诉承诺。

### 8.5 证据分析 Agent

职责：

- 分析劳动合同、工资流水、考勤、聊天记录、辞退通知等证据。
- 判断证据证明对象。
- 输出证据缺口。

输出：

```json
{
  "evidence_items": [
    {
      "name": "微信聊天记录",
      "type": "电子数据",
      "proves": "双方存在工资支付争议沟通记录",
      "strength": "medium",
      "risk": "仅截图证明力有限，建议保留原始载体"
    }
  ],
  "missing_evidence": ["劳动合同", "银行工资流水", "考勤记录"]
}
```

### 8.6 时效 Agent

职责：

- 识别入职日期、离职日期、工资拖欠日期、辞退日期等关键日期。
- 调用 `LaborDeadlineService` 计算或提示劳动仲裁时效风险。
- 对缺失日期进行追问。

### 8.7 争议焦点 Agent

职责：

- 提炼劳动争议焦点。
- 关联证据和待证事实。
- 输出举证责任和证明状态。

输出：

```json
{
  "issues": [
    {
      "issue": "双方是否存在劳动关系",
      "burden_of_proof": "用户需初步证明接受用人单位管理并提供劳动",
      "current_evidence_status": "证据不足",
      "needed_evidence": ["劳动合同", "工牌", "考勤记录", "工资流水"],
      "impact": "high"
    }
  ]
}
```

### 8.8 策略规划 Agent

职责：

- 综合法规、类案、证据、时效和争议焦点。
- 输出协商、投诉、劳动仲裁的处理路径。
- 输出材料清单和风险提示。

### 8.9 仲裁申请书生成 Agent

职责：

- 使用 `TemplateRepository` 获取仲裁申请书模板。
- 根据结构化案情生成 Markdown 初稿。
- 缺失字段使用“待补充”标记。
- 不虚构当事人、金额、日期、法条和证据。

### 8.10 法律档案 Agent

职责：

- 生成案件档案候选项。
- 抽取案件时间线、证据清单、待办事项。
- 调用 `CaseRepository` 保存待确认项。
- 等待用户确认后由服务端写入正式档案。

### 8.11 安全审核 Agent

职责：

- 审核最终回答和仲裁申请书初稿。
- 拦截伪造证据、逃避执行、威胁对方等内容。
- 检查法条、类案是否有来源。
- 将“确定会赢”等表述改写为风险提示。

## 9. RAG 检索实现

### 9.1 知识库

首版只构建劳动争议相关知识库：

| 知识库 | 内容 | 存储 |
|---|---|---|
| 劳动法规库 | 劳动合同法、劳动争议调解仲裁法、相关司法解释和常用条文 | MySQL 元数据 + Milvus 向量 + BM25 索引 |
| 劳动类案库 | 劳动报酬、未签合同、违法解除、加班费等案例摘要 | MySQL 元数据 + Milvus 向量 + BM25 索引 |
| 文书模板库 | 劳动仲裁申请书、证据目录模板 | MySQL 元数据 + Milvus 向量 |
| 时效规则库 | 劳动仲裁时效和常见期限规则 | MySQL |

### 9.2 混合检索流程

```text
结构化案情
  -> query_rewrite
  -> BM25 关键词检索
  -> Milvus 向量检索
  -> 候选结果合并
  -> Reranker 重排序
  -> 来源过滤
  -> Top-K context
```

合并规则：

- BM25 返回关键词匹配片段和 BM25 分数。
- Milvus 返回语义相似片段和向量相似度。
- 合并阶段按 `source_id` 去重，保留最高相关片段。
- Reranker 对候选片段进行二次排序。
- 来源过滤会剔除无来源、失效、低相关或不符合劳动争议场景的结果。

## 10. 异步任务与削峰填谷

系统使用 Python async 和 RabbitMQ 处理高耗时任务。

在线请求使用 FastAPI async endpoint 和 `async/await`：

- 服务端异步调用算法端内部 API。
- 服务端通过 SSE 流式返回 Agent 状态。
- 算法端并行执行无依赖 Agent 节点。
- 算法端并行调用 BM25、Milvus、Reranker 和模型网关。

进入 RabbitMQ 的任务：

| 任务 | 触发时机 | 处理方式 |
|---|---|---|
| OCR 解析 | 用户上传图片、扫描件、PDF | 算法端 Worker 消费 |
| 文档解析 | 用户上传 Word、PDF | 算法端 Worker 消费 |
| 知识库索引构建 | 新增法规、案例、模板 | 索引 Worker 消费 |

削峰策略：

- 服务端创建任务并返回 `task_id`。
- Worker 按队列优先级和并发数消费任务。
- Redis 保存任务状态、进度和短期结果。
- MySQL 保存任务最终结果和审计记录。
- 失败任务进入重试队列，超过重试次数进入死信队列。

## 11. 数据存储设计

### 11.1 MySQL 业务表

#### users

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 用户 ID |
| username | varchar | 用户名 |
| password_hash | varchar | 密码哈希 |
| created_at | timestamp | 创建时间 |

#### legal_cases

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 案件 ID |
| user_id | char(36) | 用户 ID |
| title | varchar | 案件标题 |
| domain | varchar | 固定为劳动争议 |
| cause | varchar | 劳动争议子类型 |
| status | varchar | 案件状态 |
| summary | text | 案情摘要 |
| confidence | float | 识别置信度 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

#### case_facts

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 事实 ID |
| case_id | char(36) | 案件 ID |
| fact_text | text | 事实内容 |
| occurred_at | date | 发生日期 |
| source | varchar | 来源 |
| confidence | float | 置信度 |
| confirmed_by_user | boolean | 是否经用户确认 |

#### evidence_items

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 证据 ID |
| case_id | char(36) | 案件 ID |
| name | varchar | 证据名称 |
| evidence_type | varchar | 证据类型 |
| file_url | varchar | 文件地址 |
| extracted_text | text | 抽取文本 |
| proves | text | 证明对象 |
| strength | varchar | 证明强度 |
| risk | text | 证据风险 |
| confirmed_by_user | boolean | 是否经用户确认 |

#### legal_sources

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 法源 ID |
| title | varchar | 法律法规名称 |
| article | varchar | 条文 |
| content | text | 条文内容 |
| status | varchar | 效力状态 |
| source_url | varchar | 来源地址 |
| milvus_id | varchar | Milvus 向量记录 ID |
| bm25_doc_id | varchar | BM25 索引文档 ID |

#### precedent_cases

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 案例 ID |
| title | varchar | 案件标题 |
| cause | varchar | 案由 |
| court | varchar | 法院 |
| key_facts | text | 关键事实 |
| court_view | text | 裁判观点 |
| source_url | varchar | 来源 |
| milvus_id | varchar | Milvus 向量记录 ID |
| bm25_doc_id | varchar | BM25 索引文档 ID |

#### generated_documents

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 文书 ID |
| case_id | char(36) | 案件 ID |
| document_type | varchar | 文书类型 |
| title | varchar | 标题 |
| content_md | text | Markdown 内容 |
| status | varchar | draft/confirmed |
| created_at | timestamp | 创建时间 |

#### profile_candidates

| 字段 | 类型 | 说明 |
|---|---|---|
| id | char(36) | 候选项 ID |
| case_id | char(36) | 案件 ID |
| candidate_type | varchar | timeline/evidence/todo/fact |
| content_json | json | 候选内容 |
| status | varchar | pending/confirmed/rejected |
| created_at | timestamp | 创建时间 |

### 11.2 Milvus 集合

| Collection | 内容 | 主要字段 |
|---|---|---|
| labor_law_chunks | 劳动法规条文切片 | id、source_id、title、article、text、embedding、status |
| labor_precedent_chunks | 劳动类案切片 | id、source_id、cause、court、text、embedding |
| labor_template_chunks | 劳动仲裁文书模板切片 | id、template_type、scene、text、embedding |

### 11.3 BM25 索引

| 索引 | 内容 | 用途 |
|---|---|---|
| labor_law_bm25 | 劳动法规条文 | 法规关键词检索、法条编号检索 |
| labor_precedent_bm25 | 劳动类案摘要 | 案由、法院、关键词检索 |
| labor_template_bm25 | 劳动文书模板 | 模板检索 |

## 12. API 设计

### 12.1 服务端对前端 API

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | /api/auth/login | 用户登录 |
| POST | /api/chat/stream | 提交劳动争议问题并流式返回 Agent 结果 |
| GET | /api/cases | 获取案件列表 |
| POST | /api/cases | 创建案件 |
| GET | /api/cases/{case_id} | 获取案件详情 |
| PATCH | /api/cases/{case_id} | 更新案件信息 |
| POST | /api/cases/{case_id}/confirm-profile | 确认档案更新项 |
| POST | /api/evidence/upload | 上传证据 |
| POST | /api/evidence/{evidence_id}/analyze | 创建证据分析任务 |
| GET | /api/tasks/{task_id} | 查询异步任务状态 |
| GET | /api/cases/{case_id}/evidence | 获取证据目录 |
| POST | /api/documents/arbitration | 生成劳动仲裁申请书初稿 |
| GET | /api/documents/{document_id} | 查看文书 |

### 12.2 算法端内部 API

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | /internal/agent/analyze | 执行劳动争议 Agent DAG |
| POST | /internal/evidence/analyze | 分析证据文件或证据文本 |
| POST | /internal/documents/arbitration | 生成劳动仲裁申请书初稿 |
| POST | /internal/rag/search-laws | 劳动法规混合检索 |
| POST | /internal/rag/search-cases | 劳动类案混合检索 |
| POST | /internal/safety/review | 合规安全审核 |

## 13. 前端页面

首版页面：

| 页面 | 功能 |
|---|---|
| 登录页 | 用户认证 |
| 法律咨询页 | 劳动争议对话、追问、分析结果、引用依据 |
| 案件详情页 | 案情摘要、事实、诉求、证据、时效、档案候选项 |
| 证据管理页 | 上传证据、查看证据目录和证明对象 |
| 文书页面 | 查看和编辑劳动仲裁申请书 Markdown 初稿 |

## 14. 输出规范

最终回答包含：

1. 案情摘要。
2. 劳动争议子类型。
3. 关键争议焦点。
4. 现有证据分析。
5. 需要补充的信息或证据。
6. 相关法律依据。
7. 类案参考。
8. 处理路径。
9. 时效风险。
10. 档案更新候选项。

推荐表达：

- “根据你目前提供的信息，可能涉及……”
- “该结论仍需结合劳动合同、工资流水、考勤记录等证据进一步判断。”
- “以下为仲裁申请书初稿，提交前需要由专业人士复核。”

禁止表达：

- “你一定能胜诉。”
- “仲裁委一定会支持。”
- “照这样做保证没问题。”
- “你可以伪造/补做证据。”

## 15. 安全与隐私

系统识别并保护以下敏感信息：

- 身份证号。
- 手机号。
- 银行卡号。
- 住址。
- 公司统一社会信用代码。
- 银行流水。
- 劳动合同。
- 聊天记录中的第三方信息。

隐私措施：

- 文件上传前提示用户授权。
- 档案写入前二次确认。
- 日志中脱敏存储敏感信息。
- 删除案件时同步删除证据文件和向量索引。
- 算法端不保存长期用户业务数据。

## 16. 监控指标

| 指标 | 说明 |
|---|---|
| 案由识别准确率 | 劳动争议子类型识别是否正确 |
| 要素抽取 F1 | 入职时间、离职时间、工资、合同、诉求等抽取效果 |
| 法条引用准确率 | 引用法条是否真实且与劳动争议相关 |
| 类案相关性 | 类案与当前案件的相似度是否满足阈值 |
| 证据分析准确率 | 证据类型、证明对象、证据缺口判断是否合理 |
| 文书完整性 | 仲裁申请书字段是否完整、格式是否规范 |
| 安全拦截率 | 对伪造证据、逃避执行等高风险请求的拦截能力 |
| 平均响应时间 | 常规咨询、证据分析、文书生成的接口耗时 |
| 队列堆积量 | RabbitMQ 中等待处理的任务数量 |
