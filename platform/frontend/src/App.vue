<template>
  <div>
    <nav class="navbar">
      <router-link to="/">首页</router-link>
      <router-link to="/upload">上传分析</router-link>
      <span style="flex:1"></span>
      <router-link to="/login">登录</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style>
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; }
.navbar { background: #2c3e50; padding: 12px 24px; display: flex; gap: 20px; align-items: center; }
.navbar a { color: white; text-decoration: none; }
.navbar a:hover { text-decoration: underline; }
.navbar a.router-link-exact-active { font-weight: bold; }
</style>
