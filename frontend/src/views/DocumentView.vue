<template>
  <section class="page document-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">文书</h1>
        <p class="page-caption">{{ documentTitle }}</p>
      </div>
      <div class="toolbar">
        <el-select
          v-model="selectedCaseId"
          class="case-select"
          placeholder="选择案件"
          filterable
          @change="selectCase"
        >
          <el-option v-for="item in cases" :key="item.id" :label="item.title" :value="item.id" />
        </el-select>
        <el-button
          :icon="DocumentAdd"
          type="primary"
          :disabled="!selectedCaseId"
          :loading="generating"
          @click="generateDocument"
        >
          生成初稿
        </el-button>
      </div>
    </header>

    <section class="surface document-meta">
      <div>
        <span class="meta-label">案件</span>
        <strong>{{ selectedCase?.title || "未选择" }}</strong>
      </div>
      <div>
        <span class="meta-label">状态</span>
        <StatusPill :label="documentStatus" :tone="documentStatusTone" />
      </div>
      <div>
        <span class="meta-label">待补充</span>
        <strong>{{ missingFields.length }} 处</strong>
      </div>
    </section>

    <section v-if="missingFields.length" class="surface missing-panel">
      <div v-for="item in missingFields" :key="item" class="missing-item">
        <span>待补充</span>
        <strong>{{ item }}</strong>
      </div>
    </section>

    <section class="document-layout">
      <el-input
        v-model="markdown"
        class="document-editor"
        type="textarea"
        resize="none"
        :autosize="{ minRows: 22 }"
      />
      <article class="surface document-preview">
        <div class="markdown-body" v-html="rendered" />
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { DocumentAdd } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import MarkdownIt from "markdown-it";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { listCases } from "@/api/cases";
import { createArbitrationDocument, getDocument } from "@/api/documents";
import StatusPill from "@/components/StatusPill.vue";
import { useWorkspaceStore } from "@/stores/workspace";
import type { CaseRead, GeneratedDocumentRead } from "@/types/api";
import { statusLabel } from "@/utils/format";

const route = useRoute();
const router = useRouter();
const workspace = useWorkspaceStore();
const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

const cases = ref<CaseRead[]>([]);
const document = ref<GeneratedDocumentRead | null>(null);
const selectedCaseId = ref<string | null>(null);
const markdown = ref("# 劳动仲裁申请书\n\n待补充");
const generating = ref(false);

const documentId = computed(() => (typeof route.params.documentId === "string" ? route.params.documentId : null));
const selectedCase = computed(() => cases.value.find((item) => item.id === selectedCaseId.value) ?? null);
const documentTitle = computed(() => document.value?.title || "劳动仲裁申请书初稿");
const documentStatus = computed(() => statusLabel(document.value?.status || "draft"));
const documentStatusTone = computed(() => (document.value?.status === "confirmed" ? "success" : "warning"));
const rendered = computed(() => md.render(markdown.value).replace(/待补充/g, "<mark>待补充</mark>"));
const missingFields = computed(() => inferMissingFields(markdown.value));

onMounted(async () => {
  await loadCasesForSelect();
  await loadRouteDocument();
});

watch(documentId, loadRouteDocument);

async function loadCasesForSelect() {
  try {
    cases.value = await listCases();
    const queryCaseId = typeof route.query.case_id === "string" ? route.query.case_id : null;
    selectedCaseId.value = queryCaseId ?? workspace.currentCaseId ?? cases.value[0]?.id ?? null;
    if (selectedCaseId.value) {
      workspace.setCurrentCaseId(selectedCaseId.value);
    }
  } catch {
    ElMessage.error("案件列表加载失败");
  }
}

async function loadRouteDocument() {
  if (!documentId.value || documentId.value === "demo") return;
  try {
    const item = await getDocument(documentId.value);
    applyDocument(item);
  } catch {
    ElMessage.error("文书加载失败");
  }
}

function selectCase(caseId: string) {
  selectedCaseId.value = caseId;
  workspace.setCurrentCaseId(caseId);
}

async function generateDocument() {
  if (!selectedCaseId.value) return;
  generating.value = true;
  try {
    const item = await createArbitrationDocument(selectedCaseId.value);
    applyDocument(item);
    await router.replace(`/documents/${item.id}`);
    ElMessage.success("文书初稿已生成");
  } catch {
    ElMessage.error("文书生成失败，请确认服务端已启动");
  } finally {
    generating.value = false;
  }
}

function applyDocument(item: GeneratedDocumentRead) {
  document.value = item;
  markdown.value = item.content_md || "# 劳动仲裁申请书\n\n待补充";
  selectedCaseId.value = item.case_id;
  workspace.setCurrentCaseId(item.case_id);
  workspace.setCurrentDocumentId(item.id);
}

function inferMissingFields(value: string) {
  const lines = value.split(/\r?\n/);
  const fields = new Set<string>();
  let currentHeading = "正文";

  for (const line of lines) {
    const heading = line.match(/^#{1,6}\s+(.+)$/);
    if (heading) {
      currentHeading = heading[1].trim();
    }
    if (line.includes("待补充")) {
      fields.add(currentHeading);
    }
  }

  return [...fields];
}
</script>

<style scoped>
.document-page {
  max-width: 1320px;
}

.case-select {
  width: min(320px, 100%);
}

.document-meta {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) 160px 160px;
  gap: 16px;
  padding: 16px;
}

.document-meta > div {
  display: grid;
  gap: 6px;
}

.meta-label {
  color: var(--color-muted);
  font-size: 12px;
}

.missing-panel {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 14px 16px;
  border-color: rgba(245, 165, 36, 0.38);
  background: var(--color-amber-soft);
}

.missing-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid rgba(245, 165, 36, 0.45);
  border-radius: var(--radius);
  background: #ffffff;
}

.missing-item span {
  color: #9a6700;
  font-size: 12px;
}

.document-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  min-height: 620px;
}

.document-editor :deep(textarea) {
  min-height: 620px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  line-height: 1.7;
}

.document-preview {
  min-height: 620px;
  padding: 24px;
  overflow: auto;
}

.markdown-body :deep(h1) {
  margin-top: 0;
  font-size: 24px;
}

.markdown-body :deep(h2) {
  margin-top: 22px;
  font-size: 18px;
}

.markdown-body :deep(p),
.markdown-body :deep(li) {
  line-height: 1.8;
}

.markdown-body :deep(mark) {
  padding: 1px 4px;
  border-radius: 4px;
  color: #9a6700;
  background: #ffe8a3;
}

@media (max-width: 960px) {
  .document-meta,
  .document-layout {
    grid-template-columns: 1fr;
  }
}
</style>
