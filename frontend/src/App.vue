<template>
  <RouterView v-if="isAuthRoute" />
  <div v-else class="app-shell">
    <aside class="app-sidebar">
      <div class="brand">
        <span class="brand-mark">法</span>
        <div>
          <span class="brand-name">法律咨询辅助</span>
          <span class="brand-subtitle">劳动争议服务台</span>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink v-slot="{ href, navigate }" custom to="/consultation">
          <a :href="href" :class="{ 'nav-active': route.name === 'consultation' }" @click="navigate">
            <el-icon><ChatDotRound /></el-icon>
            <span>法律咨询</span>
          </a>
        </RouterLink>
        <RouterLink v-slot="{ href, navigate }" custom :to="caseDetailLink">
          <a :href="href" :class="{ 'nav-active': route.name === 'cases' || route.name === 'case-detail' }" @click="navigate">
            <el-icon><FolderOpened /></el-icon>
            <span>案件详情</span>
          </a>
        </RouterLink>
        <RouterLink v-slot="{ href, navigate }" custom :to="evidenceLink">
          <a :href="href" :class="{ 'nav-active': route.name === 'evidence' || route.name === 'case-evidence' }" @click="navigate">
            <el-icon><Files /></el-icon>
            <span>证据管理</span>
          </a>
        </RouterLink>
        <RouterLink v-slot="{ href, navigate }" custom :to="documentLink">
          <a :href="href" :class="{ 'nav-active': route.name === 'documents' || route.name === 'document' }" @click="navigate">
            <el-icon><Document /></el-icon>
            <span>文书</span>
          </a>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <RouterLink v-slot="{ href, navigate }" custom to="/profile">
          <a :href="href" class="current-user" :class="{ 'nav-active': route.name === 'profile' }" @click="navigate">
            <img v-if="auth.avatarUrl" class="sidebar-avatar" :src="auth.avatarUrl" alt="" />
            <el-icon v-else><User /></el-icon>
            <span>{{ auth.username || "个人中心" }}</span>
          </a>
        </RouterLink>
        <el-button :icon="SwitchButton" text @click="logout">退出</el-button>
      </div>
    </aside>

    <main class="app-main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Document, Files, FolderOpened, SwitchButton, User } from "@element-plus/icons-vue";
import { computed, watchEffect } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "@/stores/auth";
import { useWorkspaceStore } from "@/stores/workspace";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const workspace = useWorkspaceStore();

const isAuthRoute = computed(() => route.name === "login" || route.name === "register");

const activeCaseId = computed(() => {
  const routeCaseId = route.params.caseId;
  if (typeof routeCaseId === "string") return routeCaseId;
  const queryCaseId = route.query.case_id;
  if (typeof queryCaseId === "string") return queryCaseId;
  return workspace.currentCaseId;
});

const caseDetailLink = "/cases";
const evidenceLink = computed(() => (activeCaseId.value ? `/cases/${activeCaseId.value}/evidence` : "/evidence"));
const documentLink = computed(() => {
  if (workspace.currentDocumentId) return `/documents/${workspace.currentDocumentId}`;
  return activeCaseId.value ? `/documents?case_id=${activeCaseId.value}` : "/documents";
});

watchEffect(() => {
  if (typeof route.params.caseId === "string") {
    workspace.setCurrentCaseId(route.params.caseId);
  }
  if (typeof route.query.case_id === "string") {
    workspace.setCurrentCaseId(route.query.case_id);
  }
  if (typeof route.params.documentId === "string") {
    workspace.setCurrentDocumentId(route.params.documentId);
  }
});

function logout() {
  auth.logout();
  workspace.setCurrentCaseId(null);
  workspace.setCurrentDocumentId(null);
  router.push("/login");
}
</script>
