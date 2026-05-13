# M1 数据模型与基础设施说明

## 数据库表

M1 已建立服务端业务数据库模型和 Alembic 初始迁移，包含：

- `users`
- `legal_cases`
- `case_facts`
- `evidence_items`
- `legal_sources`
- `precedent_cases`
- `document_templates`
- `generated_documents`
- `profile_candidates`
- `chat_messages`
- `async_tasks`
- `audit_logs`

其中 `chat_messages`、`async_tasks`、`audit_logs` 是 coding 计划中补充的首版基础表；`document_templates` 用于承载文书模板库的 MySQL 元数据和 Markdown 模板内容。

## 迁移命令

```powershell
cd D:\bishe\server
alembic upgrade head
```

运行前需要先复制并配置根目录 `.env`：

```powershell
cd D:\bishe
copy .env.example .env
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

## 服务端基础客户端

服务端只处理业务态逻辑，M1 提供以下封装：

- `DatabaseSession`：`server/app/core/database.py`
- `RedisClient`：`server/app/integrations/redis_client.py`
- `RabbitMQPublisher`：`server/app/integrations/rabbitmq.py`
- `MinIOClient`：`server/app/integrations/minio_client.py`
- `AlgorithmClient`：`server/app/integrations/algorithm_client.py`

## 算法端内部能力

算法端只处理模型态逻辑，M1 提供以下占位实现：

- `CaseRepository`
- `EvidenceRepository`
- `TemplateRepository`
- `LaborLawRetriever`
- `LaborPrecedentRetriever`
- `RerankerClient`
- `ModelGatewayClient`
- `SafetyPolicyService`
- `AuditLogger`
- `LaborDeadlineService`

MCP 仅预留以下可替换工具：

- `document.parse`
- `ocr.extract`
- `source.verify`

这些工具当前返回 `not_configured`，后续接入真实 MCP 服务时替换实现即可。
