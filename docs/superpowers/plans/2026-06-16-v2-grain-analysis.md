# v2 第二期：粒度分析 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为岩心孔洞裂缝分析教学系统添加砾岩粒度分析模块，支持颗粒逐参数测量和整体统计。

**Architecture:** 复用现有 RegionExtractor + MorphologyEngine 提取管线，新增 GrainAnalyzer 计算 Feret 直径/圆度/粒级分类，生成粒度报告。

**Tech Stack:** Python 3.10+, OpenCV, NumPy, Jinja2, matplotlib, PySide6

---

## 文件变更结构

```
core_analysis/
├── data/
│   ├── models.py          [修改] +GrainResult
│   ├── database.py        [修改] +grain_results 表
│   └── analysis_store.py  [修改] +grain_results CRUD
├── engine/
│   ├── grain_analyzer.py  [新建]
│   └── report_generator.py [修改] +粒度图表+渲染
├── ui/
│   ├── main_window.py     [修改] 分析类型切换
│   └── tool_panel.py      [修改] 粒度参数面板
└── templates/
    └── grain_report.html  [新建]

tests/
└── test_grain_analyzer.py [新建]
```

---

### Task 1: GrainResult Model + Database

**Files:**
- Modify: `core_analysis/data/models.py`
- Modify: `core_analysis/data/database.py`

- [ ] **Step 1: Add GrainResult dataclass to models.py**

Read `core_analysis/data/models.py`. Append at end:
```python
@dataclass
class GrainResult:
    """单颗粒分析结果"""
    id: Optional[int] = None
    image_id: Optional[int] = None
    session_id: Optional[int] = None
    region_index: int = 0
    area_mm2: float = 0.0
    equivalent_d_mm: float = 0.0
    perimeter_mm: float = 0.0
    feret_long_mm: float = 0.0
    feret_short_mm: float = 0.0
    circularity: float = 0.0
    size_category: str = ""
    is_valid: bool = True
    notes: str = ""
    created_at: str = ""
```

- [ ] **Step 2: Add grain_results table to database.py**

Read `core_analysis/data/database.py`. Add to `initialize()` method's executescript (after fracture_results table):
```sql
            CREATE TABLE IF NOT EXISTS grain_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER REFERENCES images(id),
                session_id INTEGER REFERENCES analysis_sessions(id),
                region_index INTEGER,
                area_mm2 REAL,
                equivalent_d_mm REAL,
                perimeter_mm REAL,
                feret_long_mm REAL,
                feret_short_mm REAL,
                circularity REAL,
                size_category TEXT,
                is_valid BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
```

- [ ] **Step 3: Verify**

```bash
python -c "from core_analysis.data.models import GrainResult; print('GrainResult OK')"
python -c "from core_analysis.data.database import ProjectManager; p=ProjectManager(':memory:'); p.initialize(); print('DB OK')"
```
Expected: `GrainResult OK` and `DB OK`

- [ ] **Step 4: Commit**

```bash
git add core_analysis/data/models.py core_analysis/data/database.py
git commit -m "feat: add GrainResult model and grain_results table"
```

---

### Task 2: AnalysisStore — Grain Results CRUD

**Files:**
- Modify: `core_analysis/data/analysis_store.py`

- [ ] **Step 1: Add save/load methods**

Read `core_analysis/data/analysis_store.py`. Append to AnalysisStore class:
```python
    def save_grain_results(self, results: list):
        conn = self.pm.get_connection()
        conn.execute("DELETE FROM grain_results WHERE session_id = ?",
                     (results[0].session_id,))
        for r in results:
            conn.execute(
                """INSERT INTO grain_results
                   (image_id, session_id, region_index, area_mm2, equivalent_d_mm,
                    perimeter_mm, feret_long_mm, feret_short_mm, circularity,
                    size_category, is_valid, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r.image_id, r.session_id, r.region_index, r.area_mm2,
                 r.equivalent_d_mm, r.perimeter_mm, r.feret_long_mm,
                 r.feret_short_mm, r.circularity, r.size_category,
                 int(r.is_valid), r.notes)
            )
        conn.commit()
        conn.close()

    def get_grain_results(self, session_id: int) -> list:
        conn = self.pm.get_connection()
        rows = conn.execute(
            "SELECT * FROM grain_results WHERE session_id = ? ORDER BY region_index",
            (session_id,)
        ).fetchall()
        conn.close()
        from core_analysis.data.models import GrainResult
        return [GrainResult(
            id=r["id"], image_id=r["image_id"], session_id=r["session_id"],
            region_index=r["region_index"], area_mm2=r["area_mm2"],
            equivalent_d_mm=r["equivalent_d_mm"],
            perimeter_mm=r["perimeter_mm"] or 0.0,
            feret_long_mm=r["feret_long_mm"] or 0.0,
            feret_short_mm=r["feret_short_mm"] or 0.0,
            circularity=r["circularity"] or 0.0,
            size_category=r["size_category"] or "",
            is_valid=bool(r["is_valid"]),
            notes=r["notes"] or "", created_at=r["created_at"] or ""
        ) for r in rows]
```

- [ ] **Step 2: Verify**

```bash
python -c "from core_analysis.data.analysis_store import AnalysisStore; print('OK')"
```

- [ ] **Step 3: Run existing tests**

```bash
python -m pytest tests/ -q
```
Ensure all pass.

- [ ] **Step 4: Commit**

```bash
git add core_analysis/data/analysis_store.py
git commit -m "feat: add grain_results CRUD to AnalysisStore"
```

---

### Task 3: GrainAnalyzer Engine

**Files:**
- Create: `core_analysis/engine/grain_analyzer.py`
- Create: `tests/test_grain_analyzer.py`

- [ ] **Step 1: Write failing test**

Write `tests/test_grain_analyzer.py`:
```python
"""Tests for GrainAnalyzer"""
import numpy as np
import cv2
from core_analysis.engine.grain_analyzer import GrainAnalyzer
from core_analysis.data.models import MaskRegion


def _make_circular_region():
    mask = np.zeros((100, 100), dtype=np.uint8)
    cv2.circle(mask, (50, 50), 25, 255, -1)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return MaskRegion(
        contour=cnts[0].squeeze(1).tolist(),
        area_px=cv2.contourArea(cnts[0]),
        centroid=(50, 50),
        bbox=(25, 25, 50, 50)
    )


class TestGrainAnalyzer:
    def test_analyze_single_grain(self):
        region = _make_circular_region()
        scale = 0.05
        image_area_px = 10000
        results, summary = GrainAnalyzer.analyze([region], scale, image_area_px)
        assert len(results) == 1
        r = results[0]
        assert r.area_mm2 > 0
        assert r.equivalent_d_mm > 0
        assert r.perimeter_mm > 0
        assert r.feret_long_mm > 0
        assert 0 < r.circularity <= 1.0

    def test_feret_dimensions(self):
        region = _make_circular_region()
        scale = 0.05
        image_area_px = 10000
        results, _ = GrainAnalyzer.analyze([region], scale, image_area_px)
        r = results[0]
        # Circle: feret_long ~ feret_short
        ratio = r.feret_long_mm / max(r.feret_short_mm, 0.001)
        assert ratio < 1.5

    def test_size_classification(self):
        region = _make_circular_region()
        scale = 1.0  # large scale → 砾石
        image_area_px = 10000
        results, _ = GrainAnalyzer.analyze([region], scale, image_area_px)
        assert results[0].size_category == "砾"

    def test_empty_regions(self):
        results, summary = GrainAnalyzer.analyze([], 0.05, 10000)
        assert results == []
        assert summary["total_count"] == 0
        assert summary["avg_diameter_mm"] == 0.0

    def test_summary_statistics(self):
        region = _make_circular_region()
        scale = 0.05
        image_area_px = 10000
        _, summary = GrainAnalyzer.analyze([region], scale, image_area_px)
        assert summary["total_count"] == 1
        assert summary["avg_diameter_mm"] > 0
        assert "md_diameter_mm" in summary
        assert "std_dev_mm" in summary
        assert "size_distribution" in summary
```

Run: `python -m pytest tests/test_grain_analyzer.py -v` — Expected: FAIL

- [ ] **Step 2: Implement GrainAnalyzer**

Write `core_analysis/engine/grain_analyzer.py`:
```python
"""GrainAnalyzer — quantitative grain analysis from extracted regions."""

import math
import cv2
import numpy as np
from core_analysis.data.models import MaskRegion, GrainResult


class GrainAnalyzer:
    @staticmethod
    def analyze(regions: list, scale_mm_per_px: float,
                image_area_px: float) -> tuple:
        results = []
        diameters = []

        for i, region in enumerate(regions):
            area_mm2 = region.area_px * (scale_mm_per_px ** 2)
            perimeter_px = cv2.arcLength(
                np.array(region.contour, dtype=np.int32).reshape(-1, 1, 2), True
            ) if len(region.contour) > 2 else 0.0
            perimeter_mm = perimeter_px * scale_mm_per_px
            d = 2.0 * math.sqrt(area_mm2 / math.pi)
            circularity = (4.0 * math.pi * area_mm2 / (perimeter_mm ** 2)) \
                          if perimeter_mm > 0 else 0.0

            # Feret diameters via minAreaRect
            pts = np.array(region.contour, dtype=np.int32).reshape(-1, 1, 2)
            rect = cv2.minAreaRect(pts) if len(pts) >= 5 else None
            if rect:
                feret_long = max(rect[1]) * scale_mm_per_px
                feret_short = min(rect[1]) * scale_mm_per_px
            else:
                feret_long = feret_short = d

            size_cat = GrainAnalyzer._classify_size(d)

            result = GrainResult(
                region_index=i,
                area_mm2=round(area_mm2, 4),
                equivalent_d_mm=round(d, 4),
                perimeter_mm=round(perimeter_mm, 4),
                feret_long_mm=round(feret_long, 4),
                feret_short_mm=round(feret_short, 4),
                circularity=round(circularity, 4),
                size_category=size_cat
            )
            results.append(result)
            diameters.append(d)

        n = len(results)
        avg_d = round(sum(diameters) / n, 4) if n > 0 else 0.0
        md = round(float(np.percentile(diameters, 50)), 4) if diameters else 0.0
        std = round(float(np.std(diameters)), 4) if diameters else 0.0

        size_dist = {"砾": 0, "砂": 0, "粉砂": 0, "泥": 0}
        for r in results:
            if r.size_category in size_dist:
                size_dist[r.size_category] += 1

        summary = {
            "total_count": n,
            "avg_diameter_mm": avg_d,
            "md_diameter_mm": md,
            "std_dev_mm": std,
            "max_diameter_mm": round(max(diameters), 4) if diameters else 0.0,
            "min_diameter_mm": round(min(diameters), 4) if diameters else 0.0,
            "size_distribution": size_dist,
            "diameters": diameters,
        }
        return results, summary

    @staticmethod
    def _classify_size(diameter_mm: float) -> str:
        if diameter_mm > 2:
            return "砾"
        elif diameter_mm >= 0.0625:
            return "砂"
        elif diameter_mm >= 0.0039:
            return "粉砂"
        else:
            return "泥"
```

Run: `python -m pytest tests/test_grain_analyzer.py -v` — Expected: 5 passed

- [ ] **Step 3: Run all tests**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 4: Commit**

```bash
git add core_analysis/engine/grain_analyzer.py tests/test_grain_analyzer.py
git commit -m "feat: add GrainAnalyzer with Feret, circularity, Udden-Wentworth classification"
```

---

### Task 4: Grain Report Template + Charts

**Files:**
- Create: `core_analysis/templates/grain_report.html`
- Modify: `core_analysis/engine/report_generator.py`

- [ ] **Step 1: Write grain report template**

Write `core_analysis/templates/grain_report.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>岩心粒度分析报告</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; padding: 20px; color: #333; }
  h1 { text-align: center; font-size: 18px; }
  h2 { font-size: 15px; border-bottom: 1px solid #333; margin-top: 24px; }
  table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 13px; }
  th, td { border: 1px solid #666; padding: 4px 8px; text-align: left; }
  th { background: #f0f0f0; }
  .info td { border: none; }
  .chart { text-align: center; margin: 16px 0; }
  .chart img { max-width: 100%; }
</style>
</head>
<body>
<h1>砾岩岩心粒度分析报告</h1>

<h2>基础信息</h2>
<table class="info">
  <tr><td><b>图像编号:</b> {{ info.image_id }}</td><td><b>井号:</b> {{ info.well }}</td></tr>
  <tr><td><b>深度:</b> {{ info.depth }} m</td><td><b>层位:</b> {{ info.layer }}</td></tr>
  <tr><td><b>岩性:</b> {{ info.lithology }}</td><td><b>标尺:</b> {{ info.scale }} mm/px</td></tr>
  <tr><td><b>分析日期:</b> {{ info.date }}</td><td><b>分析人:</b> {{ info.analyst }}</td></tr>
</table>

<h2>一、粒度检测统计</h2>
<table>
  <tr><th>指标</th><th>值</th><th>单位</th></tr>
  <tr><td>颗粒总数</td><td>{{ summary.total_count }}</td><td>个</td></tr>
  <tr><td>平均粒径</td><td>{{ summary.avg_d_mm }}</td><td>mm</td></tr>
  <tr><td>中值粒径 Md</td><td>{{ summary.md_mm }}</td><td>mm</td></tr>
  <tr><td>标准偏差 σ</td><td>{{ summary.std_mm }}</td><td>mm</td></tr>
  <tr><td>最大粒径</td><td>{{ summary.max_mm }}</td><td>mm</td></tr>
  <tr><td>最小粒径</td><td>{{ summary.min_mm }}</td><td>mm</td></tr>
</table>

<h2>二、粒度分布（Udden-Wentworth）</h2>
<table>
  <tr><th>粒级</th><th>粒径范围</th><th>数量</th><th>占比</th></tr>
  {% for item in size_dist %}
  <tr><td>{{ item.category }}</td><td>{{ item.range }}</td><td>{{ item.count }}</td><td>{{ item.percent }}%</td></tr>
  {% endfor %}
</table>

<h2>三、附图</h2>
{% if charts.histogram %}
<div class="chart"><img src="data:image/png;base64,{{ charts.histogram }}" alt="频率直方图"></div>
{% endif %}
{% if charts.cumulative %}
<div class="chart"><img src="data:image/png;base64,{{ charts.cumulative }}" alt="累计频率曲线"></div>
{% endif %}
{% if charts.feret %}
<div class="chart"><img src="data:image/png;base64,{{ charts.feret }}" alt="Feret散点图"></div>
{% endif %}
</body>
</html>
```

- [ ] **Step 2: Add grain report method + charts to ReportGenerator**

Read `core_analysis/engine/report_generator.py`. Append to ReportGenerator class:

```python
    @classmethod
    def generate_grain_report(cls, summary: dict, info: dict) -> str:
        charts = cls._generate_grain_charts(summary.get("diameters", []),
                                            summary.get("feret_data", []))
        size_dist = cls._build_grain_size_table(
            summary.get("size_distribution", {}),
            summary.get("total_count", 0))
        template = cls._env.get_template("grain_report.html")
        html = template.render(
            info=info,
            summary={
                "total_count": summary["total_count"],
                "avg_d_mm": summary["avg_diameter_mm"],
                "md_mm": summary["md_diameter_mm"],
                "std_mm": summary["std_dev_mm"],
                "max_mm": summary["max_diameter_mm"],
                "min_mm": summary["min_diameter_mm"],
            },
            size_dist=size_dist,
            charts=charts
        )
        return html

    @classmethod
    def _generate_grain_charts(cls, diameters: list, feret_data: list) -> dict:
        if not diameters:
            return {"histogram": "", "cumulative": "", "feret": ""}
        diameters = np.array(diameters)
        charts = {}

        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.hist(diameters, bins=min(12, len(diameters)), edgecolor='black', alpha=0.7)
        ax.set_xlabel("粒径 (mm)", fontsize=12)
        ax.set_ylabel("频数", fontsize=12)
        ax.set_title("粒度频率直方图", fontsize=14)
        ax.tick_params(labelsize=10)
        charts["histogram"] = cls._fig_to_b64(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        sorted_d = np.sort(diameters)
        cumulative = np.arange(1, len(sorted_d) + 1) / len(sorted_d) * 100
        ax.plot(sorted_d, cumulative, 'b-o', markersize=4, linewidth=1.5)
        ax.set_xlabel("粒径 (mm)", fontsize=12)
        ax.set_ylabel("累计频率 (%)", fontsize=12)
        ax.set_title("粒度累计频率曲线", fontsize=14)
        ax.tick_params(labelsize=10)
        charts["cumulative"] = cls._fig_to_b64(fig)
        plt.close(fig)

        if feret_data:
            fig, ax = plt.subplots(figsize=(7.5, 4.5))
            longs = [f[0] for f in feret_data]
            shorts = [f[1] for f in feret_data]
            ax.scatter(shorts, longs, alpha=0.6, s=20)
            max_val = max(max(longs), max(shorts)) * 1.1
            ax.plot([0, max_val], [0, max_val], 'r--', lw=1, alpha=0.5)
            ax.set_xlabel("Feret 短轴 (mm)", fontsize=12)
            ax.set_ylabel("Feret 长轴 (mm)", fontsize=12)
            ax.set_title("Feret 长轴-短轴散点图", fontsize=14)
            ax.tick_params(labelsize=10)
            charts["feret"] = cls._fig_to_b64(fig)
            plt.close(fig)
        else:
            charts["feret"] = ""

        return charts

    @staticmethod
    def _build_grain_size_table(size_dist: dict, total: int) -> list:
        ranges = {"砾": ">2mm", "砂": "0.0625-2mm", "粉砂": "0.0039-0.0625mm", "泥": "<0.0039mm"}
        return [{"category": k, "range": ranges.get(k, ""),
                 "count": size_dist.get(k, 0),
                 "percent": round(size_dist.get(k, 0) / total * 100, 1) if total > 0 else 0}
                for k in ("砾", "砂", "粉砂", "泥")]
```

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 4: Commit**

```bash
git add core_analysis/engine/report_generator.py core_analysis/templates/grain_report.html
git commit -m "feat: add grain report template and chart generation"
```

---

### Task 5: UI — Analysis Type Switch + Grain Panel

**Files:**
- Modify: `core_analysis/ui/main_window.py`
- Modify: `core_analysis/ui/tool_panel.py`

- [ ] **Step 1: Add "粒度分析" to menu**

Read `core_analysis/ui/main_window.py`. Find `analysis_menu.addAction("裂缝分析"...`. After it add:
```python
        analysis_menu.addAction("粒度分析", lambda: self._set_analysis_type("grain"))
```

- [ ] **Step 2: Handle "grain" in _generate_report**

Find `_generate_report`. After the `if self._analysis_type == "hole": ... else:` block, add a new branch for grain. The current code is:
```python
        if self._analysis_type == "hole":
            ...
        else:
            ...  # fracture
```

Change to:
```python
        if self._analysis_type == "hole":
            results, summary = HoleAnalyzer.analyze(self._canvas.regions, scale, image_area_px)
            fill_stats = [{"status": "未充填", "count": len(results), "area": summary["total_area_mm2"], "percent": 100}]
            effect = {"valid": len(results), "semi_valid": 0, "invalid": 0}
            html = ReportGenerator.generate_hole_report(summary, fill_stats, effect, info)
        elif self._analysis_type == "grain":
            from core_analysis.engine.grain_analyzer import GrainAnalyzer
            results, summary = GrainAnalyzer.analyze(self._canvas.regions, scale, image_area_px)
            feret_data = [(r.feret_long_mm, r.feret_short_mm) for r in results]
            summary["feret_data"] = feret_data
            html = ReportGenerator.generate_grain_report(summary, info)
        else:
            ...  # fracture (existing code)
```

And update the final persistence block (after all branches) to also handle grain:
```python
        for r in results:
            r.image_id = self._current_image_id
            r.session_id = session_id
        if self._analysis_type == "hole":
            self._store.save_hole_results(results)
        elif self._analysis_type == "grain":
            self._store.save_grain_results(results)
        else:
            self._store.save_fracture_results(results)
```

Replace the old persistence block which was:
```python
        for r in results:
            r.image_id = self._current_image_id
            r.session_id = session_id
        if self._analysis_type == "hole":
            self._store.save_hole_results(results)
        else:
            self._store.save_fracture_results(results)
```

- [ ] **Step 3: Add grain label to status bar**

Update `_set_analysis_type`:
```python
    def _set_analysis_type(self, atype: str):
        self._analysis_type = atype
        type_names = {"hole": "孔洞分析", "fracture": "裂缝分析", "grain": "粒度分析"}
        self.setWindowTitle(f"岩心孔洞裂缝分析教学系统 — {type_names.get(atype, '')}")
```

- [ ] **Step 4: Verify**

```bash
python -c "from core_analysis.ui.main_window import MainWindow; print('OK')"
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 6: Commit**

```bash
git add core_analysis/ui/main_window.py
git commit -m "feat: add grain analysis mode to MainWindow"
```

---

### Task 6: Final Integration Test

- [ ] **Step 1: Run full test suite**

```bash
python -m pytest tests/ -q
```
Expected: ~58 tests pass.

- [ ] **Step 2: Smoke test with synthetic data**

```bash
cd D:/vscode/VscodeProject/岩心分析教学系统 && python -c "
import numpy as np, cv2
from core_analysis.engine.grain_analyzer import GrainAnalyzer
from core_analysis.data.models import MaskRegion

# Create synthetic grain regions
mask = np.zeros((100, 100), dtype=np.uint8)
cv2.circle(mask, (30, 30), 15, 255, -1)
cv2.circle(mask, (70, 70), 20, 255, -1)
cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
regions = [MaskRegion(contour=c.squeeze(1).tolist(), area_px=cv2.contourArea(c),
                       centroid=(0,0), bbox=cv2.boundingRect(c)) for c in cnts]
results, summary = GrainAnalyzer.analyze(regions, 0.05, 10000)
print(f'Grains: {summary[\"total_count\"]}, Avg: {summary[\"avg_diameter_mm\"]}mm, Std: {summary[\"std_dev_mm\"]}mm')
print('Size dist:', summary['size_distribution'])
print('Smoke test passed!')
"
```
Expected: `Grains: 2, ... Smoke test passed!`

- [ ] **Step 3: Commit if needed**

```bash
git add -A && git commit -m "chore: final integration verification for grain analysis"
```

---

## Summary

| Task | Component | Files |
|---|---|---|
| 1 | Model + DB | `models.py`, `database.py` |
| 2 | AnalysisStore | `analysis_store.py` |
| 3 | GrainAnalyzer | `grain_analyzer.py`, `test_grain_analyzer.py` |
| 4 | Report | `report_generator.py`, `grain_report.html` |
| 5 | UI | `main_window.py`, `tool_panel.py` |
| 6 | Integration | smoke test |

Total: ~58 tests (52 existing + 5 new)