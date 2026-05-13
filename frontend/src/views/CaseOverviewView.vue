<template>
  <section class="page cases-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">案件详情</h1>
        <p class="page-caption">选择一个案件查看详情</p>
      </div>
      <div class="toolbar">
        <el-button :icon="Refresh" :loading="loading" @click="loadCases">刷新</el-button>
        <RouterLink to="/consultation">
          <el-button :icon="ChatDotRound" type="primary">去咨询</el-button>
        </RouterLink>
      </div>
    </header>

    <section class="surface cases-panel">
      <el-skeleton v-if="loading" :rows="6" animated />

      <div v-else-if="cases.length" class="case-list">
        <RouterLink v-for="item in cases" :key="item.id" :to="`/cases/${item.id}`" class="case-row">
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.summary || "暂无案情摘要" }}</span>
          </div>
          <div class="case-row-meta">
            <StatusPill :label="item.cause || '待识别案由'" />
            <span>{{ formatDateTime(item.updated_at) }}</span>
          </div>
        </RouterLink>
      </div>

      <div v-else class="empty-state">
        暂无案件。可以先进入法律咨询，发送问题后系统会自动创建案件。
        <div class="empty-action">
          <RouterLink to="/consultation">
            <el-button :icon="ChatDotRound" type="primary">开始咨询</el-button>
          </RouterLink>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { ChatDotRound, Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { onMounted, ref } from "vue";

import { listCases } from "@/api/cases";
import StatusPill from "@/components/StatusPill.vue";
import { useWorkspaceStore } from "@/stores/workspace";
import type { CaseRead } from "@/types/api";
import { formatDateTime } from "@/utils/format";

const workspace = useWorkspaceStore();
const cases = ref<CaseRead[]>([]);
const loading = ref(false);

onMounted(loadCases);

async function loadCases() {
  loading.value = true;
  try {
    cases.value = await listCases();
    if (workspace.currentCaseId && !cases.value.some((item) => item.id === workspace.currentCaseId)) {
      workspace.setCurrentCaseId(cases.value[0]?.id ?? null);
    }
  } catch {
    ElMessage.error("案件列表加载失败");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.cases-page {
  max-width: 960px;
}

.cases-panel {
  min-height: 420px;
  padding: 18px;
}

.case-list {
  display: grid;
}

.case-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 82px;
  padding: 14px 0;
  border-top: 1px solid var(--color-line);
}

.case-row:first-child {
  border-top: 0;
}

.case-row > div:first-child {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.case-row strong {
  overflow: hidden;
  color: var(--color-strong);
  font-size: 16px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-row span {
  color: var(--color-muted);
  line-height: 1.6;
}

.case-row-meta {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 160px;
  color: var(--color-muted);
  font-size: 13px;
}

.empty-action {
  margin-top: 18px;
}

@media (max-width: 780px) {
  .case-row {
    align-items: stretch;
    flex-direction: column;
  }

  .case-row-meta {
    justify-items: start;
  }
}
</style>
