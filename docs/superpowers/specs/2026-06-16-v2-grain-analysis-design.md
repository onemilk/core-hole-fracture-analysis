# 岩心孔洞裂缝分析教学系统 v2 第二期：粒度分析 — 设计文档

> **日期**: 2026-06-16
> **版本**: v2-phase-2
> **基于**: v2.0 (旋转工具 + 知识库)

---

## 本期功能

| 功能 | 说明 |
|---|---|
| 粒度分析 | 砾岩颗粒半自动提取 + 逐颗粒测量 + 整体统计 + 报告 |

---

## 1. 架构

```
图像 → RegionExtractor（颜色分割，复用孔洞管线）
     → MorphologyEngine（去噪/编辑，复用）
     → GrainAnalyzer（新增：Feret直径/圆度/分选参数）
     → ReportGenerator（新增粒度图表）
```

---

## 2. 逐颗粒参数

| 参数 | 算法 | 单位 |
|---|---|---|
| 面积 | `cv2.contourArea(c) * scale²` | mm² |
| 等效直径 | `Dr = 2√(A/π)` | mm |
| 周长 | `cv2.arcLength(c) * scale` | mm |
| Feret 长轴 | `cv2.minAreaRect` 长边 | mm |
| Feret 短轴 | `cv2.minAreaRect` 短边 | mm |
| 圆度 | `4πA / P²`（1=完美圆，<1=偏离圆） | — |

---

## 3. 整体统计参数

| 参数 | 算法 |
|---|---|
| 频率直方图 | `np.histogram(diameters)` → bar chart |
| 累计频率曲线 | `np.cumsum` → line plot |
| 中值粒径 Md | 累计频率 50% 对应粒径，`np.percentile(diameters, 50)` |
| 平均粒径 Mz | `np.mean(diameters)` |
| 标准偏差 σ | `np.std(diameters)` |
| 粒级分类 | Udden-Wentworth：砾(>2mm) / 砂(0.0625-2mm) / 粉砂(0.0039-0.0625mm) / 泥(<0.0039mm) |

---

## 4. UI

菜单「分析 → 粒度分析」切换模式。

右侧 ToolPanel 新增分组：
- 粒级分类标准下拉框（Udden-Wentworth）
- ☑ 显示Feret直径
- ☑ 显示颗粒序号

工具栏「自动提取」和「生成报告」自动调用 GrainAnalyzer。

---

## 5. 报告

`templates/grain_report.html`：
1. 基础信息
2. 粒度检测统计（总数/平均粒径/中值粒径/标准偏差）
3. 粒度分布表（粒级分类数量占比）
4. 附图：频率直方图、累计频率曲线、Feret长轴-短轴散点图

---

## 6. 文件变更

| 文件 | 操作 | 说明 |
|---|---|---|
| `engine/grain_analyzer.py` | **新建** | GrainAnalyzer 类 |
| `templates/grain_report.html` | **新建** | 粒度报告模板 |
| `ui/main_window.py` | 修改 | 菜单「分析→粒度分析」+ 分析类型切换 |
| `ui/tool_panel.py` | 修改 | 粒度参数面板 |
| `engine/report_generator.py` | 修改 | 新增粒度图表 + 渲染方法 |
| `data/models.py` | 修改 | 新增 GrainResult dataclass |
| `data/analysis_store.py` | 修改 | 新增 grain_results CRUD |
| `data/database.py` | 修改 | 新增 grain_results 表 |
| `tests/test_grain_analyzer.py` | **新建** | 粒度分析测试 |

---

> **下一步**: 写入实施计划 (writing-plans skill)