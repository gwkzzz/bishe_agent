<template>
  <section class="page case-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">案件详情</h1>
        <p class="page-caption">{{ caseData?.title || caseId }}</p>
      </div>
      <div class="toolbar">
        <StatusPill v-if="caseData" :label="statusLabel(caseData.status)" :tone="caseStatusTone(caseData.status)" />
        <el-button :icon="Refresh" :loading="loading" @click="loadCase">刷新</el-button>
        <RouterLink v-if="caseData" :to="`/cases/${caseData.id}/evidence`">
          <el-button :icon="Files">证据</el-button>
        </RouterLink>
        <RouterLink v-if="caseData" :to="`/documents?case_id=${caseData.id}`">
          <el-button :icon="Document">文书</el-button>
        </RouterLink>
      </div>
    </header>

    <el-skeleton v-if="loading && !caseData" :rows="8" animated />

    <template v-else-if="caseData">
      <section class="surface case-summary">
        <div>
          <span class="meta-label">案由</span>
          <strong>{{ caseData.cause || "待识别" }}</strong>
        </div>
        <div>
          <span class="meta-label">置信度</span>
          <strong>{{ percent(caseData.confidence) }}</strong>
        </div>
        <div>
          <span class="meta-label">更新时间</span>
          <strong>{{ formatDateTime(caseData.updated_at) }}</strong>
        </div>
      </section>

      <section class="case-grid">
        <div class="surface panel">
          <h2>案情摘要</h2>
          <p v-if="caseData.summary">{{ caseData.summary }}</p>
          <p v-else class="muted">暂无摘要</p>
        </div>

        <div class="surface panel">
          <h2>事实与诉求</h2>
          <div v-if="caseData.facts.length" class="record-list">
            <div v-for="fact in caseData.facts" :key="fact.id" class="record-row">
              <strong>{{ fact.fact_text }}</strong>
              <span>{{ fact.occurred_at ? formatDate(fact.occurred_at) : "时间待补充" }}</span>
            </div>
          </div>
          <p v-else class="muted">暂无已确认事实</p>
        </div>

        <div class="surface panel">
          <div class="panel-title-row">
            <h2>证据</h2>
            <RouterLink :to="`/cases/${caseData.id}/evidence`">管理</RouterLink>
          </div>
          <div v-if="caseData.evidence_items.length" class="record-list">
            <div v-for="item in caseData.evidence_items" :key="item.id" class="record-row">
              <strong>{{ item.name }}</strong>
              <span>{{ item.proves || "证明对象待补充" }}</span>
              <StatusPill :label="strengthLabel(item.strength)" />
            </div>
          </div>
          <p v-else class="muted">暂无证据</p>
        </div>

        <div class="surface panel">
          <h2>时效与风险</h2>
          <div v-if="riskItems.length" class="record-list">
            <div v-for="item in riskItems" :key="item.id" class="record-row">
              <strong>{{ candidateTypeLabel(item.candidate_type) }}</strong>
              <span>{{ summarizeContent(item.content_json) }}</span>
            </div>
          </div>
          <p v-else class="muted">暂无时效风险记录</p>
        </div>
      </section>

      <section class="surface panel candidates-panel">
        <div class="panel-title-row">
          <h2>档案候选项</h2>
          <span class="muted">{{ pendingCandidates.length }} 项待处理</span>
        </div>

        <div v-if="caseData.profile_candidates.length" class="candidate-table">
          <div class="candidate-head">
            <span>类型</span>
            <span>内容</span>
            <span>状态</span>
            <span>操作</span>
          </div>
          <div v-for="candidate in caseData.profile_candidates" :key="candidate.id" class="candidate-row">
            <span>{{ candidateTypeLabel(candidate.candidate_type) }}</span>
            <span>{{ summarizeContent(candidate.content_json) }}</span>
            <StatusPill :label="statusLabel(candidate.status)" :tone="candidateTone(candidate.status)" />
            <div class="candidate-actions">
              <el-button
                v-if="candidate.status === 'pending'"
                :icon="Check"
                size="small"
                type="primary"
                :loading="updatingCandidateId === candidate.id"
                @click="updateCandidate(candidate.id, 'confirmed')"
              >
                确认
              </el-button>
              <el-button
                v-if="candidate.status === 'pending'"
                :icon="Close"
                size="small"
                :loading="updatingCandidateId === candidate.id"
                @click="updateCandidate(candidate.id, 'rejected')"
              >
                拒绝
              </el-button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state compact">暂无候选项</div>
      </section>
    </template>

    <el-empty v-else description="案件不存在或无权访问" />
  </section>
</template>

<script setup lang="ts">
import { Check, Close, Document, Files, Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { confirmProfileCandidate, getCase } from "@/api/cases";
import StatusPill from "@/components/StatusPill.vue";
import { useWorkspaceStore } from "@/stores/workspace";
import type { CaseDetailRead, ProfileCandidateRead } from "@/types/api";
import {
  candidateTypeLabel,
  formatDate,
  formatDateTime,
  percent,
  statusLabel,
  strengthLabel
} from "@/utils/format";

const route = useRoute();
const workspace = useWorkspaceStore();

const caseData = ref<CaseDetailRead | null>(null);
const loading = ref(false);
const updatingCandidateId = ref<string | null>(null);
const caseId = computed(() => String(route.params.caseId ?? ""));
const pendingCandidates = computed(
  () => caseData.value?.profile_candidates.filter((item) => item.status === "pending") ?? []
);
const riskItems = computed(
  () =>
    caseData.value?.profile_candidates.filter((item) => {
      const text = JSON.stringify(item.content_json);
      return item.candidate_type === "todo" || item.candidate_type === "timeline" || /时效|风险|期限/.test(text);
    }) ?? []
);

onMounted(loadCase);
watch(caseId, loadCase);

async function loadCase() {
  if (!caseId.value) return;
  loading.value = true;
  try {
    caseData.value = await getCase(caseId.value);
    workspace.setCurrentCaseId(caseData.value.id);
  } catch {
    caseData.value = null;
    workspace.setCurrentCaseId(null);
    ElMessage.error("案件详情加载失败");
  } finally {
    loading.value = false;
  }
}

async function updateCandidate(candidateId: string, status: "confirmed" | "rejected") {
  if (!caseData.value) return;
  updatingCandidateId.value = candidateId;
  try {
    await confirmProfileCandidate(caseData.value.id, candidateId, status);
    ElMessage.success(status === "confirmed" ? "候选项已确认" : "候选项已拒绝");
    await loadCase();
  } catch {
    ElMessage.error("候选项更新失败");
  } finally {
    updatingCandidateId.value = null;
  }
}

function candidateTone(status: string) {
  if (status === "confirmed") return "success";
  if (status === "rejected") return "danger";
  return "warning";
}

function caseStatusTone(status: string) {
  if (status === "open") return "success";
  if (status === "closed") return "neutral";
  return "warning";
}

function summarizeContent(value: ProfileCandidateRead["content_json"]) {
  const labels: Record<string, string> = {
    fact_text: "事实",
    fact: "事实",
    occurred_at: "日期",
    time: "时间",
    name: "名称",
    evidence_type: "类型",
    proves: "证明对象",
    strength: "强度",
    risk: "风险",
    action: "事项"
  };
  return (
    Object.entries(value)
      .filter(([, item]) => item !== null && item !== undefined && item !== "")
      .slice(0, 5)
      .map(([key, item]) => `${labels[key] ?? key}：${formatValue(item)}`)
      .join("；") || "待补充"
  );
}

function formatValue(value: unknown) {
  if (Array.isArray(value)) return value.join("、");
  if (typeof value === "object" && value !== null) return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.case-page {
  max-width: 1280px;
}

.case-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  padding: 16px;
}

.case-summary > div {
  display: grid;
  gap: 6px;
}

.meta-label {
  color: var(--color-muted);
  font-size: 12px;
}

.case-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.panel {
  min-height: 190px;
  padding: 18px;
}

.panel h2 {
  margin: 0 0 12px;
  font-size: 17px;
}

.panel p {
  margin: 0;
  line-height: 1.7;
}

.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-title-row h2 {
  margin: 0;
}

.panel-title-row a {
  color: var(--color-brand);
  font-size: 14px;
  font-weight: 700;
}

.record-list {
  display: grid;
  gap: 10px;
}

.record-row {
  display: grid;
  gap: 6px;
  padding: 10px 0;
  border-top: 1px solid #f2f4f7;
}

.record-row:first-child {
  border-top: 0;
}

.record-row span {
  color: var(--color-muted);
  line-height: 1.5;
}

.candidates-panel {
  padding: 18px;
}

.candidate-table {
  display: grid;
  gap: 0;
  overflow-x: auto;
}

.candidate-head,
.candidate-row {
  display: grid;
  grid-template-columns: 120px minmax(280px, 1fr) 110px 180px;
  gap: 12px;
  align-items: center;
  min-width: 760px;
  padding: 12px 0;
  border-top: 1px solid var(--color-line);
}

.candidate-head {
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 700;
}

.candidate-row > span:nth-child(2) {
  line-height: 1.6;
}

.candidate-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 780px) {
  .case-summary,
  .case-grid {
    grid-template-columns: 1fr;
  }
}
</style>
