<template>
  <section class="page evidence-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">证据管理</h1>
        <p class="page-caption">{{ selectedCase?.title || "选择案件后管理证据" }}</p>
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
        <el-button :icon="Refresh" :loading="loadingEvidence" @click="loadEvidence">刷新</el-button>
      </div>
    </header>

    <section class="surface upload-panel">
      <div class="upload-grid">
        <el-form label-position="top">
          <el-form-item label="证据名称">
            <el-input v-model="uploadName" placeholder="劳动合同、工资流水、聊天记录等" />
          </el-form-item>
          <el-form-item label="证据类型">
            <el-select v-model="uploadType" clearable placeholder="选择类型">
              <el-option label="劳动合同" value="contract" />
              <el-option label="工资流水" value="payroll" />
              <el-option label="考勤记录" value="attendance" />
              <el-option label="聊天记录" value="chat_record" />
              <el-option label="解除通知" value="termination_notice" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
        </el-form>
        <div class="file-box">
          <input type="file" @change="handleFileChange" />
          <span>{{ selectedFile?.name || "未选择文件" }}</span>
        </div>
        <div class="upload-actions">
          <el-button
            :icon="Upload"
            type="primary"
            :disabled="!selectedCaseId || !selectedFile"
            :loading="uploading"
            @click="submitUpload"
          >
            上传证据
          </el-button>
        </div>
      </div>
    </section>

    <section class="surface evidence-list">
      <div class="list-header">
        <h2>证据列表</h2>
        <span class="muted">{{ evidenceItems.length }} 项</span>
      </div>

      <div v-if="loadingEvidence" class="list-loading">
        <el-skeleton :rows="6" animated />
      </div>

      <div v-else-if="evidenceItems.length" class="evidence-table">
        <div class="evidence-head">
          <span>名称</span>
          <span>证明对象</span>
          <span>强度</span>
          <span>解析状态</span>
          <span>操作</span>
        </div>

        <div v-for="item in evidenceItems" :key="item.id" class="evidence-row">
          <div>
            <strong>{{ item.name }}</strong>
            <span>{{ item.evidence_type || "未分类" }} · {{ formatDateTime(item.created_at) }}</span>
          </div>
          <p>{{ item.proves || "待分析" }}</p>
          <StatusPill :label="strengthLabel(item.strength)" :tone="strengthTone(item.strength)" />
          <div class="task-cell">
            <StatusPill :label="taskStatus(item)" :tone="taskTone(item)" />
            <span v-if="tasksByEvidenceId[item.id]?.error_message" class="task-error">
              {{ tasksByEvidenceId[item.id]?.error_message }}
            </span>
          </div>
          <div class="row-actions">
            <el-button
              :icon="DataAnalysis"
              size="small"
              :loading="analyzingEvidenceId === item.id"
              @click="startAnalysis(item.id)"
            >
              分析
            </el-button>
            <el-button v-if="item.file_url" :icon="Link" size="small" text @click="openFile(item.file_url)">
              文件
            </el-button>
          </div>
          <div v-if="item.risk || item.extracted_text" class="evidence-extra">
            <p v-if="item.risk"><strong>风险：</strong>{{ item.risk }}</p>
            <p v-if="item.extracted_text"><strong>解析文本：</strong>{{ item.extracted_text }}</p>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">暂无证据</div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { DataAnalysis, Link, Refresh, Upload } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { listCases } from "@/api/cases";
import { analyzeEvidence, getTask, listCaseEvidence, uploadEvidence } from "@/api/evidence";
import StatusPill from "@/components/StatusPill.vue";
import { useWorkspaceStore } from "@/stores/workspace";
import type { CaseRead, EvidenceItemRead, TaskRead } from "@/types/api";
import { formatDateTime, strengthLabel } from "@/utils/format";

const route = useRoute();
const workspace = useWorkspaceStore();

const cases = ref<CaseRead[]>([]);
const evidenceItems = ref<EvidenceItemRead[]>([]);
const selectedCaseId = ref<string | null>(null);
const selectedFile = ref<File | null>(null);
const uploadName = ref("");
const uploadType = ref("");
const loadingEvidence = ref(false);
const uploading = ref(false);
const analyzingEvidenceId = ref<string | null>(null);
const tasksByEvidenceId = ref<Record<string, TaskRead>>({});
const selectedCase = computed(() => cases.value.find((item) => item.id === selectedCaseId.value) ?? null);

onMounted(async () => {
  await loadCasesForSelect();
});

watch(
  () => route.params.caseId,
  (value) => {
    if (typeof value === "string") {
      selectedCaseId.value = value;
      workspace.setCurrentCaseId(value);
      void loadEvidence();
    }
  }
);

async function loadCasesForSelect() {
  try {
    cases.value = await listCases();
    const routeCaseId = typeof route.params.caseId === "string" ? route.params.caseId : null;
    selectedCaseId.value = routeCaseId ?? workspace.currentCaseId ?? cases.value[0]?.id ?? null;
    if (selectedCaseId.value) {
      workspace.setCurrentCaseId(selectedCaseId.value);
      await loadEvidence();
    }
  } catch {
    ElMessage.error("案件列表加载失败");
  }
}

function selectCase(caseId: string) {
  selectedCaseId.value = caseId;
  workspace.setCurrentCaseId(caseId);
  void loadEvidence();
}

async function loadEvidence() {
  if (!selectedCaseId.value) return;
  loadingEvidence.value = true;
  try {
    evidenceItems.value = await listCaseEvidence(selectedCaseId.value);
  } catch {
    ElMessage.error("证据列表加载失败");
  } finally {
    loadingEvidence.value = false;
  }
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
  if (!uploadName.value && selectedFile.value) {
    uploadName.value = selectedFile.value.name.replace(/\.[^.]+$/, "");
  }
}

async function submitUpload() {
  if (!selectedCaseId.value || !selectedFile.value) return;
  uploading.value = true;
  try {
    await uploadEvidence({
      caseId: selectedCaseId.value,
      file: selectedFile.value,
      name: uploadName.value,
      evidenceType: uploadType.value || undefined
    });
    ElMessage.success("证据已上传");
    selectedFile.value = null;
    uploadName.value = "";
    uploadType.value = "";
    await loadEvidence();
  } catch {
    ElMessage.error("上传失败，请确认对象存储服务已启动");
  } finally {
    uploading.value = false;
  }
}

async function startAnalysis(evidenceId: string) {
  analyzingEvidenceId.value = evidenceId;
  try {
    const response = await analyzeEvidence(evidenceId);
    ElMessage.success("已创建证据分析任务");
    await pollTask(response.task_id, evidenceId);
  } catch {
    ElMessage.error("分析任务创建失败，请确认 Redis 与 RabbitMQ 已启动");
  } finally {
    analyzingEvidenceId.value = null;
  }
}

async function pollTask(taskId: string, evidenceId: string, attempt = 0) {
  try {
    const task = await getTask(taskId);
    tasksByEvidenceId.value = {
      ...tasksByEvidenceId.value,
      [evidenceId]: task
    };
    if (!["completed", "failed"].includes(task.status) && attempt < 10) {
      window.setTimeout(() => void pollTask(taskId, evidenceId, attempt + 1), 2000);
    }
  } catch {
    ElMessage.warning("任务状态暂时不可用");
  }
}

function taskStatus(item: EvidenceItemRead) {
  const task = tasksByEvidenceId.value[item.id];
  if (task) return `${task.status} ${task.progress}%`;
  if (item.extracted_text || item.proves || item.risk) return "已有结果";
  return "未分析";
}

function taskTone(item: EvidenceItemRead) {
  const task = tasksByEvidenceId.value[item.id];
  if (task?.status === "completed" || item.proves) return "success";
  if (task?.status === "failed") return "danger";
  if (task) return "warning";
  return "neutral";
}

function strengthTone(strength?: string | null) {
  if (strength === "high") return "success";
  if (strength === "medium") return "warning";
  if (strength === "low") return "danger";
  return "neutral";
}

function openFile(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}
</script>

<style scoped>
.evidence-page {
  max-width: 1280px;
}

.case-select {
  width: min(320px, 100%);
}

.upload-panel {
  padding: 18px;
}

.upload-grid {
  display: grid;
  grid-template-columns: minmax(260px, 480px) minmax(220px, 1fr) auto;
  gap: 18px;
  align-items: end;
}

.file-box {
  display: grid;
  gap: 8px;
  align-content: center;
  min-height: 84px;
  padding: 12px;
  border: 1px dashed #b8c0cc;
  border-radius: var(--radius);
  background: #f8fbff;
}

.file-box span {
  color: var(--color-muted);
  font-size: 13px;
}

.upload-actions {
  display: flex;
  align-items: center;
  min-height: 84px;
}

.evidence-list {
  min-height: 420px;
  padding: 18px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.list-header h2 {
  margin: 0;
  font-size: 17px;
}

.list-loading {
  padding-top: 12px;
}

.evidence-table {
  display: grid;
  overflow-x: auto;
}

.evidence-head,
.evidence-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.2fr) minmax(220px, 1fr) 90px 150px 150px;
  gap: 14px;
  align-items: start;
  min-width: 920px;
  padding: 14px 0;
  border-top: 1px solid var(--color-line);
}

.evidence-head {
  color: var(--color-muted);
  font-size: 12px;
  font-weight: 700;
}

.evidence-row > div:first-child {
  display: grid;
  gap: 6px;
}

.evidence-row span,
.evidence-row p {
  margin: 0;
  color: var(--color-muted);
  line-height: 1.6;
}

.evidence-row strong {
  color: var(--color-strong);
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-cell {
  display: grid;
  gap: 6px;
}

.task-error {
  color: #bd3324;
  font-size: 12px;
  line-height: 1.5;
}

.evidence-extra {
  grid-column: 1 / -1;
  display: grid;
  gap: 6px;
  padding: 10px 12px;
  border-left: 3px solid var(--color-mint);
  background: #f8fbff;
}

@media (max-width: 900px) {
  .upload-grid {
    grid-template-columns: 1fr;
  }

  .upload-actions {
    min-height: 0;
  }
}
</style>
