# 企业平台 第一期：平台骨架 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建企业级 B/S 平台骨架：Docker Compose + Node.js Express + MongoDB + Python FastAPI 引擎 + Redis Celery + Vue3 前端壳。

**Architecture:** Nginx 反向代理 → Node.js Express (API) → MongoDB (数据) + Redis (队列) → Python FastAPI (引擎)。全部容器化。

**Tech Stack:** Node.js 20 + Express, Python 3.10 + FastAPI + Celery, MongoDB 7, Redis 7, Vue3 + Vite, Docker Compose, Nginx

---

## 项目目录结构

```
platform/
├── docker-compose.yml
├── nginx/
│   └── default.conf
├── backend/                    # Node.js Express
│   ├── package.json
│   ├── src/
│   │   ├── index.js            # 入口
│   │   ├── routes/
│   │   │   ├── auth.js
│   │   │   ├── samples.js
│   │   │   └── analysis.js
│   │   ├── models/
│   │   │   └── db.js           # MongoDB 连接
│   │   └── middleware/
│   │       └── auth.js         # JWT 中间件
│   └── Dockerfile
├── engine-api/                 # Python FastAPI
│   ├── requirements.txt
│   ├── main.py                 # FastAPI 入口
│   ├── engine/                 # 从桌面版复制
│   │   ├── image_processor.py
│   │   ├── region_extractor.py
│   │   ├── morphology_engine.py
│   │   ├── hole_analyzer.py
│   │   ├── fracture_analyzer.py
│   │   └── grain_analyzer.py
│   ├── worker.py               # Celery worker
│   └── Dockerfile
├── frontend/                   # Vue3
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/index.js
│       ├── views/
│       │   └── Home.vue
│       └── components/
│           └── Layout.vue
└── .env
```

---

### Task 1: Docker Compose 环境骨架

**Files:**
- Create: `platform/docker-compose.yml`
- Create: `platform/nginx/default.conf`
- Create: `platform/.env`

- [ ] **Step 1: Write docker-compose.yml**

Create `platform/docker-compose.yml`:
```yaml
version: "3.8"

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend
      - frontend

  backend:
    build: ./backend
    ports:
      - "3000:3000"
    env_file: .env
    depends_on:
      - mongo
      - redis

  engine:
    build: ./engine-api
    ports:
      - "5001:5001"
    env_file: .env
    depends_on:
      - redis

  worker:
    build: ./engine-api
    command: celery -A worker.celery worker --loglevel=info
    env_file: .env
    depends_on:
      - redis

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"

volumes:
  mongo_data:
```

- [ ] **Step 2: Write Nginx config**

Create `platform/nginx/default.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://frontend:5173;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /engine/ {
        proxy_pass http://engine:5001;
        proxy_set_header Host $host;
    }
}
```

- [ ] **Step 3: Write .env**

Create `platform/.env`:
```
MONGODB_URI=mongodb://mongo:27017/core_analysis
REDIS_URI=redis://redis:6379/0
JWT_SECRET=dev-secret-change-in-production
ENGINE_URL=http://engine:5001
```

- [ ] **Step 4: Verify docker-compose config**

```bash
cd platform && docker compose config 2>&1 | head -5
```
Expected: valid YAML output, no errors.

- [ ] **Step 5: Commit**

```bash
git add platform/docker-compose.yml platform/nginx/default.conf platform/.env
git commit -m "feat: add Docker Compose skeleton with nginx, mongo, redis"
```

---

### Task 2: Node.js Express Backend

**Files:**
- Create: `platform/backend/package.json`
- Create: `platform/backend/Dockerfile`
- Create: `platform/backend/src/index.js`
- Create: `platform/backend/src/models/db.js`

- [ ] **Step 1: Write package.json**

Create `platform/backend/package.json`:
```json
{
  "name": "core-analysis-backend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "node --watch src/index.js",
    "start": "node src/index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^8.0.0",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1",
    "redis": "^4.6.0",
    "dotenv": "^16.3.1"
  }
}
```

- [ ] **Step 2: Write Dockerfile**

Create `platform/backend/Dockerfile`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY src/ ./src/
EXPOSE 3000
CMD ["node", "src/index.js"]
```

- [ ] **Step 3: Write index.js**

Create `platform/backend/src/index.js`:
```javascript
import express from 'express';
import cors from 'cors';
import { connectDB } from './models/db.js';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Routes (to be added in later tasks)
// import authRoutes from './routes/auth.js';
// import sampleRoutes from './routes/samples.js';
// import analysisRoutes from './routes/analysis.js';
// app.use('/api/auth', authRoutes);
// app.use('/api/samples', sampleRoutes);
// app.use('/api/analysis', analysisRoutes);

connectDB().then(() => {
  app.listen(PORT, () => {
    console.log(`Backend listening on port ${PORT}`);
  });
});
```

- [ ] **Step 4: Write db.js**

Create `platform/backend/src/models/db.js`:
```javascript
import mongoose from 'mongoose';

export async function connectDB() {
  const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017/core_analysis';
  await mongoose.connect(uri);
  console.log('MongoDB connected');
}
```

- [ ] **Step 5: Verify locally**

```bash
cd platform/backend && npm install && node src/index.js &
sleep 3
curl http://localhost:3000/api/health
kill %1
```
Expected: `{"status":"ok","timestamp":"..."}`

- [ ] **Step 6: Commit**

```bash
git add platform/backend/
git commit -m "feat: add Node.js Express backend with MongoDB connection and health check"
```

---

### Task 3: Python FastAPI Engine

**Files:**
- Create: `platform/engine-api/requirements.txt`
- Create: `platform/engine-api/Dockerfile`
- Create: `platform/engine-api/main.py`
- Copy: engine files from `core_analysis/engine/`

- [ ] **Step 1: Write requirements.txt**

Create `platform/engine-api/requirements.txt`:
```
fastapi==0.104.1
uvicorn==0.24.0
celery==5.3.4
redis==5.0.1
opencv-python==4.8.1.78
numpy==1.26.2
scipy==1.11.4
matplotlib==3.8.2
jinja2==3.1.2
python-multipart==0.0.6
```

- [ ] **Step 2: Write Dockerfile**

Create `platform/engine-api/Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py worker.py ./
COPY engine/ ./engine/
EXPOSE 5001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
```

- [ ] **Step 3: Write FastAPI main.py**

Create `platform/engine-api/main.py`:
```python
"""FastAPI analysis engine — wraps core_analysis.engine modules."""

import os
import sys
import base64
import io
import numpy as np
import cv2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))

from engine.image_processor import ImageProcessor
from engine.region_extractor import RegionExtractor
from engine.morphology_engine import MorphologyEngine
from engine.hole_analyzer import HoleAnalyzer
from engine.fracture_analyzer import FractureAnalyzer
from engine.grain_analyzer import GrainAnalyzer
from engine.report_generator import ReportGenerator

app = FastAPI(title="Core Analysis Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class AnalysisRequest(BaseModel):
    image_base64: str       # base64-encoded image
    analysis_type: str      # "hole" | "fracture" | "grain"
    scale_mm_per_px: float = 0.05
    match_tolerance: int = 30
    denoise_threshold: int = 10
    core_length_m: float = 1.0


class AnalysisResponse(BaseModel):
    regions: list = []
    summary: dict = {}
    charts: dict = {}


@app.get("/engine/health")
def health():
    return {"status": "ok", "engine": "v1.0"}


@app.post("/engine/analyze", response_model=AnalysisResponse)
def analyze(req: AnalysisRequest):
    try:
        # Decode image
        img_bytes = base64.b64decode(req.image_base64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if bgr is None:
            raise HTTPException(400, "Invalid image data")

        h, w = bgr.shape[:2]
        image_area_px = h * w

        # Preprocess
        preprocessed = ImageProcessor.auto_levels(bgr)

        # Extract regions
        center_color = preprocessed[h // 2, w // 2]
        regions = RegionExtractor.extract_by_color_sample(
            preprocessed, center_color, req.match_tolerance)
        regions = MorphologyEngine.denoise_by_area(regions, req.denoise_threshold)

        # Analyze
        if req.analysis_type == "hole":
            results, summary = HoleAnalyzer.analyze(regions, req.scale_mm_per_px, image_area_px)
        elif req.analysis_type == "fracture":
            results, summary = FractureAnalyzer.analyze(regions, req.scale_mm_per_px,
                                                        image_area_px, req.core_length_m)
        elif req.analysis_type == "grain":
            results, summary = GrainAnalyzer.analyze(regions, req.scale_mm_per_px, image_area_px)
        else:
            raise HTTPException(400, f"Unknown analysis_type: {req.analysis_type}")

        # Convert results to JSON-safe format
        regions_json = []
        for r in results:
            d = {}
            for field in r.__dataclass_fields__:
                d[field] = getattr(r, field)
            regions_json.append(d)

        return AnalysisResponse(regions=regions_json, summary=summary, charts={})
    except Exception as e:
        raise HTTPException(500, str(e))
```

- [ ] **Step 4: Write Celery worker.py**

Create `platform/engine-api/worker.py`:
```python
"""Celery worker for async analysis tasks."""
from celery import Celery
import os

REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379/0")
celery = Celery("engine", broker=REDIS_URI, backend=REDIS_URI)

# Worker will be expanded in later phases
```

- [ ] **Step 5: Copy engine files**

```bash
cp -r core_analysis/engine/image_processor.py platform/engine-api/engine/
cp -r core_analysis/engine/region_extractor.py platform/engine-api/engine/
cp -r core_analysis/engine/morphology_engine.py platform/engine-api/engine/
cp -r core_analysis/engine/hole_analyzer.py platform/engine-api/engine/
cp -r core_analysis/engine/fracture_analyzer.py platform/engine-api/engine/
cp -r core_analysis/engine/grain_analyzer.py platform/engine-api/engine/
cp -r core_analysis/engine/report_generator.py platform/engine-api/engine/
cp -r core_analysis/data/models.py platform/engine-api/engine/
```

- [ ] **Step 6: Verify locally**

```bash
cd platform/engine-api && mkdir -p engine && cp ../../core_analysis/engine/*.py engine/ && cp ../../core_analysis/data/models.py engine/ && pip install -r requirements.txt -q && uvicorn main:app --port 5001 &
sleep 3
curl http://localhost:5001/engine/health
kill %1
```
Expected: `{"status":"ok","engine":"v1.0"}`

- [ ] **Step 7: Commit**

```bash
git add platform/engine-api/
git commit -m "feat: add FastAPI engine with analyze endpoint and copied engine modules"
```

---

### Task 4: Vue3 Frontend Skeleton

**Files:**
- Create: `platform/frontend/package.json`
- Create: `platform/frontend/vite.config.js`
- Create: `platform/frontend/index.html`
- Create: `platform/frontend/src/main.js`
- Create: `platform/frontend/src/App.vue`
- Create: `platform/frontend/src/router/index.js`
- Create: `platform/frontend/src/views/Home.vue`

- [ ] **Step 1: Scaffold Vue3 project**

```bash
cd platform && npm create vite@latest frontend -- --template vue && cd frontend && npm install && npm install vue-router@4 pinia axios
```

- [ ] **Step 2: Write Home.vue**

Create `platform/frontend/src/views/Home.vue`:
```vue
<template>
  <div class="home">
    <h1>岩心孔洞裂缝分析系统</h1>
    <p>企业级数字岩心分析平台 v1.0</p>
    <div class="modules">
      <div class="card" v-for="m in modules" :key="m.key">
        <h3>{{ m.name }}</h3>
        <p>{{ m.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const modules = [
  { key: 'hole', name: '孔洞分析', desc: '自动检测岩心孔洞区域，计算等效直径、面孔率、充填特征' },
  { key: 'fracture', name: '裂缝分析', desc: '识别裂缝并计算长度、宽度、密度、有效性评价' },
  { key: 'grain', name: '粒度分析', desc: '颗粒Feret直径、圆度、Udden-Wentworth粒级分类' },
]
</script>

<style scoped>
.home { max-width: 1200px; margin: 0 auto; padding: 40px 20px; text-align: center; }
.modules { display: flex; gap: 20px; margin-top: 40px; justify-content: center; flex-wrap: wrap; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 24px; width: 280px; text-align: left; }
.card h3 { margin-top: 0; color: #2c3e50; }
</style>
```

- [ ] **Step 3: Write router**

Create `platform/frontend/src/router/index.js`:
```javascript
import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
]

export default createRouter({ history: createWebHistory(), routes })
```

- [ ] **Step 4: Update main.js and App.vue**

Write `platform/frontend/src/main.js`:
```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

Write `platform/frontend/src/App.vue`:
```vue
<template>
  <router-view />
</template>
```

- [ ] **Step 5: Verify**

```bash
cd platform/frontend && npm run dev &
sleep 3
curl http://localhost:5173 | head -5
kill %1
```
Expected: HTML response with "岩心孔洞裂缝分析系统"

- [ ] **Step 6: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add Vue3 frontend skeleton with Home page"
```

---

### Task 5: MongoDB Schemas + Backend Routes

**Files:**
- Create: `platform/backend/src/models/User.js`
- Create: `platform/backend/src/models/Sample.js`
- Create: `platform/backend/src/models/Analysis.js`
- Create: `platform/backend/src/routes/auth.js`
- Create: `platform/backend/src/routes/samples.js`
- Create: `platform/backend/src/routes/analysis.js`
- Create: `platform/backend/src/middleware/auth.js`

- [ ] **Step 1: Write Mongoose models**

Create `platform/backend/src/models/User.js`:
```javascript
import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password_hash: { type: String, required: true },
  role: { type: String, enum: ['admin', 'teacher', 'student'], default: 'student' },
  created_at: { type: Date, default: Date.now }
});

userSchema.pre('save', async function(next) {
  if (this.isModified('password_hash')) {
    this.password_hash = await bcrypt.hash(this.password_hash, 10);
  }
  next();
});

userSchema.methods.comparePassword = function(password) {
  return bcrypt.compare(password, this.password_hash);
};

export default mongoose.model('User', userSchema);
```

Create `platform/backend/src/models/Sample.js`:
```javascript
import mongoose from 'mongoose';

const sampleSchema = new mongoose.Schema({
  sample_id: { type: String, required: true, unique: true },
  basin: { type: String, required: true },
  well_id: { type: String, required: true },
  top_depth: { type: Number, required: true },
  bottom_depth: { type: Number, required: true },
  lithology: { type: Object, default: {} },
  resolution_dpi: { type: Number, enum: [600, 1200], default: 600 },
  image_files: [{ type: mongoose.Schema.Types.ObjectId, ref: 'ImageFile' }],
  created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  created_at: { type: Date, default: Date.now }
});

sampleSchema.index({ basin: 1, well_id: 1 });

export default mongoose.model('Sample', sampleSchema);
```

Create `platform/backend/src/models/Analysis.js`:
```javascript
import mongoose from 'mongoose';

const analysisSchema = new mongoose.Schema({
  sample_id: { type: mongoose.Schema.Types.ObjectId, ref: 'Sample', required: true },
  type: { type: String, enum: ['hole', 'fracture', 'grain', 'mineral'], required: true },
  status: { type: String, enum: ['pending', 'processing', 'done', 'failed'], default: 'pending' },
  params: { type: Object, default: {} },
  results: { type: Object, default: {} },
  report_html: { type: String },
  confidence: { type: Number, min: 0, max: 1 },
  created_by: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  created_at: { type: Date, default: Date.now }
});

export default mongoose.model('Analysis', analysisSchema);
```

- [ ] **Step 2: Write middleware and routes**

Create `platform/backend/src/middleware/auth.js`:
```javascript
import jwt from 'jsonwebtoken';

export function authMiddleware(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET || 'dev-secret');
    next();
  } catch (e) {
    res.status(401).json({ error: 'Invalid token' });
  }
}

export function roleMiddleware(...roles) {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }
    next();
  };
}
```

Create `platform/backend/src/routes/auth.js`:
```javascript
import { Router } from 'express';
import jwt from 'jsonwebtoken';
import User from '../models/User.js';

const router = Router();

router.post('/register', async (req, res) => {
  try {
    const { username, password, role } = req.body;
    const user = await User.create({ username, password_hash: password, role });
    res.status(201).json({ id: user._id, username: user.username, role: user.role });
  } catch (e) {
    res.status(400).json({ error: e.message });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    const user = await User.findOne({ username });
    if (!user || !(await user.comparePassword(password))) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    const token = jwt.sign(
      { id: user._id, username: user.username, role: user.role },
      process.env.JWT_SECRET || 'dev-secret',
      { expiresIn: '24h' }
    );
    res.json({ token, user: { id: user._id, username: user.username, role: user.role } });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
```

- [ ] **Step 3: Wire routes in index.js**

Update `platform/backend/src/index.js` — uncomment the route imports at the bottom:
```javascript
import authRoutes from './routes/auth.js';
import sampleRoutes from './routes/samples.js';
import analysisRoutes from './routes/analysis.js';
app.use('/api/auth', authRoutes);
app.use('/api/samples', sampleRoutes);
app.use('/api/analysis', analysisRoutes);
```

- [ ] **Step 4: Verify**

```bash
cd platform/backend && node src/index.js &
sleep 2
curl -X POST http://localhost:3000/api/auth/register -H "Content-Type: application/json" -d '{"username":"test","password":"123456","role":"student"}'
curl http://localhost:3000/api/health
kill %1
```
Expected: registration success + health check OK.

- [ ] **Step 5: Commit**

```bash
git add platform/backend/
git commit -m "feat: add Mongoose models, auth routes, JWT middleware"
```

---

### Task 6: Docker 集成验证

- [ ] **Step 1: Start all services**

```bash
cd platform && docker compose up -d
```

- [ ] **Step 2: Verify each service**

```bash
curl http://localhost/api/health        # Backend health
curl http://localhost:5001/engine/health  # Engine health
curl http://localhost/                    # Frontend
```

Expected: all respond with expected JSON/HTML.

- [ ] **Step 3: Run desktop tests**

```bash
cd .. && python -m pytest tests/ -q
```
Ensure desktop engine tests still pass (57 tests).

- [ ] **Step 4: Shut down**

```bash
cd platform && docker compose down
```

- [ ] **Step 5: Commit**

```bash
git add platform/
git commit -m "chore: Docker Compose integration verification complete"
```

---

## Summary

| Task | Component | Expected Output |
|---|---|---|
| 1 | Docker Compose | `docker compose config` valid |
| 2 | Node.js Backend | `GET /api/health` → 200 |
| 3 | Python Engine API | `GET /engine/health` → 200 |
| 4 | Vue3 Frontend | `GET /` → 200 HTML |
| 5 | MongoDB + Routes | `POST /api/auth/register` → 201 |
| 6 | Docker Integration | All 6 services up |

Total: 6 services × 可独立验证 = 平台骨架就绪
