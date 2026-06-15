# 岩心孔洞裂缝分析教学系统 — 设计文档

> **日期**: 2026-06-16
> **版本**: v1.0
> **来源文档**: 岩心孔洞软件.md

---

## 1. 系统概述

### 1.1 项目目标

构建一套**桌面端岩心图像分析教学系统**，对岩心上的裂缝、孔洞进行测量计算分析，为学生提供深入学习的研究平台，满足地质专业实践性教学需求。

### 1.2 目标用户

地质专业学生（本科/研究生），在实验室环境中使用。

### 1.3 核心功能（第一期）

| 序号 | 功能模块 | 说明 |
|---|---|---|
| 1 | 图像库管理 | 按盆地/区块/构造/井号分类管理岩心图像，支持导入、检索、浏览 |
| 2 | 孔洞分析 | 半自动检测孔洞 → 手动微调编辑 → 定量计算 → 统计图表 → 报告 |
| 3 | 裂缝分析 | 半自动检测裂缝 → 手动微调编辑 → 定量计算 → 统计图表 → 报告 |

### 1.4 设计决策汇总

| 决策点 | 选择 |
|---|---|
| 平台形态 | 桌面应用 |
| 技术栈 | Python + PySide6 + OpenCV |
| 架构模式 | 分层 MVC（UI层 / 业务逻辑层 / 数据层） |
| 操作模式 | 半自动型（一键智能检测 + 全手动调节入口） |
| 界面布局 | 经典工具型（左工具条 + 中画布 + 右面板） |
| 数据存储 | SQLite 本地数据库 |
| 图像管理 | 图像库管理（盆地/区块/构造/井号多级分类） |

---

## 2. 系统架构

### 2.1 三层 MVC 架构

```
┌─────────────────────────────────────────────────────────────┐
│  UI 层 (PySide6)                                            │
│  ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐   │
│  │MainWindow│ │ToolPanel│ │ImageCanvas│ │ImageLibrary  │   │
│  │ 菜单/工具│ │左工具条 │ │QGraphics  │ │Widget 图像库│   │
│  │  /状态栏 │ │右参数面板│ │View 3图层│ │分类树+缩略图│   │
│  └──────────┘ └─────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────────┐                                           │
│  │ReportViewer  │  报告浏览 + 导出                          │
│  └──────────────┘                                           │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层 (纯 Python，无 Qt 依赖)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ImageProc  │ │RegionExtr │ │Morphology│ │HoleAnaly │      │
│  │预处理     │ │区域分割   │ │形态学    │ │孔洞分析  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐                                  │
│  │FracAnaly │ │ReportGen │                                  │
│  │裂缝分析  │ │报告生成  │                                  │
│  └──────────┘ └──────────┘                                  │
├─────────────────────────────────────────────────────────────┤
│  数据层 (SQLite)                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                    │
│  │ImageRepo │ │Analysis  │ │Project   │                    │
│  │图像元数据│ │Store结果 │ │Mgr项目   │                    │
│  └──────────┘ └──────────┘ └──────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 关键设计原则

- **分析引擎零 Qt 依赖**：业务逻辑层只依赖 NumPy/OpenCV/SciPy，可脱离 UI 独立测试
- **信号/槽解耦**：UI 通过 Qt Signal/Slot 调用业务层，不直接耦合
- **未来可扩展**：分析引擎接口统一，后期可注册新分析模块

---

## 3. 模块职责与接口

### 3.1 UI 层

| 模块 | 职责 | 核心 Qt 类 |
|---|---|---|
| MainWindow | 主框架：菜单栏、快捷工具栏、状态栏、QDockWidget 管理 | QMainWindow |
| ImageCanvas | 中央画布：原图层 + 提取区域层 + 标注层，支持缩放漫游 | QGraphicsView / QGraphicsScene |
| ToolPanel | 左侧竖排工具条（漫游/选择/分割/橡皮擦/膨胀/腐蚀/画笔） + 右侧参数面板（智能提取/编辑/特征参数） | QToolBar / QWidget |
| ImageLibraryWidget | 可停靠面板：分类树(QTreeView) + 缩略图网格(QListView) | QDockWidget |
| ReportViewer | HTML 报告渲染 + 导出按钮 | QTextBrowser |

### 3.2 业务逻辑层

**ImageProcessor** — 图像预处理
- 输入：`np.ndarray` (BGR图像)
- 操作：自动色阶(`CLAHE`)、灰度化、亮度/对比度、高斯滤波、锐化、Canny边缘
- 输出：`np.ndarray` (处理后图像)

**RegionExtractor** — 区域分割
- 输入：`np.ndarray` + 采样点颜色 + 匹配度参数
- 算法：LAB 颜色空间转换 → `cv2.inRange` 阈值 → `cv2.findContours` 连通域
- 输出：`List[MaskRegion]` (每个区域包含：轮廓点集、面积、质心、bbox)

**MorphologyEngine** — 形态学处理
- 输入：`List[MaskRegion]` + 操作参数
- 操作：膨胀(`cv2.dilate`) / 腐蚀(`cv2.erode`) / 去噪(连通域面积过滤) / 孔洞填充(`cv2.drawContours`)
- 输出：`List[MaskRegion]` (更新后)

**HoleAnalyzer** — 孔洞分析
- 输入：`List[MaskRegion]` + 标尺(scale_value: mm/pixel)
- 计算：
  - 单孔面积：`cv2.contourArea(c) * scale²`
  - 等效直径：`Dr = 2 * sqrt(A / π)`
  - 平均直径：`D̄r = ΣDi / n`
  - 面孔率：`ΣA_hole / A_image`
  - 大小分类：大洞(>10mm) / 中洞(5-10mm) / 小洞(1-4.9mm) / 针孔(<1mm)
- 输出：`HoleAnalysisResult`（结构化数据 + 统计汇总）

**FractureAnalyzer** — 裂缝分析
- 输入：`List[MaskRegion]` + 标尺
- 算法：骨架化(`cv2.ximgproc.thinning`) → 中轴长度 → 宽度 W=A/L
- 计算：
  - 面孔隙度：`ΣA_fracture / A_image`
  - 面密度：`ΣL / A_image` (m/m²)
  - 线密度：`N / L_core` (条/m)
  - 裂缝间距：平均相邻裂缝距离 (mm)
- 输出：`FractureAnalysisResult`（逐条明细 + 成因分类统计）

**ReportGenerator** — 报告生成
- 输入：`AnalysisResult` + 基础信息(井号/深度/岩性/分析人)
- 图表：频率直方图(`plt.bar`) / 累计频率曲线(`np.cumsum` + `plt.plot`) / 正态累计曲线(`scipy.stats.norm.cdf`)
- 输出：HTML 报告字符串（Jinja2 模板渲染，图表 base64 内嵌）

### 3.3 数据层

| 模块 | 职责 |
|---|---|
| ImageRepository | 图像元数据 CRUD、分类树查询、缩略图生成 |
| AnalysisStore | 孔洞/裂缝分析结果持久化、会话管理、历史查询 |
| ProjectManager | SQLite 数据库文件创建/打开/备份 |

---

## 4. 数据库设计

### 4.1 表结构（SQLite，6 张表）

**categories** — 分类树（自引用）
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    type TEXT NOT NULL  -- 'basin'|'block'|'structure'|'well'
);
```

**images** — 图像元数据
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id),
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,        -- 原始文件路径（或副本路径）
    capture_date TEXT,
    depth_from REAL,               -- 起始深度(m)
    depth_to REAL,                 -- 结束深度(m)
    scale_value REAL,              -- mm/pixel
    scale_unit TEXT DEFAULT 'mm',  -- 'mm'|'μm'
    dpi INTEGER,
    lithology TEXT,                -- 岩性描述
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**hole_results** — 孔洞分析结果
```sql
CREATE TABLE hole_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER REFERENCES images(id),
    session_id INTEGER REFERENCES analysis_sessions(id),
    region_index INTEGER,          -- 该图像中的区域序号
    area_mm2 REAL,
    equivalent_d_mm REAL,
    fill_status TEXT,              -- '未充填'|'半充填'|'全充填'
    fill_material TEXT,            -- '方解石'|'白云石'|'泥质'|'沥青'|'石膏'|'黄铁矿'|'高岭石'|'石英'
    effectiveness TEXT,            -- '有效'|'较有效'|'无效'
    hole_type TEXT,                -- '溶洞'|'晶洞'
    size_category TEXT,            -- '大洞'|'中洞'|'小洞'|'针孔/溶孔'
    is_valid BOOLEAN DEFAULT 1,   -- 是否被充填扣除
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**fracture_results** — 裂缝分析结果
```sql
CREATE TABLE fracture_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER REFERENCES images(id),
    session_id INTEGER REFERENCES analysis_sessions(id),
    region_index INTEGER,
    length_mm REAL,
    width_mm REAL,
    area_mm2 REAL,
    porosity REAL,
    fracture_type TEXT,            -- '构造缝'|'成岩缝'|'风化缝'
    fill_status TEXT,              -- '张开缝(未充填)'|'半充填缝'|'充填缝(全充填)'
    fill_material TEXT,
    effectiveness TEXT,
    is_valid BOOLEAN DEFAULT 1,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

**analysis_sessions** — 分析会话
```sql
CREATE TABLE analysis_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_id INTEGER REFERENCES images(id),
    analysis_type TEXT NOT NULL,   -- 'hole'|'fracture'
    params_json TEXT,              -- 分析参数快照
    report_html TEXT,              -- 生成的报告HTML
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### 4.2 实体关系

```
categories (1) ──< (N) images
images (1) ──< (N) hole_results
images (1) ──< (N) fracture_results
images (1) ──< (N) analysis_sessions
analysis_sessions (1) ──< (N) hole_results
analysis_sessions (1) ──< (N) fracture_results
```

---

## 5. UI 布局设计

### 5.1 分析模式主界面

```
┌─────────────────────────────────────────────────────────────┐
│  文件  编辑  查看  处理  分析  帮助          ← 菜单栏       │
├─────────────────────────────────────────────────────────────┤
│ 📁 💾 ↩ ↪ | 🔍自动提取 📊报告 | 📏标尺   📐100% 👁图层  │ ← 工具栏
├────┬──────────────────────────────────┬──────────────────────┤
│ 🖐️ │                                  │ ⚡智能提取           │
│ ⬚  │                                  │  颜色匹配度: [===]   │
│ ▣  │                                  │  ☑连续区域           │
│ 🎯 │       岩心图像 + 提取区域        │  [一键提取]          │
│ 🧹 │       叠加层（半透明）            │                      │
│ 🧹+│                                  │ 🔧区域编辑           │
│ ⭢  │                                  │  去噪 <[10] px       │
│ ⭠  │                                  │  [膨胀] [腐蚀] [填充]│
│ ✏️ │                                  │                      │
│ ▭  │                                  │ 📝特征参数           │
│ ○  │                                  │  充填: [未充填 ▼]    │
│ T  │                                  │  填充物:[方解石 ▼]   │
│    │                                  │  有效性:[有效 ▼]     │
│    │                                  │                      │
│    │                                  │  [修改保存] [查看报告]│
├────┴──────────────────────────────────┴──────────────────────┤
│ 📏 标尺: 0.05 mm/px | 🕳️ 检测: 12个孔洞 | 🖱️ X:342 Y:156 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 图像库面板（可停靠）

```
┌── 图像库 ──────────────────────────────────┐
│ 🔍 [搜索...]  [+导入]                       │
├─────────────────────────────────────────────┤
│ 📁 渤海湾盆地                               │
│  ├─ 📁 辽河坳陷                            │
│  │   ├─ 📁 沙河街组                        │
│  │   │   ├─ 🖼️ J12-3井 (12)               │
│  │   │   └─ 🖼️ J15-7井 (8)                │
│  │   └─ 📁 东营组                          │
│  └─ 📁 黄骅坳陷                            │
├─────────────────────────────────────────────┤
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐          │
│ │1560m│ │1562m│ │1564m│ │1566m│          │
│ └─────┘ └─────┘ └─────┘ └─────┘          │
│ ┌─────┐ ┌─────┐                           │
│ │1568m│ │1570m│          ← 缩略图网格      │
│ └─────┘ └─────┘                           │
└─────────────────────────────────────────────┘
```

### 5.3 关键 UI 特性

- **3 层图层叠加**：QGraphicsScene 管理原图层 → 提取区域层(半透明红) → 标注层(序号/文字)，独立开关
- **可停靠面板**：QDockWidget 实现图像库面板可停靠/浮动/隐藏
- **操作撤销栈**：QUndoStack 驱动撤销/还原，覆盖所有编辑操作
- **双模式标尺**：宏观(DPI自动计算 mm/px) / 微观(手动输入 μm/px)

---

## 6. 核心算法

### 6.1 孔洞分析处理管线

```
预处理          颜色分割          连通域提取        形态学后处理
CLAHE均衡  →   LAB空间inRange  →  findContours  →  dilate/erode
自动色阶        用户拾取孔洞色     面积过滤          去噪/孔洞填充
                                     ↓
          参数计算                        统计图表
          Dr=2√(A/π)                   频率直方图
          D̄r=ΣDi/n                    累计频率曲线
          面孔率                        正态累计曲线
```

### 6.2 裂缝分析处理管线

```
预处理            裂缝提取              骨架化            参数计算
灰度化+Gaussian  → Canny边缘检测  →  Zhang-Suen细化  →  W=A/L
                  HoughLinesP                            面密度/线密度
                  线段合并连接                          裂缝间距
```

### 6.3 核心 OpenCV 函数

| 步骤 | 函数 | 说明 |
|---|---|---|
| 预处理 | `cv2.createCLAHE`, `cv2.equalizeHist` | 自适应直方图均衡 |
| 颜色分割 | `cv2.cvtColor(..., LAB)`, `cv2.inRange` | LAB空间阈值 |
| 连通域 | `cv2.findContours`, `cv2.connectedComponentsWithStats` | 区域提取+面积过滤 |
| 形态学 | `cv2.dilate`, `cv2.erode`, `cv2.morphologyEx` | 膨胀/腐蚀 |
| 骨架化 | `cv2.ximgproc.thinning` | Zhang-Suen细化 |
| 图表 | `matplotlib.pyplot` → `FigureCanvas` | 直方图/曲线 |

### 6.4 半自动对照表

| 步骤 | 自动做什么 | 手动可调什么 |
|---|---|---|
| 预处理 | 自动色阶一键执行 | 所有滤镜手动微调 |
| 区域提取 | 点击孔洞 → 自动分割所有相似区域 | 颜色匹配度滑块、连续/全局切换 |
| 形态学 | 自动去噪(<10px) + 自动填充 | 去噪阈值、膨胀/腐蚀方向和次数 |
| 编辑 | — | 橡皮擦(增/删)、画笔、局部膨胀/腐蚀 |
| 参数 | 自动计算所有定量指标 | 充填状态/充填物/有效性 人工判定 |

---

## 7. 报告格式

### 7.1 生成方案

- **模板引擎**：Jinja2 渲染 HTML 报告
- **图表嵌入**：matplotlib savefig → base64 内嵌 `<img>` 标签，单 HTML 文件可离线查看
- **导出格式**：HTML(默认) / PDF(Qt QPrinter) / CSV(Excel数据表)
- **存储**：report_html 存入 analysis_sessions 表，支持历史回溯

### 7.2 孔洞分析报告内容

1. 基础信息（图像编号/井号/深度/层位/岩性/标尺/分析日期/分析人）
2. 孔洞检测统计（总数/总面积/平均面积/面孔率/最大/最小/平均等效直径）
3. 充填特征（未充填/半充填/全充填 各数量/面积/占比）
4. 有效性评价（有效/较有效/无效 各数量）
5. 孔洞大小分布（大洞/中洞/小洞/针孔各数量/占比）
6. 附图（频率直方图、累计频率曲线、正态累计曲线）

### 7.3 裂缝分析报告内容

1. 基础信息
2. 裂缝检测统计（总条数/总面积/面孔隙度/累计长度/面密度/线密度/平均间距）
3. 裂缝明细表（逐条：长度/宽度/类型/充填/有效性）
4. 裂缝成因分类（构造缝/成岩缝/风化缝 各条数/总长）
5. 缝洞关系描述（缝连洞/切割缝/缝合缝 各几处）
6. 附件（原图 + 提取区域标注图 + 骨架化图）

---

## 8. 技术栈

| 类别 | 技术 | 用途 |
|---|---|---|
| 语言 | Python 3.10+ | 主语言 |
| UI框架 | PySide6 | 桌面GUI |
| 图像处理 | OpenCV (cv2) | 所有图像算法 |
| 数值计算 | NumPy, SciPy | 统计计算 |
| 图表 | matplotlib | 频率曲线/直方图 |
| 模板 | Jinja2 | HTML报告渲染 |
| 数据库 | SQLite3 (内置) | 图像库+分析结果 |
| 打包 | PyInstaller | 分发exe |

---

## 9. 不在第一期范围内的功能

以下功能在原始文档中有描述但不在第一期实施范围：

- 粒度分析
- 荧光分析
- 铸体分析
- 矿物分析
- 三维恢复
- 自动旋转
- 沉积知识库

---

## 10. 待确认事项

无。所有设计决策已在脑力激荡阶段确认完毕。

---

> **下一步**: 写入实施计划 (writing-plans skill)
