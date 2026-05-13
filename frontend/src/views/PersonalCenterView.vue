<template>
  <section class="page profile-page">
    <header class="page-header">
      <div>
        <h1 class="page-title">个人中心</h1>
        <p class="page-caption">账号状态与当前工作区</p>
      </div>
      <div class="toolbar">
        <el-button :icon="Refresh" :loading="loadingCases" @click="loadCases">刷新</el-button>
        <el-button :icon="SwitchButton" type="danger" plain @click="logout">退出登录</el-button>
      </div>
    </header>

    <section class="profile-grid">
      <div class="surface account-panel">
        <div class="avatar-block">
          <button class="avatar" type="button" @click="avatarInputRef?.click()">
            <img v-if="auth.avatarUrl" :src="auth.avatarUrl" alt="" />
            <el-icon v-else><User /></el-icon>
          </button>
          <input
            ref="avatarInputRef"
            class="avatar-input"
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            @change="handleAvatarChange"
          />
          <el-button :icon="Upload" size="small" :loading="uploadingAvatar" @click="avatarInputRef?.click()">
            上传头像
          </el-button>
        </div>
        <div>
          <h2>{{ auth.username || "未命名用户" }}</h2>
          <p class="signature-text">{{ auth.signature || "还没有个性签名" }}</p>
        </div>
        <div class="account-meta">
          <div>
            <span>注册时间</span>
            <strong>{{ formatDateTime(auth.createdAt) }}</strong>
          </div>
          <div>
            <span>登录状态</span>
            <StatusPill :label="auth.token ? '已登录' : '未登录'" :tone="auth.token ? 'success' : 'danger'" />
          </div>
        </div>
      </div>

      <div class="surface workspace-panel">
        <h2>个性签名</h2>
        <el-input
          v-model="signatureDraft"
          type="textarea"
          :rows="4"
          maxlength="255"
          show-word-limit
          resize="none"
          placeholder="写一句给自己的工作提示"
        />
        <div class="workspace-actions">
          <el-button :icon="EditPen" type="primary" :loading="savingSignature" @click="saveSignature">
            保存签名
          </el-button>
        </div>
      </div>
    </section>

    <section class="surface workspace-wide-panel">
      <div>
        <h2>当前工作区</h2>
        <div class="workspace-list">
          <div>
            <span>当前案件</span>
            <RouterLink v-if="currentCase" :to="`/cases/${currentCase.id}`">{{ currentCase.title }}</RouterLink>
            <strong v-else>未选择</strong>
          </div>
          <div>
            <span>当前文书</span>
            <RouterLink v-if="workspace.currentDocumentId" :to="`/documents/${workspace.currentDocumentId}`">
              {{ truncateMiddle(workspace.currentDocumentId, 18) }}
            </RouterLink>
            <strong v-else>未生成</strong>
          </div>
        </div>
        <div class="workspace-actions">
          <RouterLink to="/consultation">
            <el-button :icon="ChatDotRound" type="primary">继续咨询</el-button>
          </RouterLink>
          <el-button :icon="Close" @click="clearWorkspace">清除当前选择</el-button>
        </div>
      </div>
    </section>

    <section class="surface stats-panel">
      <div class="stat-item">
        <span>案件总数</span>
        <strong>{{ cases.length }}</strong>
      </div>
      <div class="stat-item">
        <span>进行中</span>
        <strong>{{ openCases.length }}</strong>
      </div>
      <div class="stat-item">
        <span>已识别案由</span>
        <strong>{{ casesWithCause.length }}</strong>
      </div>
      <div class="stat-item">
        <span>最近更新</span>
        <strong>{{ formatDateTime(cases[0]?.updated_at) }}</strong>
      </div>
    </section>

    <section class="surface recent-panel">
      <div class="panel-title-row">
        <h2>最近案件</h2>
        <RouterLink to="/consultation">进入咨询</RouterLink>
      </div>

      <div v-if="loadingCases" class="recent-loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="cases.length" class="recent-list">
        <RouterLink v-for="item in cases.slice(0, 6)" :key="item.id" :to="`/cases/${item.id}`" class="recent-item">
          <div>
            <strong>{{ item.title }}</strong>
            <span>{{ item.cause || "待识别案由" }}</span>
          </div>
          <span>{{ formatDateTime(item.updated_at) }}</span>
        </RouterLink>
      </div>

      <div v-else class="empty-state compact">暂无案件</div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { ChatDotRound, Close, EditPen, Refresh, SwitchButton, Upload, User } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { listCases } from "@/api/cases";
import { getMe, updateSignature, uploadAvatar } from "@/api/profile";
import StatusPill from "@/components/StatusPill.vue";
import { useAuthStore } from "@/stores/auth";
import { useWorkspaceStore } from "@/stores/workspace";
import type { CaseRead } from "@/types/api";
import { formatDateTime, truncateMiddle } from "@/utils/format";

const router = useRouter();
const auth = useAuthStore();
const workspace = useWorkspaceStore();

const cases = ref<CaseRead[]>([]);
const loadingCases = ref(false);
const savingSignature = ref(false);
const uploadingAvatar = ref(false);
const signatureDraft = ref(auth.signature ?? "");
const avatarInputRef = ref<HTMLInputElement | null>(null);
const currentCase = computed(() => cases.value.find((item) => item.id === workspace.currentCaseId) ?? null);
const openCases = computed(() => cases.value.filter((item) => item.status === "open"));
const casesWithCause = computed(() => cases.value.filter((item) => Boolean(item.cause)));

onMounted(async () => {
  await Promise.all([loadProfile(), loadCases()]);
});

async function loadProfile() {
  try {
    applyProfile(await getMe());
  } catch {
    ElMessage.warning("个人资料暂时无法刷新");
  }
}

async function loadCases() {
  loadingCases.value = true;
  try {
    cases.value = await listCases();
  } catch {
    ElMessage.error("案件概览加载失败");
  } finally {
    loadingCases.value = false;
  }
}

async function clearWorkspace() {
  workspace.setCurrentCaseId(null);
  workspace.setCurrentDocumentId(null);
  ElMessage.success("当前选择已清除");
}

async function saveSignature() {
  savingSignature.value = true;
  try {
    const value = signatureDraft.value.trim();
    applyProfile(await updateSignature(value || null));
    ElMessage.success("个性签名已保存");
  } catch {
    ElMessage.error("个性签名保存失败");
  } finally {
    savingSignature.value = false;
  }
}

async function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    ElMessage.warning("请选择图片文件");
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning("头像图片不能超过 2MB");
    return;
  }

  uploadingAvatar.value = true;
  try {
    const profile = await uploadAvatar(file);
    applyProfile({
      ...profile,
      avatar_url: profile.avatar_url ? `${profile.avatar_url}?v=${Date.now()}` : null
    });
    ElMessage.success("头像已更新");
  } catch {
    ElMessage.error("头像上传失败，请确认对象存储服务已启动");
  } finally {
    uploadingAvatar.value = false;
  }
}

function applyProfile(profile: {
  username: string;
  created_at?: string;
  avatar_url?: string | null;
  signature?: string | null;
}) {
  auth.setProfile({
    username: profile.username,
    createdAt: profile.created_at,
    avatarUrl: profile.avatar_url ?? null,
    signature: profile.signature ?? null
  });
  signatureDraft.value = profile.signature ?? "";
}

async function logout() {
  try {
    await ElMessageBox.confirm("退出后需要重新登录才能访问业务页面。", "退出登录", {
      confirmButtonText: "退出",
      cancelButtonText: "取消",
      type: "warning"
    });
  } catch {
    return;
  }
  auth.logout();
  workspace.setCurrentCaseId(null);
  workspace.setCurrentDocumentId(null);
  router.push("/login");
}
</script>

<style scoped>
.profile-page {
  max-width: 1180px;
}

.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 16px;
}

.account-panel,
.workspace-panel,
.workspace-wide-panel,
.recent-panel {
  padding: 18px;
}

.account-panel {
  display: grid;
  grid-template-columns: 118px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}

.avatar-block {
  display: grid;
  justify-items: center;
  gap: 10px;
}

.avatar-input {
  display: none;
}

.avatar {
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  color: #ffffff;
  background: var(--color-brand);
  font-size: 28px;
  overflow: hidden;
  cursor: pointer;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.account-panel h2,
.workspace-panel h2,
.recent-panel h2 {
  margin: 0;
  font-size: 18px;
}

.signature-text {
  margin: 6px 0 0;
  color: var(--color-muted);
  line-height: 1.7;
}

.account-meta {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-line);
}

.account-meta > div,
.workspace-list > div {
  display: grid;
  gap: 6px;
}

.account-meta span,
.workspace-list span,
.stat-item span {
  color: var(--color-muted);
  font-size: 12px;
}

.account-meta strong,
.workspace-list strong,
.workspace-list a {
  overflow-wrap: anywhere;
  color: var(--color-strong);
  font-size: 14px;
}

.workspace-panel,
.workspace-wide-panel {
  display: grid;
  gap: 16px;
}

.workspace-wide-panel h2 {
  margin: 0 0 16px;
  font-size: 18px;
}

.workspace-list {
  display: grid;
  gap: 14px;
}

.workspace-list a,
.panel-title-row a {
  color: var(--color-brand);
  font-weight: 700;
}

.workspace-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stats-panel {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  background: var(--color-line);
}

.stat-item {
  display: grid;
  gap: 8px;
  padding: 18px;
  background: #ffffff;
  border-top: 3px solid var(--color-brand);
}

.stat-item:nth-child(2) {
  border-top-color: var(--color-mint);
}

.stat-item:nth-child(3) {
  border-top-color: var(--color-violet);
}

.stat-item:nth-child(4) {
  border-top-color: var(--color-amber);
}

.stat-item strong {
  font-size: 24px;
}

.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.recent-loading {
  padding-top: 8px;
}

.recent-list {
  display: grid;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 64px;
  padding: 12px 0;
  border-top: 1px solid var(--color-line);
}

.recent-item > div {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.recent-item strong {
  overflow: hidden;
  color: var(--color-strong);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-item span {
  color: var(--color-muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .profile-grid,
  .account-meta,
  .stats-panel {
    grid-template-columns: 1fr;
  }

  .account-panel {
    grid-template-columns: 1fr;
  }

  .avatar {
    width: 86px;
    height: 86px;
  }
}
</style>
