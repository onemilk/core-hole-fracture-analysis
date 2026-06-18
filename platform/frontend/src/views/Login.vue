<template>
  <div class="login-page">
    <h2>登录</h2>
    <form @submit.prevent="login">
      <input v-model="username" placeholder="用户名" required />
      <input v-model="password" type="password" placeholder="密码" required />
      <button type="submit">登录</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
    <p class="hint">没有账号？先注册：</p>
    <form @submit.prevent="register">
      <input v-model="regUser" placeholder="用户名" required />
      <input v-model="regPass" type="password" placeholder="密码" required />
      <button type="submit">注册</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/index.js';

const router = useRouter();
const username = ref('');
const password = ref('');
const regUser = ref('');
const regPass = ref('');
const error = ref(null);

async function login() {
  try {
    const res = await api.login({ username: username.value, password: password.value });
    localStorage.setItem('token', res.data.token);
    router.push('/');
  } catch (e) {
    error.value = '登录失败: ' + (e.response?.data?.error || e.message);
  }
}

async function register() {
  try {
    await api.register({ username: regUser.value, password: regPass.value, role: 'student' });
    username.value = regUser.value;
    password.value = regPass.value;
    await login();
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
