# 岩心孔洞裂缝分析教学系统 v2 第一期 — 设计文档

> **日期**: 2026-06-16
> **版本**: v2-phase-1
> **基于**: v1.0 (2026-06-16-core-hole-fracture-analysis-design.md)

---

## 本期功能

| 功能 | 类型 | 说明 |
|---|---|---|
| 自动旋转 + 手动旋转 | 图像工具 | 自动检测岩心方向并校正，支持手动旋转/翻转 |
| 沉积知识库 | 内容功能 | 内置沉积学知识 JSON，分类树搜索浏览 |

---

## 1. 自动旋转 + 手动旋转

### 1.1 自动旋转

**算法**：
```
Canny边缘检测 → HoughLinesP概率霍夫变换 → 统计主导方向角度 → cv2.rotate + 仿射变换校正
```

**核心逻辑**：
1. 将图像灰度化 + Canny 边缘提取
2. 用 `cv2.HoughLinesP` 检测线段
3. 收集所有线段角度，取中位数作为主导方向
4. 计算偏角（与水平/竖直的差值）
5. 用 `cv2.warpAffine` 旋转校正
6. 同时旋转所有已提取的 MaskRegion

**触发方式**：菜单「处理 → 自动旋转校正」或快捷键

### 1.2 手动旋转

**工具栏按钮**：

| 按钮 | 操作 | 角度 |
|---|---|---|
| ↺ | 左转 | -90° |
| ↻ | 右转 | +90° |
| ↩ | 水平翻转 | — |
| ↕ | 竖直翻转 | — |

**菜单**：「处理 → 旋转 → 90°左转 / 90°右转 / 180° / 水平翻转 / 竖直翻转 / 自定义角度...」

自定义角度弹出 `QInputDialog` 输入任意角度（-180~180）。

### 1.3 模块改动

| 文件 | 改动 |
|---|---|
| `engine/image_processor.py` | 新增: `detect_orientation()`, `auto_rotate()`, `rotate(image, angle)`, `flip_horizontal(image)`, `flip_vertical(image)` |
| `engine/morphology_engine.py` | 新增: `rotate_region(region, angle, image_shape)` — 对 MaskRegion 做旋转 |
| `ui/main_window.py` | 工具栏添加旋转按钮，菜单添加「处理 → 旋转」子菜单，连接信号 |
| `ui/image_canvas.py` | 新增: `rotate_regions(angle)` — 旋转画布上的所有区域 |

### 1.4 测试

- `test_rotation.py`: 测试霍夫线角度检测、图像旋转、区域旋转一致性、翻转对称性

---

## 2. 沉积知识库

### 2.1 数据文件

`core_analysis/data/sedimentary_knowledge.json`

结构：
```
{
  "categories": {
    "<分类名>": {
      "<条目名>": {
        "definition": "<定义文本>",
        "related": ["<相关条目1>", "<相关条目2>"]
      }
    }
  }
}
```

**内置 6 个分类**：
1. 沉积岩分类 — 碳酸盐岩、碎屑岩、蒸发岩等
2. 沉积构造 — 层理、交错层理、波痕等
3. 成岩作用 — 压实、胶结、溶解、交代等
4. 孔隙类型 — 原生孔、次生孔、晶间孔等
5. 常见矿物 — 方解石、白云石、石英、长石等
6. 常用术语 — 面孔率、等效直径、缝合线等

**初始条目数**：约 30-40 条，覆盖基础教学需求

### 2.2 UI

菜单「帮助 → 沉积知识库」打开独立窗口：

```
KnowledgeDialog(QDialog)
├── 顶部: QLineEdit 搜索框（实时过滤）
├── 左侧: QTreeWidget 分类树
└── 右侧: QTextBrowser 详情（definition + 相关条目超链接）
```

- 点击左侧条目 → 右侧显示定义
- 搜索框输入 → 实时过滤匹配条目名和定义文本
- 点击「相关」链接 → 跳转到对应条目

### 2.3 模块

| 文件 | 说明 |
|---|---|
| `core_analysis/data/sedimentary_knowledge.json` | 知识库数据 |
| `core_analysis/ui/knowledge_dialog.py` | 知识库窗口 |
| `core_analysis/ui/main_window.py` | 菜单项「帮助 → 沉积知识库」 |

### 2.4 如何更新知识库

1. 编辑 `core_analysis/data/sedimentary_knowledge.json`
2. 按现有结构添加/修改条目
3. 重启应用即可
4. 确保 JSON 格式正确（可用 VS Code 的 JSON 校验）

### 2.5 测试

- `test_knowledge.py`: 测试 JSON 文件可解析、结构完整、搜索逻辑正确

---

## 3. 文件变更总览

| 文件 | 操作 | 说明 |
|---|---|---|
| `engine/image_processor.py` | 修改 | 添加旋转相关方法 |
| `engine/morphology_engine.py` | 修改 | 添加区域旋转方法 |
| `ui/main_window.py` | 修改 | 工具栏旋转按钮 + 知识库菜单 |
| `ui/image_canvas.py` | 修改 | 添加区域旋转方法 |
| `ui/knowledge_dialog.py` | **新建** | 知识库窗口 |
| `data/sedimentary_knowledge.json` | **新建** | 知识库数据 |
| `tests/test_rotation.py` | **新建** | 旋转功能测试 |
| `tests/test_knowledge.py` | **新建** | 知识库测试 |

---

> **下一步**: 写入实施计划 (writing-plans skill)
