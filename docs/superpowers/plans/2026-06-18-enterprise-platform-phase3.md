# 企业平台 第三期：用户认证与权限 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善三级权限系统：admin/teacher/student 角色生效，前端受保护路由，登录状态管理。

**Architecture:** Backend 用现有 roleMiddleware 保护路由。前端用 Pinia store 管理登录状态 + Vue Router navigation guard 保护页面。

**Tech Stack:** Existing (Express + JWT + Vue3 + Pinia)

---

### Task 1: Backend — Apply Role Protection to Routes

**Files:**
- Modify: `platform/backend/src/routes/samples.js`
- Modify: `platform/backend/src/routes/analysis.js`
- Create: `platform/backend/src/routes/admin.js`

- [ ] **Step 1: Apply roleMiddleware to samples routes**

Read `platform/backend/src/routes/samples.js`. Update import:
```javascript
import { authMiddleware, roleMiddleware } from '../middleware/auth.js';
```

Update POST route to require admin:
```javascript
router.post('/', authMiddleware, roleMiddleware('admin', 'teacher'), async (req, res) => {
```
Update DELETE route (add after GET route):
```javascript
router.delete('/:id', authMiddleware, roleMiddleware('admin'), async (req, res) => {
  try {
    await Sample.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

- [ ] **Step 2: Apply roleMiddleware to analysis delete**

Read `platform/backend/src/routes/analysis.js`. Add DELETE route:
```javascript
router.delete('/:id', authMiddleware, roleMiddleware('admin'), async (req, res) => {
  try {
    await Analysis.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
```

- [ ] **Step 3: Create admin user management route**

Create `platform/backend/src/routes/admin.js`:
```javascript
import { Router } from 'express';
import { authMiddleware, roleMiddleware } from '../middleware/auth.js';
import User from '../models/User.js';

const router = Router();

// All admin routes require admin role
router.use(authMiddleware, roleMiddleware('admin'));

router.get('/users', async (req, res) => {
  const users = await User.find().select('-password_hash');
  res.json(users);
});

router.put('/users/:id/role', async (req, res) => {
  const { role } = req.body;
  if (!['admin', 'teacher', 'student'].includes(role)) {
    return res.status(400).json({ error: 'Invalid role' });
  }
  const user = await User.findByIdAndUpdate(req.params.id, { role }, { new: true })
    .select('-password_hash');
  if (!user) return res.status(404).json({ error: 'User not found' });
  res.json(user);
});

router.delete('/users/:id', async (req, res) => {
  await User.findByIdAndDelete(req.params.id);
  res.json({ message: 'User deleted' });
});

export default router;
```

- [ ] **Step 4: Wire admin routes in index.js**

Read `platform/backend/src/index.js`. After existing route imports, add:
```javascript
import adminRoutes from './routes/admin.js';
app.use('/api/admin', adminRoutes);
```

- [ ] **Step 5: Verify**

```bash
cd platform/backend && node --check src/index.js && echo "OK"
```

- [ ] **Step 6: Commit**

```bash
git add platform/backend/
git commit -m "feat: add role-based access control and admin user management"
```

---

### Task 2: Frontend — Auth Store + Route Guards

**Files:**
- Create: `platform/frontend/src/stores/auth.js`
- Modify: `platform/frontend/src/router/index.js`

- [ ] **Step 1: Create Pinia auth store**

Create `platform/frontend/src/stores/auth.js`:
```javascript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '../api/index.js';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null);
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'));

  const isLoggedIn = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.role === 'admin');
  const isTeacher = computed(() => user.value?.role === 'teacher');

  async function loginAction(username, password) {
    const res = await api.login({ username, password });
    token.value = res.data.token;
    user.value = res.data.user;
    localStorage.setItem('token', res.data.token);
    localStorage.setItem('user', JSON.stringify(res.data.user));
  }

  async function registerAction(username, password) {
    await api.register({ username, password, role: 'student' });
    await loginAction(username, password);
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  return { token, user, isLoggedIn, isAdmin, isTeacher, loginAction, registerAction, logout };
});
```

- [ ] **Step 2: Add navigation guards to router**

Read `platform/frontend/src/router/index.js`. After creating router, add:
```javascript
import { useAuthStore } from '../stores/auth.js';

// ... routes definition ...

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to, from, next) => {
  const publicPages = ['/', '/login'];
  const authRequired = !publicPages.includes(to.path);
  const auth = useAuthStore();

  if (authRequired && !auth.isLoggedIn) {
    next('/login');
  } else {
    next();
  }
});

export default router;
```

- [ ] **Step 3: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add Pinia auth store and Vue Router navigation guards"
```

---

### Task 3: Frontend — Update Pages to Use Auth Store

**Files:**
- Modify: `platform/frontend/src/App.vue`
- Modify: `platform/frontend/src/views/Login.vue`
- Modify: `platform/frontend/src/views/Upload.vue`

- [ ] **Step 1: Update App.vue nav to show login state**

Replace `platform/frontend/src/App.vue`:
```vue
<template>
  <div>
    <nav class="navbar">
      <router-link to="/">首页</router-link>
      <router-link to="/upload">上传分析</router-link>
      <span style="flex:1"></span>
      <template v-if="auth.isLoggedIn">
        <span style="color:#aaa;font-size:13px">{{ auth.user?.username }} ({{ auth.user?.role }})</span>
        <a href="#" @click.prevent="auth.logout(); $router.push('/')">退出</a>
      </template>
      <router-link v-else to="/login">登录</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth.js';
const auth = useAuthStore();
</script>

<style>
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; }
.navbar { background: #2c3e50; padding: 12px 24px; display: flex; gap: 20px; align-items: center; }
.navbar a { color: white; text-decoration: none; }
.navbar a:hover { text-decoration: underline; }
.navbar a.router-link-exact-active { font-weight: bold; }
</style>
```

- [ ] **Step 2: Update Login.vue to use auth store**

Replace `platform/frontend/src/views/Login.vue`:
```vue
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
```

- [ ] **Step 3: Build and verify**

```bash
cd platform/frontend && npm run build 2>&1 | tail -3
```
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add platform/frontend/
git commit -m "feat: integrate auth store into navbar, login, and upload pages"
```

---

### Task 4: E2E Auth Verification

- [ ] **Step 1: Verify desktop tests still pass**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 2: Verify backend syntax**

```bash
cd platform/backend && node --check src/index.js && echo "OK"
```

- [ ] **Step 3: Verify frontend build**

```bash
cd platform/frontend && npm run build 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "chore: Phase 3 E2E auth verification complete" && git push origin v3.0-platform
```

---

## Summary

| Task | Component | Key Files |
|---|---|---|
| 1 | RBAC Routes | samples.js, analysis.js, admin.js |
| 2 | Auth Store + Guards | stores/auth.js, router/index.js |
| 3 | Updated UI | App.vue, Login.vue |
| 4 | E2E Verification | tests + builds |
