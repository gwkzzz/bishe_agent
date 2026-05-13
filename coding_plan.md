# 法律咨询辅助 Multi-Agent 系统 Coding 计划

## 0. 目标与范围

本计划基于 `legal_multi_agent_design.md` 生成，用于指导首版 MVP 开发。

首版只做劳动争议场景，优先闭环：

1. 用户登录与案件管理。
2. 用户输入劳动争议描述，系统追问或给出结构化分析。
3. 系统检索法规、类案，分析证据与时效。
4. 系统生成处理路径、档案候选项和劳动仲裁申请书 Markdown 初稿。
5. 所有最终输出经过安全审核，避免虚构法条、虚构案例和确定性承诺。

不纳入首版：

- 非劳动争议法律场景。
- 自动胜诉判断、自动裁判、律师执业替代。
- 复杂权限体系、多租户、在线支付。
- 完整生产级监控面板，可先暴露指标并保留 Grafana 配置入口。

## 1. 推荐仓库结构

```text
.
├── frontend/                 # Vue 3 前端
├── server/                   # FastAPI 业务服务端
├── algorithm/                # FastAPI 算法端与 Agent DAG
├── infra/                    # Docker Compose、MySQL、Redis、RabbitMQ、Milvus、MinIO
├── docs/                     # 补充设计、接口契约、测试说明
├── legal_multi_agent_design.md
└── coding_plan.md
```

三层边界必须保持清晰：

- `frontend` 只调用 `server` 的 `/api/*`。
- `server` 处理认证、案件、证据、文书、任务状态，不直接调用大模型。
- `algorithm` 处理 Agent、RAG、OCR、文档解析、模型网关和安全审核，不保存长期用户业务数据。

## 2. 里程碑总览

| 阶段 | 目标 | 主要产物 | 建议优先级 |
|---|---|---|---|
| M0 | 工程骨架与基础规范 | 前后端项目、算法端项目、Docker Compose、配置体系 | P0 |
| M1 | 数据模型与基础设施 | MySQL 表、Alembic 迁移、Redis/RabbitMQ/MinIO/Milvus 客户端 | P0 |
| M2 | 服务端业务 API | 登录、案件、证据、任务、文书 API | P0 |
| M3 | 算法端契约与 Mock DAG | 内部 API、Pydantic schema、可运行 LangGraph 骨架 | P0 |
| M4 | 前端 MVP 页面 | 登录页、咨询页、案件详情、证据管理、文书页 | P0 |
| M5 | RAG 与知识库 | 法规/类案/模板入库、BM25、Milvus、Rerank 合并 | P1 |
| M6 | 证据异步分析 | 上传、任务队列、文档解析、OCR、证据结构化 | P1 |
| M7 | 完整 Agent DAG | 案情采集、案由识别、争议焦点、策略、档案候选、安全审核 | P1 |
| M8 | 仲裁文书生成 | 模板读取、Markdown 初稿生成、缺失字段标记、安全审核 | P1 |
| M9 | 验证、监控与收尾 | 测试、日志、指标、端到端验收、部署说明 | P2 |

## 3. M0：工程骨架与基础规范

### 3.1 前端初始化

- 使用 Vite 初始化 `frontend`。
- 引入 Vue 3、TypeScript、Vue Router、Pinia、Element Plus、Axios、TanStack Query、markdown-it、PDF.js。
- 建立目录：
  - `src/api`
  - `src/router`
  - `src/stores`
  - `src/views`
  - `src/components`
  - `src/types`

验收标准：

- `npm run dev` 可启动。
- 路由包含登录页、咨询页、案件详情页、证据管理页、文书页。
- Axios 有统一 baseURL、错误处理和 token 注入位置。

### 3.2 服务端初始化

- 创建 `server` FastAPI 项目。
- 引入 Pydantic v2、SQLAlchemy 2.x、Alembic、PyMySQL、Uvicorn、structlog。
- 建立目录：
  - `app/api`
  - `app/core`
  - `app/models`
  - `app/schemas`
  - `app/repositories`
  - `app/services`
  - `app/integrations`
  - `app/tasks`
  - `tests`

验收标准：

- `GET /health` 返回服务状态。
- 配置从 `.env` 读取。
- 日志包含 `trace_id` 占位。

### 3.3 算法端初始化

- 创建 `algorithm` FastAPI 项目。
- 引入 Pydantic v2、LangGraph、pymilvus、PyMuPDF、python-docx、PaddleOCR、structlog。
- 建立目录：
  - `app/api`
  - `app/agents`
  - `app/graph`
  - `app/retrieval`
  - `app/repositories`
  - `app/services`
  - `app/model_gateway`
  - `app/workers`
  - `app/safety`
  - `tests`

验收标准：

- `GET /health` 返回服务状态。
- 内部 API 使用统一鉴权 header 或共享 token。
- 所有内部响应包含 `trace_id`。

### 3.4 基础设施

- 在 `infra` 提供 Docker Compose：
  - MySQL
  - Redis
  - RabbitMQ
  - MinIO
  - Milvus standalone
- 增加 `.env.example`。

验收标准：

- 本地一条命令可启动依赖服务。
- 服务端和算法端均可连接依赖服务。

## 4. M1：数据模型与基础设施

### 4.1 MySQL 表与迁移

实现文档中的业务表：

- `users`
- `legal_cases`
- `case_facts`
- `evidence_items`
- `legal_sources`
- `precedent_cases`
- `generated_documents`
- `profile_candidates`

建议补充表：

- `chat_messages`：保存用户消息、系统回答、结构化结果摘要。
- `async_tasks`：保存 OCR、文档解析、证据分析、索引任务状态。
- `audit_logs`：保存 Agent 节点、工具调用、输入输出 hash、耗时、状态。

验收标准：

- Alembic 可从空库迁移到最新版本。
- 所有关联字段具备索引。
- 删除案件时具备级联清理策略，至少服务层明确实现。

### 4.2 基础客户端封装

服务端实现：

- `DatabaseSession`
- `RedisClient`
- `RabbitMQPublisher`
- `MinIOClient`
- `AlgorithmClient`

算法端实现：

- `CaseRepository`
- `EvidenceRepository`
- `LaborLawRetriever`
- `LaborPrecedentRetriever`
- `RerankerClient`
- `TemplateRepository`
- `ModelGatewayClient`
- `SafetyPolicyService`
- `AuditLogger`

验收标准：

- 客户端有超时、错误包装和日志。
- 算法端内部能力不包装成 MCP 工具。
- MCP 仅预留 `document.parse`、`ocr.extract`、`source.verify` 适配层。

## 5. M2：服务端业务 API

### 5.1 认证

实现：

- `POST /api/auth/login`
- 密码 hash 校验。
- JWT 或 session token。

验收标准：

- 未登录访问业务 API 返回 401。
- 登录成功返回 token 和用户信息。

### 5.2 案件管理

实现：

- `GET /api/cases`
- `POST /api/cases`
- `GET /api/cases/{case_id}`
- `PATCH /api/cases/{case_id}`
- `POST /api/cases/{case_id}/confirm-profile`

验收标准：

- 用户只能访问自己的案件。
- 档案候选项支持 `pending / confirmed / rejected`。
- 确认候选项后写入正式事实、证据或待办数据。

### 5.3 在线咨询

实现：

- `POST /api/chat/stream`
- 服务端保存用户消息。
- 服务端调用 `algorithm /internal/agent/analyze`。
- 服务端保存结构化分析结果和档案候选项。
- 通过 SSE 返回 Agent 状态和最终回答。

验收标准：

- 前端可看到流式状态。
- 算法端异常时返回可读降级提示。
- 不在服务端直接调用模型。

### 5.4 证据与任务

实现：

- `POST /api/evidence/upload`
- `POST /api/evidence/{evidence_id}/analyze`
- `GET /api/tasks/{task_id}`
- `GET /api/cases/{case_id}/evidence`

验收标准：

- 文件上传到 MinIO。
- `evidence_items` 保存元数据。
- RabbitMQ 创建异步任务。
- Redis/MySQL 可查询任务状态。

### 5.5 文书

实现：

- `POST /api/documents/arbitration`
- `GET /api/documents/{document_id}`

验收标准：

- 服务端读取案件结构化数据后调用算法端。
- 返回并保存 Markdown 初稿。
- 文书状态为 `draft / confirmed`。

## 6. M3：算法端契约与 Mock DAG

### 6.1 内部 API

实现：

- `POST /internal/agent/analyze`
- `POST /internal/evidence/analyze`
- `POST /internal/documents/arbitration`
- `POST /internal/rag/search-laws`
- `POST /internal/rag/search-cases`
- `POST /internal/safety/review`

验收标准：

- 所有接口有 Pydantic request/response schema。
- 所有接口返回结构稳定，便于前端和服务端先并行开发。
- 初期可返回 mock 数据，但字段必须贴近最终输出规范。

### 6.2 LangGraph 骨架

实现节点：

- `input_normalize`
- `pii_detect`
- `intent_detect`
- `unsafe_request_detect`
- `intake_extract`
- `need_more_info`
- `labor_cause_classify`
- `parallel_analysis`
- `retrieval_merge_and_rerank`
- `issue_analyze`
- `strategy_plan`
- `arbitration_document_generate`
- `answer_compose`
- `safety_review`
- `final_response`

验收标准：

- DAG 可执行完整流程。
- 缺信息时返回追问，不继续生成结论。
- 每个节点写审计日志或至少打结构化日志。

## 7. M4：前端 MVP 页面

### 7.1 登录页

- 用户名、密码输入。
- 登录成功保存 token 并跳转咨询页。

### 7.2 法律咨询页

- 左侧案件列表或当前案件入口。
- 主区域为对话流。
- 支持显示：
  - Agent 当前状态。
  - 追问问题。
  - 案情摘要。
  - 争议焦点。
  - 法律依据。
  - 类案参考。
  - 处理路径。
  - 时效风险。
  - 档案候选项。

验收标准：

- SSE 流式更新稳定。
- Markdown 内容正确渲染。
- 风险提示和免责声明视觉上清晰但不喧宾夺主。

### 7.3 案件详情页

- 展示案情摘要、事实、诉求、证据、时效、档案候选项。
- 支持确认或拒绝候选项。

### 7.4 证据管理页

- 上传证据。
- 查看解析状态。
- 展示证据证明对象、强度、风险、缺口。

### 7.5 文书页面

- 查看劳动仲裁申请书 Markdown 初稿。
- 支持基础编辑。
- 标记“待补充”字段。

## 8. M5：RAG 与知识库

### 8.1 数据导入

构建首版知识库：

- 劳动法规库。
- 劳动类案库。
- 文书模板库。
- 时效规则库。

验收标准：

- 每条法规和类案都有 `source_url` 或可追溯 `source_id`。
- 法规条文有状态字段。
- 数据导入脚本可重复执行并去重。

### 8.2 BM25 与 Milvus

实现：

- `labor_law_bm25`
- `labor_precedent_bm25`
- `labor_template_bm25`
- `labor_law_chunks`
- `labor_precedent_chunks`
- `labor_template_chunks`

验收标准：

- 新增法规、案例、模板后可重建索引。
- 支持按 `source_id` 去重。
- 支持 Top-K 检索。

### 8.3 混合检索

实现流程：

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

验收标准：

- 法规检索和类案检索均返回来源、标题、片段、相关分。
- 低相关、无来源、失效内容被过滤。
- `source.verify` 异常时允许降级，但必须记录审计日志。

## 9. M6：证据异步分析

### 9.1 上传与任务队列

- 服务端上传文件到 MinIO。
- 创建 `evidence_items`。
- 创建 `async_tasks`。
- 投递 RabbitMQ。

### 9.2 Worker

算法端 Worker 消费任务：

- PDF/Word 使用文档解析。
- 图片/扫描件/聊天截图使用 OCR。
- 抽取文本后调用证据分析 Agent。
- 将结果回写服务端或服务端可拉取结果。

验收标准：

- 支持任务重试。
- 超过重试次数进入失败状态。
- 证据结果包括证明对象、强度、风险和缺失证据建议。

## 10. M7：完整 Agent DAG

逐步替换 Mock 节点：

1. 案情采集 Agent：抽取结构化案情和缺失问题。
2. 案由识别 Agent：识别劳动争议子类型和是否支持。
3. 法规检索 Agent：调用混合检索。
4. 类案检索 Agent：调用混合检索并提取相似点、差异点。
5. 证据分析 Agent：读取证据元数据和解析文本。
6. 时效 Agent：识别关键日期并计算风险。
7. 争议焦点 Agent：输出待证明事实、举证责任、证据状态。
8. 策略规划 Agent：输出协商、投诉、仲裁路径。
9. 法律档案 Agent：生成时间线、证据、待办、事实候选项。
10. 安全审核 Agent：检查虚构来源、确定性承诺和高风险请求。

验收标准：

- 缺少关键事实时优先追问。
- 有足够信息时输出完整规范字段。
- 每个最终回答包含文档要求的 10 类内容。
- 明确使用“可能涉及”“仍需结合证据判断”等审慎表达。

## 11. M8：仲裁申请书生成

### 11.1 模板

建立劳动仲裁申请书 Markdown 模板，至少包含：

- 申请人。
- 被申请人。
- 仲裁请求。
- 事实与理由。
- 证据目录。
- 法律依据。
- 尾部签署信息。

### 11.2 生成

算法端根据结构化案情生成初稿：

- 缺失字段写“待补充”。
- 不虚构金额、日期、当事人、证据、法条。
- 引用法条必须来自检索结果。

验收标准：

- 文书通过安全审核。
- 前端可查看和编辑 Markdown。
- 提交前提示需专业人士复核。

## 12. M9：验证、监控与收尾

### 12.1 测试

服务端测试：

- 认证。
- 案件 CRUD。
- 证据上传。
- 任务状态。
- 文书保存。
- 算法端异常降级。

算法端测试：

- 案情抽取 schema。
- 案由识别。
- 混合检索去重和排序。
- 时效计算。
- 安全审核改写。
- 文书缺失字段处理。

前端测试：

- 登录流程。
- SSE 渲染。
- 案件详情。
- 证据上传状态。
- 文书编辑。

### 12.2 端到端验收用例

至少覆盖：

- 拖欠工资。
- 未签劳动合同。
- 违法解除。
- 加班费争议。
- 拒开离职证明。
- 缺少关键日期，需要追问。
- 用户要求伪造证据，应被拦截。
- 法条或类案来源缺失，应被过滤或提示降级。

### 12.3 监控指标

先暴露 Prometheus 指标：

- 案由识别准确率。
- 要素抽取 F1。
- 法条引用准确率。
- 类案相关性。
- 证据分析准确率。
- 文书完整性。
- 安全拦截率。
- 平均响应时间。
- RabbitMQ 队列堆积量。

## 13. 推荐开发顺序

1. 先完成 `infra`、`server`、`algorithm`、`frontend` 骨架。
2. 先用 Mock 算法端打通 `前端 -> 服务端 -> 算法端 -> SSE 返回`。
3. 完成 MySQL 表和服务端案件/证据/文书 API。
4. 完成前端五个 MVP 页面。
5. 接入真实 LangGraph DAG，但节点先返回规则或 mock 结果。
6. 接入模型网关，替换案情抽取、案由识别、争议焦点、策略生成。
7. 接入 RAG，替换法规和类案检索。
8. 接入证据异步分析。
9. 接入仲裁申请书生成。
10. 做安全审核、端到端测试和性能收尾。

## 14. 第一轮可执行任务清单

第一轮目标是打通系统主干，不追求智能效果。

- 创建 `infra/docker-compose.yml` 和 `.env.example`。
- 创建 `server` FastAPI 项目，提供 `/health` 和 `/api/auth/login`。
- 创建 `algorithm` FastAPI 项目，提供 `/health` 和 mock `/internal/agent/analyze`。
- 创建 `frontend` Vite 项目，提供登录页和咨询页。
- 服务端实现 `/api/chat/stream`，调用算法端 mock API 并用 SSE 返回。
- 前端实现咨询输入框、消息流和 Agent 状态展示。
- 增加最小 README，说明本地启动顺序。

第一轮完成标准：

- 本地启动依赖、服务端、算法端、前端。
- 用户登录后进入咨询页。
- 输入劳动争议描述后，页面能流式展示 mock 分析结果。
- mock 结果结构已经包含案情摘要、案由、争议焦点、证据缺口、处理路径、时效风险和安全提示。

## 15. 风险与注意事项

- 法律输出必须始终是辅助参考，不能承诺胜诉或保证结果。
- 法规和类案必须有来源，缺来源时宁可降级提示。
- 服务端和算法端职责不能混淆，服务端不直接调用大模型。
- 算法端不长期保存用户业务数据。
- 文件、日志、审计记录中的敏感信息需要脱敏。
- 档案候选项必须由用户确认后再写入正式档案。
- MCP 工具异常不能直接中断主流程，应返回可识别错误并降级。
