<template>
  <div class="login-page">
    <h2>登录</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="username" placeholder="用户名" required />
      <input v-model="password" type="password" placeholder="密码" required />
      <button type="submit">登录</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="hint">没有账号？在此注册：</p>
    <form @submit.prevent="handleRegister">
      <input v-model="regUser" placeholder="用户名" required />
      <input v-model="regPass" type="password" placeholder="密码" required />
      <button type="submit">注册</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth.js';

const router = useRouter();
const auth = useAuthStore();
const username = ref('');
const password = ref('');
const regUser = ref('');
const regPass = ref('');
const error = ref(null);

async function handleLogin() {
  try {
    await auth.loginAction(username.value, password.value);
    router.push('/');
  } catch (e) {
    error.value = '登录失败: ' + (e.response?.data?.error || e.message);
  }
}

async function handleRegister() {
  try {
    await auth.registerAction(regUser.value, regPass.value);
    router.push('/');
  } catch (e) {
    error.value = '注册失败: ' + (e.response?.data?.error || e.message);
  }
}
</script>

<style scoped>
.login-page { max-width: 400px; margin: 60px auto; padding: 40px; border: 1px solid #ddd; border-radius: 8px; }
input, button { display: block; width: 100%; margin: 12px 0; padding: 10px; font-size: 14px; box-sizing: border-box; }
button { background: #2c3e50; color: white; border: none; cursor: pointer; border-radius: 4px; }
.error { color: #c0392b; }
.hint { margin-top: 30px; color: #666; font-size: 13px; }
</style>
