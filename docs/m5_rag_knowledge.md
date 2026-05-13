# M5 RAG 与知识库说明

## 范围

M5 在算法端实现首版劳动争议知识库与混合检索能力：

- 劳动法规库：`legal_sources` 与本地种子 JSON。
- 劳动类案库：`precedent_cases` 与本地种子 JSON。
- 文书模板库：`document_templates` 与本地种子 JSON。
- 时效规则库：本地种子 JSON，并纳入法规检索上下文。

## 检索流程

```text
结构化案情或用户问题
  -> query_rewrite
  -> BM25 检索
  -> 可选 Milvus 向量检索
  -> source_id 去重
  -> 本地 overlap rerank
  -> 来源和状态过滤
  -> Top-K context
```

## 索引命名

- `labor_law_bm25`
- `labor_precedent_bm25`
- `labor_template_bm25`
- `labor_law_chunks`
- `labor_precedent_chunks`
- `labor_template_chunks`

## 导入与重建

验证种子数据：

```powershell
cd D:\bishe\algorithm
python scripts/import_knowledge.py --skip-db
```

导入 MySQL：

```powershell
cd D:\bishe\algorithm
python scripts/import_knowledge.py
```

重建 Milvus：

```powershell
cd D:\bishe\algorithm
python scripts/import_knowledge.py --with-milvus --drop-vector
```

## 降级策略

默认 `RAG_VECTOR_ENABLED=false`，系统使用本地 BM25 知识库即可运行。
启用向量检索后，如果 Milvus 查询异常，算法端记录结构化日志并退回 BM25 结果。
