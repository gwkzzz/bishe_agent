# 法律咨询辅助 Multi-Agent 系统

本仓库当前完成到 M5 RAG 与知识库，包含：

- `frontend`：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、Axios。
- `server`：FastAPI 业务服务端，包含 `/health`、配置读取、CORS、trace header。
- `algorithm`：FastAPI 算法端，包含 `/health`、内部 token 鉴权、trace header、M3 内部 API、Pydantic 契约、可运行 LangGraph DAG，以及 M5 劳动法规/类案/模板知识库检索。
- `infra`：MySQL、Redis、RabbitMQ、MinIO、Milvus 的 Docker Compose 配置。
- `docs/m1_infrastructure.md`：M1 表结构、迁移命令和基础客户端说明。

算法端 M3 内部接口：

- `POST /internal/agent/analyze`
- `POST /internal/evidence/analyze`
- `POST /internal/documents/arbitration`
- `POST /internal/rag/search-laws`
- `POST /internal/rag/search-cases`
- `POST /internal/safety/review`

M5 知识库能力：

- `algorithm/app/retrieval/data/labor_knowledge.json` 提供首版劳动法规、类案、模板和时效规则种子数据。
- `algorithm/app/retrieval` 实现 `labor_law_bm25`、`labor_precedent_bm25`、`labor_template_bm25`，支持查询改写、BM25 检索、可选 Milvus 向量检索、去重、重排和来源过滤。
- `algorithm/scripts/import_knowledge.py` 可重复导入 MySQL，并可按需重建 `labor_law_chunks`、`labor_precedent_chunks`、`labor_template_chunks`。

## 本地配置

```bash
cp .env.example .env
```

## 基础设施

```bash
docker compose --env-file .env -f infra/docker-compose.yml up -d
```

## 服务端

```bash
cd server
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 算法端

```bash
cd algorithm
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e ".[dev]"
python scripts/import_knowledge.py --skip-db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

导入 MySQL 知识库：

```bash
cd algorithm
python scripts/import_knowledge.py
```

如需同时重建 Milvus 向量集合：

```bash
cd algorithm
python scripts/import_knowledge.py --with-milvus --drop-vector
```

## 前端

```bash
cd frontend
npm install
npm run dev
```

前端本地地址：`http://localhost:5173`
