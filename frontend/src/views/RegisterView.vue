<template>
  <main class="register-page">
    <section class="register-panel">
      <h1>注册账号</h1>
      <el-form class="register-form" :model="form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="new-password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="confirmPassword" type="password" autocomplete="new-password" show-password />
        </el-form-item>
        <el-button class="register-button" type="primary" native-type="submit" :loading="submitting">
          注册
        </el-button>
      </el-form>
      <p class="auth-switch">
        已有账号？
        <RouterLink to="/login">去登录</RouterLink>
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { http } from "@/api/http";
import type { ApiError } from "@/api/http";

const router = useRouter();
const form = reactive({
  username: "",
  password: ""
});
const confirmPassword = ref("");
const submitting = ref(false);

async function submit() {
  const username = form.username.trim();
  if (!username) {
    ElMessage.warning("请输入用户名");
    return;
  }
  if (form.password.length < 6) {
    ElMessage.warning("密码至少 6 位");
    return;
  }
  if (form.password !== confirmPassword.value) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }

  submitting.value = true;
  try {
    await http.post("/api/auth/register", {
      username,
      password: form.password
    });
    ElMessage.success("注册成功，请登录");
    router.push({ name: "login" });
  } catch (error) {
    const apiError = error as ApiError;
    if (apiError.status === 409) {
      ElMessage.error("用户名已存在，请换一个用户名");
    } else if (apiError.status === 422) {
      ElMessage.error(apiError.message || "注册信息格式不正确");
    } else {
      ElMessage.error(apiError.message || "注册失败，请确认服务端已启动");
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.register-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
  background: var(--color-soft);
}

.register-panel {
  width: min(420px, 100%);
  padding: 32px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  background: #ffffff;
  box-shadow: var(--shadow-soft);
}

.register-panel h1 {
  margin: 0 0 24px;
  font-size: 26px;
}

.register-form {
  display: grid;
  gap: 4px;
}

.register-button {
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
