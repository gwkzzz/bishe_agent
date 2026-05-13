<template>
  <main class="login-page">
    <section class="login-panel">
      <h1>法律咨询辅助</h1>
      <el-alert
        v-if="mustLogin"
        class="login-required"
        title="请先登录"
        description="该页面需要登录后才能访问。请使用已注册账号登录后继续。"
        type="warning"
        show-icon
        :closable="false"
      />
      <el-form class="login-form" :model="form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button class="login-button" type="primary" native-type="submit" :loading="submitting">
          登录
        </el-button>
      </el-form>
      <p class="auth-switch">
        还没有账号？
        <RouterLink to="/register">先注册</RouterLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { http } from "@/api/http";
import { useAuthStore } from "@/stores/auth";
import type { LoginResponse } from "@/types/api";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const form = reactive({
  username: "",
  password: ""
});
const submitting = ref(false);
const mustLogin = computed(() => route.query.reason === "login-required" || Boolean(route.query.redirect));

async function submit() {
  submitting.value = true;
  try {
    const response = await http.post<LoginResponse>("/api/auth/login", form);
    auth.setSession(
      response.data.access_token,
      response.data.user.username,
      response.data.user.created_at,
      response.data.user.avatar_url,
      response.data.user.signature
    );
    router.push((route.query.redirect as string | undefined) ?? "/consultation");
  } catch {
    ElMessage.error("登录失败，请先注册并确认密码正确");
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
  background: var(--color-soft);
}

.login-panel {
  width: min(420px, 100%);
  padding: 32px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  background: #ffffff;
  box-shadow: var(--shadow-soft);
}

.login-panel h1 {
  margin: 0 0 24px;
  font-size: 26px;
}

.login-form {
  display: grid;
  gap: 4px;
}

.login-required {
  margin-bottom: 18px;
}

.login-button {
  width: 100%;
  min-height: 40px;
}

.auth-switch {
  margin: 18px 0 0;
  color: #606266;
  text-align: center;
}

.auth-switch a {
  color: var(--color-brand);
  font-weight: 700;
  text-decoration: none;
}
</style>
