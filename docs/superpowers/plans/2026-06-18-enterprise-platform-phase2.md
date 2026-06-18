# 企业平台 第二期：前后端分析流程 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 打通完整分析流程：上传图像 → 提交分析 → Python 引擎处理 → 前端展示结果和报告。

**Architecture:** Backend 新增文件上传和异步分析端点，通过 axios 调用 Python engine。Frontend 新增上传页和分析结果页。ReportGenerator 输出同时支持 HTML（现有）和 JSON。

**Tech Stack:** multer (file upload), axios (Node→Python HTTP), Vue3 composition API, Chart.js (前端图表)

---

### Task 1: Backend — File Upload Endpoint

**Files:**
- Modify: `platform/backend/src/routes/samples.js`
- Create: `platform/backend/uploads/` directory

- [ ] **Step 1: Add multer config and upload route to samples.js**

Read `platform/backend/src/routes/samples.js`. Replace with:

```javascript
import { Router } from 'express';
import multer from 'multer';
import path from 'path';
import { authMiddleware } from '../middleware/auth.js';
import Sample from '../models/Sample.js';

const router = Router();
router.use(authMiddleware);

const upload = multer({
  dest: path.join(process.cwd(), 'uploads'),
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'];
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, allowed.includes(ext));
  }
});

router.get('/', async (req, res) => {
  const samples = await Sample.find().limit(20);
  res.json(samples);
});

router.post('/', async (req, res) => {
  try {
    const sample = await Sample.create({ ...req.body, created_by: req.user.id });
    res.status(201).json(sample);
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

router.post('/:id/images', upload.single('image'), async (req, res) => {
  try {
    const sample = await Sample.findById(req.params.id);
    if (!sample) return res.status(404).json({ error: 'Sample not found' });
    sample.image_files.push({
      filename: req.file.originalname,
      path: req.file.path,
      mimetype: req.file.mimetype,
      size: req.file.size
    });
    await sample.save();
    res.json(sample);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
```

- [ ] **Step 2: Create uploads directory**

```bash
mkdir -p platform/backend/uploads
echo "*.jpg" > platform/backend/uploads/.gitignore
```

- [ ] **Step 3: Commit**

```bash
git add platform/backend/src/routes/samples.js platform/backend/uploads/
git commit -m "feat: add file upload endpoint with multer (50MB limit)"
```

---

### Task 2: Backend — Analysis Submission + Engine Call

**Files:**
- Modify: `platform/backend/src/routes/analysis.js`
- Create: `platform/backend/src/services/engine.js`

- [ ] **Step 1: Create engine service**

Create `platform/backend/src/services/engine.js`:
```javascript
import axios from 'axios';
import fs from 'fs';

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:5001';

export async function runAnalysis(imagePath, analysisType, params = {}) {
  const imageBuffer = fs.readFileSync(imagePath);
  const imageBase64 = imageBuffer.toString('base64');

  const response = await axios.post(`${ENGINE_URL}/engine/analyze`, {
    image_base64: imageBase64,
    analysis_type: analysisType,
    scale_mm_per_px: params.scale || 0.05,
    match_tolerance: params.tolerance || 30,
    denoise_threshold: params.denoise || 10,
    core_length_m: params.coreLength || 1.0
  }, { timeout: 120000 });

  return response.data;
}
```

- [ ] **Step 2: Install axios in backend**

```bash
cd platform/backend && npm install axios
```

- [ ] **Step 3: Replace analysis.js with full implementation**

Overwrite `platform/backend/src/routes/analysis.js`:
```javascript
import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.js';
import Analysis from '../models/Analysis.js';
import { runAnalysis } from '../services/engine.js';

const router = Router();
router.use(authMiddleware);

// Submit analysis
router.post('/', async (req, res) => {
  try {
    const { sample_id, type, image_path, params } = req.body;
    const analysis = await Analysis.create({
      sample_id, type, params, status: 'pending', created_by: req.user.id
    });

    // Run analysis asynchronously
    runAnalysis(image_path, type, params)
      .then(async (result) => {
        analysis.status = 'done';
        analysis.results = result;
        await analysis.save();
      })
      .catch(async (err) => {
        analysis.status = 'failed';
        analysis.results = { error: err.message };
        await analysis.save();
      });

    res.status(202).json({ task_id: analysis._id, status: 'pending' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Get analysis result
router.get('/:id', async (req, res) => {
  const analysis = await Analysis.findById(req.params.id)
    .populate('sample_id');
  if (!analysis) return res.status(404).json({ error: 'Analysis not found' });
  res.json(analysis);
});

// List analyses for a sample
router.get('/sample/:sampleId', async (req, res) => {
  const analyses = await Analysis.find({ sample_id: req.params.sampleId })
    .sort({ created_at: -1 }).limit(20);
  res.json(analyses);
});

export default router;
```

- [ ] **Step 4: Verify**

```bash
cd platform/backend && npm install axios && node --check src/index.js && echo "OK"
```

- [ ] **Step 5: Commit**

```bash
git add platform/backend/
git commit -m "feat: add analysis submission endpoint with async engine call"
```

---

### Task 3: Frontend — Upload Page

**Files:**
- Create: `platform/frontend/src/views/Upload.vue`
- Modify: `platform/frontend/src/router/index.js`
- Create: `platform/frontend/src/api/index.js`

- [ ] **Step 1: Create API helper**

Create `platform/frontend/src/api/index.js`:
```javascript
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

// Attach JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default {
  // Auth
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  // Samples
  getSamples: () => api.get('/samples'),
  createSample: (data) => api.post('/samples', data),
  uploadImage: (sampleId, formData) => api.post(`/samples/${sampleId}/images`, formData),
  // Analysis
  submitAnalysis: (data) => api.post('/analysis', data),
  getAnalysis: (id) => api.get(`/analysis/${id}`),
};
```

- [ ] **Step 2: Create Upload page**

Create `platform/frontend/src/views/Upload.vue`:
```vue
<template>
  <div class="upload-page">
    <h2>岩心图像上传</h2>
    
    <div class="step" v-if="!sampleId">
      <h3>1. 创建样本</h3>
      <form @submit.prevent="createSample">
        <input v-model="form.basin" placeholder="盆地（如塔里木盆地）" required />
        <input v-model="form.well_id" placeholder="井号（如J12-01）" required />
        <input v-model.number="form.top_depth" type="number" step="0.01" placeholder="起始深度(m)" required />
        <input v-model.number="form.bottom_depth" type="number" step="0.01" placeholder="结束深度(m)" required />
        <button type="submit">创建样本</button>
      </form>
    </div>

    <div class="step" v-if="sampleId">
      <h3>2. 上传图像</h3>
      <input type="file" @change="uploadImage" accept="image/*" />
      <p v-if="uploaded">✅ 上传成功</p>
    </div>

    <div class="step" v-if="uploaded">
      <h3>3. 开始分析</h3>
      <select v-model="analysisType">
        <option value="hole">孔洞分析</option>
        <option value="fracture">裂缝分析</option>
        <option value="grain">粒度分析</option>
      </select>
      <button @click="startAnalysis" :disabled="analyzing">
        {{ analyzing ? '分析中...' : '开始分析' }}
      </button>
      <p v-if="analysisId">✅ 分析任务已提交: {{ analysisId }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../api/index.js';

const sampleId = ref(null);
const uploaded = ref(false);
const analyzing = ref(false);
const analysisType = ref('hole');
const analysisId = ref(null);
const form = ref({ basin: '', well_id: '', top_depth: null, bottom_depth: null });

async function createSample() {
  const res = await api.createSample({ ...form.value, sample_id: `${form.value.basin}-${form.value.well_id}-${Date.now()}` });
  sampleId.value = res.data._id;
}

async function uploadImage(e) {
  const fd = new FormData();
  fd.append('image', e.target.files[0]);
  await api.uploadImage(sampleId.value, fd);
  uploaded.value = true;
}

async function startAnalysis() {
  analyzing.value = true;
  const res = await api.submitAnalysis({ sample_id: sampleId.value, type: analysisType.value, params: {} });
  analysisId.value = res.data.task_id;
  analyzing.value = false;
}
</script>

<style scoped>
.upload-page { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
.step { margin: 24px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
input, select, button { display: block; width: 100%; margin: 8px 0; padding: 10px; font-size: 14px; }
button { background: #2c3e50; color: white; border: none; cursor: pointer; border-radius: 4px; }
button:disabled { background: #999; }
</style>
```

- [ ] **Step 3: Update router**

Edit `platform/frontend/src/router/index.js` — add Upload route:
```javascript
const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: () => import('../views/Upload.vue') },
]
```

- [ ] **Step 4: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add Upload page with sample creation, image upload, analysis submission"
```

---

### Task 4: Frontend — Analysis Result Page

**Files:**
- Create: `platform/frontend/src/views/Result.vue`
- Modify: `platform/frontend/src/router/index.js`

- [ ] **Step 1: Create Result page**

Create `platform/frontend/src/views/Result.vue`:
```vue
<template>
  <div class="result-page">
    <h2>分析结果</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else-if="analysis">
      <p>状态: <b>{{ analysis.status }}</b></p>
      <div v-if="analysis.status === 'done' && results">
        <h3>统计摘要</h3>
        <table>
          <tr v-for="(val, key) in results.summary" :key="key">
            <td>{{ key }}</td><td>{{ val }}</td>
          </tr>
        </table>
        <h3>检测区域 ({{ results.regions?.length || 0 }} 个)</h3>
      </div>
      <button @click="refresh">刷新结果</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/index.js';

const route = useRoute();
const loading = ref(true);
const error = ref(null);
const analysis = ref(null);
const results = ref(null);

async function load() {
  try {
    const res = await api.getAnalysis(route.params.id);
    analysis.value = res.data;
    if (res.data.results) results.value = res.data.results;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function refresh() {
  loading.value = true;
  load();
}

onMounted(load);
</script>

<style scoped>
.result-page { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
td, th { border: 1px solid #ddd; padding: 8px; }
button { padding: 10px 20px; background: #2c3e50; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style>
```

- [ ] **Step 2: Add route**

Edit `platform/frontend/src/router/index.js`:
```javascript
const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: () => import('../views/Upload.vue') },
  { path: '/result/:id', name: 'Result', component: () => import('../views/Result.vue') },
]
```

- [ ] **Step 3: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add Analysis Result page with status polling"
```

---

### Task 5: Frontend — Navigation + Login Page

**Files:**
- Create: `platform/frontend/src/views/Login.vue`
- Modify: `platform/frontend/src/App.vue` (add nav bar)
- Modify: `platform/frontend/src/router/index.js`

- [ ] **Step 1: Add navigation to App.vue**

Replace `platform/frontend/src/App.vue`:
```vue
<template>
  <div>
    <nav class="navbar">
      <router-link to="/">首页</router-link>
      <router-link to="/upload">上传分析</router-link>
    </nav>
    <router-view />
  </div>
</template>

<style>
body { margin: 0; font-family: "Microsoft YaHei", sans-serif; }
.navbar { background: #2c3e50; padding: 12px 24px; display: flex; gap: 20px; }
.navbar a { color: white; text-decoration: none; }
.navbar a:hover { text-decoration: underline; }
</style>
```

- [ ] **Step 2: Create Login page**

Create `platform/frontend/src/views/Login.vue`:
```vue
<template>
  <div class="login-page">
    <h2>登录</h2>
    <form @submit.prevent="login">
      <input v-model="username" placeholder="用户名" required />
      <input v-model="password" type="password" placeholder="密码" required />
      <button type="submit">登录</button>
    </form>
    <p v-if="error" style="color:red">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/index.js';

const router = useRouter();
const username = ref('');
const password = ref('');
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
</script>

<style scoped>
.login-page { max-width: 400px; margin: 60px auto; padding: 40px; border: 1px solid #ddd; border-radius: 8px; }
input, button { display: block; width: 100%; margin: 12px 0; padding: 10px; font-size: 14px; }
button { background: #2c3e50; color: white; border: none; cursor: pointer; border-radius: 4px; }
</style>
```

- [ ] **Step 3: Add route**

Edit router `routes`:
```javascript
{ path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
```

- [ ] **Step 4: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add navigation bar and login page"
```

---

### Task 6: E2E Integration Smoke Test

- [ ] **Step 1: Verify desktop tests still pass**

```bash
cd ../.. && python -m pytest tests/ -q
```

- [ ] **Step 2: Manual verification checklist**

```
□ Backend:  GET /api/health → 200
□ Engine:   GET /engine/health → 200
□ Auth:     POST /api/auth/register → 201
□ Auth:     POST /api/auth/login → 200 + token
□ Frontend: GET / → 200 HTML with nav bar
□ Frontend: GET /upload → Upload page
□ Frontend: GET /login → Login page
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "chore: E2E integration checklist for Phase 2"
```

---

## Summary

| Task | Component | Key Files |
|---|---|---|
| 1 | File Upload | `routes/samples.js` + multer |
| 2 | Analysis Pipeline | `routes/analysis.js` + `services/engine.js` |
| 3 | Upload Page | `views/Upload.vue` + `api/index.js` |
| 4 | Result Page | `views/Result.vue` |
| 5 | Navigation + Login | `App.vue` + `views/Login.vue` |
| 6 | E2E Verification | Desktop tests + manual check |
