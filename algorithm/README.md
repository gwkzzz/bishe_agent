# Algorithm

FastAPI algorithm service. It owns the LangGraph agent DAG, RAG retrieval, model
gateway, evidence parsing workers, and safety review.

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Health check:

```bash
curl http://localhost:8001/health
```

Internal endpoints require:

```text
X-Internal-Token: <ALGORITHM_INTERNAL_TOKEN>
```

M3 includes stable Pydantic contracts and a runnable LangGraph DAG for:

- `POST /internal/agent/analyze`
- `POST /internal/evidence/analyze`
- `POST /internal/documents/arbitration`
- `POST /internal/rag/search-laws`
- `POST /internal/rag/search-cases`
- `POST /internal/safety/review`

The DAG currently covers input normalization, PII and unsafe request checks,
intake extraction, missing-info routing, labor cause classification, M5 RAG
retrieval, issue analysis, strategy planning, arbitration document drafting,
safety review, and final response composition.

## M5 RAG knowledge base

Seed data lives in `app/retrieval/data/labor_knowledge.json` and covers:

- labor laws and judicial interpretation snippets with `source_url` or stable `source_id`;
- precedent summaries with traceable source metadata;
- document templates;
- limitation-period rules.

Local search uses BM25 indexes named `labor_law_bm25`,
`labor_precedent_bm25`, and `labor_template_bm25`. Set
`RAG_VECTOR_ENABLED=true` after building Milvus chunks to enable vector
retrieval from `labor_law_chunks`, `labor_precedent_chunks`, and
`labor_template_chunks`.

Validate seed data without infrastructure:

```bash
python scripts/import_knowledge.py --skip-db
```

Upsert MySQL knowledge rows:

```bash
python scripts/import_knowledge.py
```

Rebuild Milvus chunks:

```bash
python scripts/import_knowledge.py --with-milvus --drop-vector
```
