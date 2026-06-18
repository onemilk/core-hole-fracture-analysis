<template>
  <div>
    <nav class="navbar">
      <router-link to="/">首页</router-link>
      <router-link to="/upload">上传分析</router-link>
      <span style="flex:1"></span>
      <template v-if="auth.isLoggedIn">
        <span style="color:#aaa;font-size:13px">{{ auth.user?.username }} ({{ auth.user?.role }})</span>
        <a href="#" @click.prevent="handleLogout">退出</a>
      </template>
      <router-link v-else to="/login">登录</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth.js';
const auth = useAuthStore();
const router = useRouter();

function handleLogout() {
  auth.logout();
  router.push('/');
}
</script>

<style>
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; }
.navbar { background: #2c3e50; padding: 12px 24px; display: flex; gap: 20px; align-items: center; }
.navbar a { color: white; text-decoration: none; }
.navbar a:hover { text-decoration: underline; }
.navbar a.router-link-exact-active { font-weight: bold; }
</style>
