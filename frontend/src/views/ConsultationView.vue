<template>
  <section class="page consultation-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">法律咨询</h1>
        <p class="page-caption">劳动争议咨询工作台</p>
      </div>
      <div class="toolbar">
        <StatusPill :label="stageLabel(currentStage)" :tone="statusTone" />
        <el-button :icon="Plus" @click="startCase">新建案件</el-button>
      </div>
    </header>

    <section class="consultation-workbench">
      <aside class="surface case-rail">
        <div class="rail-header">
          <h2>案件</h2>
          <el-button :icon="Refresh" circle text :loading="loadingCases" @click="loadCases" />
        </div>

        <div v-if="cases.length > 0" class="case-list">
          <button
            v-for="item in cases"
            :key="item.id"
            class="case-item"
            type="button"
            :data-active="item.id === currentCaseId"
            @click="selectCase(item.id)"
          >
            <span class="case-item-title">{{ item.title }}</span>
            <span class="case-item-meta">
              {{ item.cause || "待识别案由" }} · {{ formatDateTime(item.updated_at) }}
            </span>
          </button>
        </div>
        <div v-else class="empty-state compact">暂无案件</div>
      </aside>

      <section class="chat-column">
        <div class="surface current-case-bar">
          <div>
            <span class="bar-label">当前案件</span>
            <strong>{{ currentCase?.title || "首次发送后自动创建" }}</strong>
          </div>
          <div class="bar-actions" v-if="currentCaseId">
            <RouterLink :to="`/cases/${currentCaseId}`">详情</RouterLink>
            <RouterLink :to="`/cases/${currentCaseId}/evidence`">证据</RouterLink>
            <RouterLink :to="`/documents?case_id=${currentCaseId}`">文书</RouterLink>
          </div>
        </div>

        <div ref="messageListRef" class="message-list surface">
          <article v-for="message in messages" :key="message.id" class="message" :data-role="message.role">
            <div class="message-role">{{ roleLabel[message.role] }}</div>
            <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(message.content)" />
            <p v-else>{{ message.content }}</p>
          </article>
          <div v-if="messages.length === 0" class="empty-state">暂无对话</div>
        </div>

        <form class="composer surface" @submit.prevent="send">
          <el-input
            v-model="draft"
            type="textarea"
            :rows="5"
            resize="none"
            placeholder="输入劳动争议事实、时间、诉求或证据情况"
          />
          <div class="composer-actions">
            <span class="muted">{{ statusMessage }}</span>
            <el-button :icon="Promotion" type="primary" native-type="submit" :loading="sending">发送</el-button>
          </div>
        </form>
      </section>

      <aside class="analysis-pane surface">
        <div class="analysis-header">
          <h2>结构化分析</h2>
          <StatusPill :label="analysis?.cause || '待分析'" />
        </div>

        <template v-if="analysis">
          <section v-if="analysis.needs_more_info || analysis.questions.length" class="analysis-section attention">
            <h3>追问问题</h3>
            <ul class="plain-list">
              <li v-for="question in analysis.questions" :key="question">{{ question }}</li>
            </ul>
          </section>

          <section class="analysis-section">
            <h3>案情摘要</h3>
            <p>{{ analysis.summary }}</p>
          </section>

          <section v-if="analysis.issues.length" class="analysis-section">
            <h3>争议焦点</h3>
            <div v-for="issue in analysis.issues" :key="issue.issue" class="divided-item">
              <strong>{{ issue.issue }}</strong>
              <p>{{ issue.burden_of_proof }}</p>
              <p class="muted">{{ issue.current_evidence_status }}</p>
            </div>
          </section>

          <section v-if="analysis.legal_basis.length" class="analysis-section">
            <h3>法律依据</h3>
            <div v-for="item in analysis.legal_basis" :key="item.source_id" class="divided-item">
              <strong>{{ item.title }}{{ item.article || "" }}</strong>
              <p>{{ item.summary }}</p>
              <span class="source-id">{{ item.source_id }}</span>
            </div>
          </section>

          <section v-if="analysis.precedents.length" class="analysis-section">
            <h3>类案参考</h3>
            <div v-for="item in analysis.precedents" :key="item.source_id" class="divided-item">
              <strong>{{ item.title }}</strong>
              <p>{{ item.summary }}</p>
              <p v-if="item.similarities.length" class="muted">相似点：{{ item.similarities.join("；") }}</p>
            </div>
          </section>

          <section v-if="analysis.evidence_gaps.length" class="analysis-section">
            <h3>证据缺口</h3>
            <ul class="plain-list">
              <li v-for="item in analysis.evidence_gaps" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section v-if="analysis.strategy_steps.length || analysis.strategy.length" class="analysis-section">
            <h3>处理路径</h3>
            <div v-for="item in analysis.strategy_steps" :key="item.step" class="divided-item">
              <strong>{{ item.step }}</strong>
              <p>{{ item.action }}</p>
              <p v-if="item.materials.length" class="muted">材料：{{ item.materials.join("、") }}</p>
            </div>
            <ul v-if="!analysis.strategy_steps.length" class="plain-list">
              <li v-for="item in analysis.strategy" :key="item">{{ item }}</li>
            </ul>
          </section>

          <section v-if="analysis.deadline_risk" class="analysis-section risk">
            <h3>时效风险</h3>
            <p>{{ analysis.deadline_risk }}</p>
          </section>

          <section v-if="analysis.profile_candidates.length" class="analysis-section">
            <h3>档案候选项</h3>
            <div v-for="(item, index) in analysis.profile_candidates" :key="index" class="divided-item">
              <strong>{{ candidateLabel(item.candidate_type) }}</strong>
              <p>{{ summarizeContent(item.content_json) }}</p>
            </div>
          </section>

          <section class="analysis-section notice">
            <p>{{ analysis.safety_notice }}</p>
          </section>
        </template>

        <div v-else class="empty-state compact">等待咨询输入</div>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { Plus, Promotion, Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import MarkdownIt from "markdown-it";
import { computed, nextTick, onMounted, ref } from "vue";

import { createCase, listCases } from "@/api/cases";
import StatusPill from "@/components/StatusPill.vue";
import { useWorkspaceStore } from "@/stores/workspace";
import type { AgentAnalyzeResponse, CaseRead, ChatMessage, ChatStatusEvent } from "@/types/api";
import { candidateTypeLabel, formatDateTime } from "@/utils/format";

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });
const workspace = useWorkspaceStore();

const draft = ref("");
const cases = ref<CaseRead[]>([]);
const messagesByCase = ref<Record<string, ChatMessage[]>>({});
const transientMessages = ref<ChatMessage[]>([]);
const analysis = ref<AgentAnalyzeResponse | null>(null);
const loadingCases = ref(false);
const sending = ref(false);
const currentStage = ref("ready");
const statusMessage = ref("就绪");
const messageListRef = ref<HTMLElement | null>(null);

const roleLabel: Record<ChatMessage["role"], string> = {
  user: "用户",
  assistant: "系统",
  system: "状态"
};

const currentCaseId = computed(() => workspace.currentCaseId);
const currentCase = computed(() => cases.value.find((item) => item.id === currentCaseId.value) ?? null);
const messages = computed(() => {
  if (!currentCaseId.value) return transientMessages.value;
  return messagesByCase.value[currentCaseId.value] ?? [];
});
const statusTone = computed(() => {
  if (currentStage.value === "algorithm_degraded") return "warning";
  if (currentStage.value === "error") return "danger";
  if (currentStage.value === "final") return "success";
  return "neutral";
});
const apiBaseUrl = computed(() => {
  const configured = import.meta.env.VITE_API_BASE_URL as string | undefined;
  const fallback =
    typeof window === "undefined"
      ? "http://127.0.0.1:8000"
      : `${window.location.protocol}//${window.location.hostname}:8000`;
  return (configured ?? fallback).replace(/\/$/, "");
});

onMounted(async () => {
  await loadCases();
});

async function loadCases() {
  loadingCases.value = true;
  try {
    cases.value = await listCases();
    if (!workspace.currentCaseId && cases.value[0]) {
      workspace.setCurrentCaseId(cases.value[0].id);
    }
  } catch {
    ElMessage.error("案件列表加载失败");
  } finally {
    loadingCases.value = false;
  }
}

async function startCase() {
  try {
    const item = await createCase({
      title: `劳动争议咨询 ${new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
      }).format(new Date())}`,
      domain: "labor_dispute"
    });
    cases.value = [item, ...cases.value];
    workspace.setCurrentCaseId(item.id);
    analysis.value = null;
    ElMessage.success("已创建新案件");
  } catch {
    ElMessage.error("新建案件失败");
  }
}

function selectCase(caseId: string) {
  workspace.setCurrentCaseId(caseId);
  analysis.value = null;
  statusMessage.value = "就绪";
  currentStage.value = "ready";
}

async function send() {
  const content = draft.value.trim();
  if (!content || sending.value) return;

  pushMessage({
    id: crypto.randomUUID(),
    role: "user",
    content
  });
  draft.value = "";
  sending.value = true;
  currentStage.value = "sent";
  statusMessage.value = "已发送，等待服务端接收";
  await scrollToBottom();

  try {
    const response = await fetch(`${apiBaseUrl.value}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("auth_token") ?? ""}`
      },
      body: JSON.stringify({
        case_id: currentCaseId.value,
        message: content
      })
    });

    if (!response.ok || response.body === null) {
      throw new Error("chat stream failed");
    }

    await readSseStream(response.body);
    await loadCases();
  } catch {
    currentStage.value = "error";
    statusMessage.value = "发送失败";
    ElMessage.error("发送失败，请确认服务已启动");
    pushMessage({
      id: crypto.randomUUID(),
      role: "system",
      content: "发送失败，请确认服务已启动。"
    });
  } finally {
    sending.value = false;
    if (currentStage.value !== "error") {
      statusMessage.value = "就绪";
    }
    await scrollToBottom();
  }
}

async function readSseStream(body: ReadableStream<Uint8Array>) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      await handleSseBlock(block);
    }
  }

  if (buffer.trim()) {
    await handleSseBlock(buffer);
  }
}

async function handleSseBlock(block: string) {
  const lines = block.split(/\r?\n/);
  const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim() || "message";
  const dataText = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .join("\n");

  if (!dataText) return;

  let data: unknown;
  try {
    data = JSON.parse(dataText);
  } catch {
    return;
  }

  if (event === "status") {
    const status = data as ChatStatusEvent;
    if (status.case_id) adoptCase(status.case_id);
    currentStage.value = status.stage ?? "processing";
    statusMessage.value = status.message ?? stageLabel(status.stage);
    return;
  }

  if (event === "final") {
    const finalResult = normalizeAnalysis(data as Partial<AgentAnalyzeResponse>);
    adoptCase(finalResult.case_id);
    analysis.value = finalResult;
    currentStage.value = "final";
    statusMessage.value = "分析完成";
    pushMessage({
      id: crypto.randomUUID(),
      role: "assistant",
      content: finalResult.answer || finalResult.summary || "分析完成。"
    });
    await scrollToBottom();
  }
}

function adoptCase(caseId: string) {
  if (!caseId) return;
  const transient = transientMessages.value;
  workspace.setCurrentCaseId(caseId);
  if (transient.length > 0) {
    const existing = messagesByCase.value[caseId] ?? [];
    messagesByCase.value = {
      ...messagesByCase.value,
      [caseId]: [...existing, ...transient]
    };
    transientMessages.value = [];
  }
}

function pushMessage(message: ChatMessage) {
  if (!currentCaseId.value) {
    transientMessages.value = [...transientMessages.value, message];
    return;
  }

  const bucket = messagesByCase.value[currentCaseId.value] ?? [];
  messagesByCase.value = {
    ...messagesByCase.value,
    [currentCaseId.value]: [...bucket, message]
  };
}

async function scrollToBottom() {
  await nextTick();
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
}

function normalizeAnalysis(value: Partial<AgentAnalyzeResponse>): AgentAnalyzeResponse {
  return {
    trace_id: value.trace_id ?? null,
    case_id: value.case_id ?? currentCaseId.value ?? "",
    summary: value.summary ?? "",
    cause: value.cause ?? null,
    confidence: value.confidence ?? null,
    needs_more_info: Boolean(value.needs_more_info),
    questions: value.questions ?? [],
    intake: value.intake ?? null,
    cause_result: value.cause_result ?? null,
    issues: value.issues ?? [],
    evidence_analysis: value.evidence_analysis ?? { evidence_items: [], missing_evidence: [] },
    evidence_gaps: value.evidence_gaps ?? [],
    strategy_steps: value.strategy_steps ?? [],
    strategy: value.strategy ?? [],
    deadline: value.deadline ?? null,
    deadline_risk: value.deadline_risk ?? null,
    legal_basis: value.legal_basis ?? [],
    precedents: value.precedents ?? [],
    profile_candidates: value.profile_candidates ?? [],
    arbitration_document: value.arbitration_document ?? null,
    answer: value.answer ?? "",
    safety_notice: value.safety_notice ?? "以上内容仅供参考，不能替代专业法律意见。",
    risk_flags: value.risk_flags ?? [],
    node_trace: value.node_trace ?? [],
    degraded: value.degraded,
    error: value.error
  };
}

function renderMarkdown(value: string) {
  return md.render(value);
}

function stageLabel(stage?: string) {
  const labels: Record<string, string> = {
    ready: "就绪",
    sent: "已发送",
    received: "已接收",
    algorithm_analyzing: "材料分析中",
    algorithm_degraded: "基础模式",
    final: "已完成",
    error: "失败",
    processing: "处理中"
  };
  return labels[stage ?? ""] ?? "处理中";
}

function candidateLabel(type: string) {
  return candidateTypeLabel(type);
}

function summarizeContent(value: Record<string, unknown>) {
  const lines = Object.entries(value)
    .filter(([, item]) => item !== null && item !== undefined && item !== "")
    .slice(0, 4)
    .map(([key, item]) => `${fieldLabel(key)}：${formatValue(item)}`);
  return lines.join("；") || "待补充";
}

function fieldLabel(key: string) {
  const labels: Record<string, string> = {
    fact_text: "事实",
    fact: "事实",
    occurred_at: "日期",
    time: "时间",
    name: "名称",
    evidence_type: "类型",
    proves: "证明对象",
    risk: "风险",
    strength: "强度",
    action: "事项"
  };
  return labels[key] ?? key;
}

function formatValue(value: unknown) {
  if (Array.isArray(value)) return value.join("、");
  if (typeof value === "object" && value !== null) return JSON.stringify(value);
  return String(value);
}
</script>

<style scoped>
.consultation-page {
  max-width: 1440px;
  min-height: calc(100vh - 56px);
}

.consultation-workbench {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 360px;
  gap: 16px;
  min-height: 0;
}

.case-rail,
.analysis-pane {
  min-height: 0;
  padding: 16px;
}

.rail-header,
.analysis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.rail-header h2,
.analysis-header h2 {
  margin: 0;
  font-size: 16px;
}

.case-list {
  display: grid;
  gap: 8px;
  max-height: calc(100vh - 180px);
  overflow: auto;
}

.case-item {
  display: grid;
  gap: 6px;
  width: 100%;
  min-height: 68px;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--color-strong);
  background: #f8fbff;
  text-align: left;
  cursor: pointer;
}

.case-item[data-active="true"] {
  border-color: rgba(22, 119, 255, 0.35);
  color: var(--color-brand-strong);
  background: var(--color-brand-soft);
}

.case-item-title {
  overflow: hidden;
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-item-meta {
  color: var(--color-muted);
  font-size: 12px;
}

.chat-column {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  gap: 16px;
  min-height: calc(100vh - 128px);
}

.current-case-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 56px;
  padding: 12px 16px;
}

.bar-label {
  display: block;
  margin-bottom: 4px;
  color: var(--color-muted);
  font-size: 12px;
}

.bar-actions {
  display: flex;
  gap: 10px;
  color: var(--color-brand);
  font-size: 14px;
  font-weight: 700;
}

.message-list {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 420px;
  padding: 18px;
  overflow: auto;
}

.message {
  max-width: 760px;
  padding: 14px 16px;
  border-radius: var(--radius);
  background: #f3f7fc;
}

.message[data-role="user"] {
  justify-self: end;
  color: #ffffff;
  background: var(--color-brand);
}

.message[data-role="system"] {
  color: #9a6700;
  background: var(--color-amber-soft);
}

.message-role {
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 700;
}

.message p,
.analysis-section p {
  margin: 0;
  line-height: 1.6;
}

.composer {
  display: grid;
  gap: 12px;
  padding: 16px;
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.analysis-pane {
  align-content: start;
  display: grid;
  max-height: calc(100vh - 104px);
  overflow: auto;
}

.analysis-section {
  padding: 14px 0;
  border-top: 1px solid var(--color-line);
}

.analysis-section h3 {
  margin: 0 0 10px;
  color: var(--color-strong);
  font-size: 14px;
}

.analysis-section.attention {
  color: #9a6700;
}

.analysis-section.risk,
.analysis-section.notice {
  color: #9a6700;
  background: linear-gradient(90deg, rgba(255, 245, 220, 0.92), rgba(255, 255, 255, 0));
}

.divided-item {
  display: grid;
  gap: 6px;
  padding: 10px 0;
  border-top: 1px solid var(--color-line);
}

.divided-item:first-of-type {
  border-top: 0;
}

.divided-item strong {
  color: var(--color-strong);
  font-size: 14px;
}

.source-id {
  color: var(--color-muted);
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
  font-size: 12px;
}

.plain-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
}

.markdown-body :deep(p) {
  margin: 0 0 8px;
  line-height: 1.7;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 18px;
}

@media (max-width: 1180px) {
  .consultation-workbench {
    grid-template-columns: 240px minmax(0, 1fr);
  }

  .analysis-pane {
    grid-column: 1 / -1;
    max-height: none;
  }
}

@media (max-width: 780px) {
  .consultation-page {
    min-height: auto;
  }

  .consultation-workbench,
  .chat-column {
    grid-template-columns: 1fr;
  }

  .chat-column {
    min-height: 0;
  }

  .case-list {
    max-height: 260px;
  }

  .current-case-bar,
  .composer-actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
