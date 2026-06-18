# 岩心孔洞裂缝分析系统 — 企业级 B/S 平台设计文档

> **日期**: 2026-06-18
> **版本**: v3.0 (企业平台)
> **基于**: 桌面版 v2.1 + 需求规格说明书 (软件需求报告.pdf)

---

## 1. 架构总览

```
Frontend (Vue3 + Three.js) :5173
        │
Nginx (静态 + 反向代理) :80/443
        │
Node.js API (Express) :3000     Redis :6379
        │                           │
MongoDB :27017              Python Engine :5001
                            (FastAPI + Celery Worker)
```

---

## 2. 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue3 + Vite + Three.js + Pinia | SPA, WebGL 3D 渲染 |
| Web 后端 | Node.js + Express + JWT | 认证/路由/文件/权限 |
| 分析引擎 | Python FastAPI + Celery | 复用现有 engine/ 模块 |
| 消息队列 | Redis | 异步任务调度 |
| 数据库 | MongoDB | 文档型，JSON 原生存储 |
| 容器化 | Docker Compose | 本地开发/测试 |
| 编排 | Kubernetes (生产) | 弹性伸缩 |
| 监控 | Prometheus + Grafana | 指标采集/告警 |
| CI/CD | GitHub Actions | 自动测试/构建 |

---

## 3. 组件与端口

| 组件 | 技术 | 端口 | 职责 |
|---|---|---|---|
| Nginx | nginx:alpine | 80, 443 | 静态文件 + 反向代理 + HTTPS |
| API Gateway | Node.js + Express | 3000 | 认证(JWT)、路由、文件上传、权限 |
| Analysis Engine | Python FastAPI | 5001 | 图像分析（引擎层） |
| Worker | Celery | — | 异步消费分析任务 |
| Message Queue | Redis | 6379 | 任务队列 + 缓存 |
| Database | MongoDB | 27017 | 所有业务数据 |
| Frontend | Vue3 + Vite | 5173 | 用户界面 |

---

## 4. 数据流

```
用户点击"孔洞分析"
  → Vue3 POST /api/analysis {image_id, type:"hole", params}
  → Node.js validate → MongoDB insert (status:"pending")
  → Node.js push task to Redis queue
  → Celery worker pop task → call Python engine
  → hole_analyzer.py analyze() → return results
  → worker POST results back to Node.js
  → Node.js → MongoDB update (status:"done")
  → WebSocket notify → Vue3 show results
```

---

## 5. 复用清单

从桌面版 `core_analysis/engine/` 直接复制，零改动：

| 文件 | 行数 | 说明 |
|---|---|---|
| `engine/image_processor.py` | ~100 | 预处理、旋转、方向检测 |
| `engine/region_extractor.py` | ~60 | LAB 颜色分割 |
| `engine/morphology_engine.py` | ~80 | 膨胀/腐蚀/去噪/填充 |
| `engine/hole_analyzer.py` | ~60 | 等效直径、面孔率、分类 |
| `engine/fracture_analyzer.py` | ~70 | 骨架化、W=A/L、密度 |
| `engine/grain_analyzer.py` | ~90 | Feret、圆度、粒级 |

`engine/report_generator.py` 需小改：Jinja2 模板 → JSON输出 + 前端 Vue 组件渲染。

---

## 6. 数据库设计 (MongoDB)

### collections

**users**
```json
{
  "_id": ObjectId,
  "username": "zhangsan",
  "password_hash": "$2b$...",
  "role": "student",      // "admin" | "teacher" | "student"
  "created_at": ISODate
}
```

**samples**（岩心样本）
```json
{
  "_id": ObjectId,
  "sample_id": "TAQJ12001SHJ001",
  "basin": "塔里木盆地",
  "well_id": "J12-01",
  "top_depth": 3250.15,
  "bottom_depth": 3250.83,
  "lithology": {"code": "LS", "name": "灰岩"},
  "resolution_dpi": 600,
  "image_files": [
    {"file_id": ObjectId, "format": "TIFF", "width_px": 8000, "height_px": 6000}
  ],
  "created_by": ObjectId,
  "created_at": ISODate
}
```

**analysis_results**（分析结果）
```json
{
  "_id": ObjectId,
  "sample_id": ObjectId,
  "type": "hole",         // "hole" | "fracture" | "grain" | "mineral"
  "status": "done",       // "pending" | "processing" | "done" | "failed"
  "params": {},           // 分析参数
  "results": {
    "regions": [],
    "summary": {},
    "charts": []
  },
  "report_html": "",
  "confidence": 0.92,
  "created_by": ObjectId,
  "created_at": ISODate
}
```

---

## 7. API 端点 (Node.js)

### 认证
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 → JWT |
| GET | /api/auth/me | 当前用户信息 |

### 样本
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/samples | 列表（分页/筛选） |
| POST | /api/samples | 创建 |
| GET | /api/samples/:id | 详情 |
| POST | /api/samples/:id/images | 上传图像 |
| DELETE | /api/samples/:id | 删除（admin） |

### 分析
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/analysis | 提交分析任务 → 返回 task_id |
| GET | /api/analysis/:id | 查询任务状态/结果 |
| GET | /api/analysis/:id/report | 获取报告HTML |

### Python Engine API
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /engine/analyze | 接收图像+参数 → 返回结果 |

---

## 8. 分期实施

| 期数 | 内容 | 预估 |
|---|---|---|
| 第1期 | 平台骨架：Docker + Express + MongoDB + FastAPI引擎 + Vue3壳 | 3-5天 |
| 第2期 | 分析引擎 REST API + 前端交互（上传→分析→报告） | 2-3天 |
| 第3期 | 用户认证 + 三级权限 | 1-2天 |
| 第4期 | 深度学习升级（U-Net孔洞 / Mask R-CNN粒度） | 3-5天 |
| 第5期 | 3D重建（Open3D + Three.js） | 3-5天 |
| 第6期 | CI/CD + 监控 + K8s 部署 | 2-3天 |

---

> **下一步**: 写入实施计划 (writing-plans skill) — 从第1期「平台骨架」开始
