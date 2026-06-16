# v2 第一期：自动/手动旋转 + 沉积知识库 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为岩心孔洞裂缝分析教学系统添加图像旋转工具（自动+手动）和内置沉积学知识库。

**Architecture:** 旋转功能扩展 ImageProcessor/MorphologyEngine 引擎层 + MainWindow/ImageCanvas UI 层。知识库为独立模块：JSON 数据文件 + KnowledgeDialog UI，通过菜单入口挂载。

**Tech Stack:** Python 3.10+, OpenCV, PySide6

---

## 文件变更结构

```
core_analysis/
├── engine/
│   ├── image_processor.py   [修改] +5 静态方法
│   └── morphology_engine.py [修改] +1 静态方法
├── ui/
│   ├── main_window.py       [修改] 工具栏按钮 + 菜单
│   ├── image_canvas.py      [修改] +2 方法
│   └── knowledge_dialog.py  [新建]
└── data/
    └── sedimentary_knowledge.json [新建]

tests/
├── test_rotation.py   [新建]
└── test_knowledge.py  [新建]
```

---

### Task 1: Rotation Engine — ImageProcessor Methods

**Files:**
- Modify: `core_analysis/engine/image_processor.py`
- Create: `tests/test_rotation.py`

- [ ] **Step 1: Write failing rotation tests**

Write `tests/test_rotation.py`:
```python
"""Tests for image rotation and flip operations."""
import numpy as np
import cv2
from core_analysis.engine.image_processor import ImageProcessor


def _make_test_image(w=120, h=80):
    img = np.ones((h, w, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (40, 30), (80, 50), (50, 50, 50), -1)
    return img


class TestRotation:
    def test_rotate_90(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 90)
        assert result.shape[0] == img.shape[1]
        assert result.shape[1] == img.shape[0]

    def test_rotate_180_shape_unchanged(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 180)
        assert result.shape == img.shape

    def test_rotate_45(self):
        img = _make_test_image()
        result = ImageProcessor.rotate(img, 45)
        assert result.shape[0] >= img.shape[0]

    def test_flip_horizontal(self):
        img = _make_test_image()
        result = ImageProcessor.flip_horizontal(img)
        assert result.shape == img.shape
        # Pixel at top-left should now equal original top-right pixel
        assert result[0, 0, 0] == img[0, -1, 0]

    def test_flip_vertical(self):
        img = _make_test_image()
        result = ImageProcessor.flip_vertical(img)
        assert result.shape == img.shape
        assert result[-1, 0, 0] == img[0, 0, 0]

    def test_detect_orientation_returns_angle(self):
        # Create an image with a dominant horizontal line
        img = np.ones((100, 200, 3), dtype=np.uint8) * 200
        cv2.line(img, (40, 50), (160, 50), (30, 30, 30), 3)
        angle = ImageProcessor.detect_orientation(img)
        # Should be near 0° or 180° (horizontal)
        assert abs(abs(angle) - 0) < 10 or abs(abs(angle) - 180) < 10

    def test_auto_rotate(self):
        # Create image with a line at 45°
        img = np.ones((200, 200, 3), dtype=np.uint8) * 200
        cv2.line(img, (50, 50), (150, 150), (30, 30, 30), 3)
        result = ImageProcessor.auto_rotate(img)
        assert result.shape == img.shape  # Should still be valid
        assert result.dtype == np.uint8
```

Run: `python -m pytest tests/test_rotation.py -v`
Expected: FAIL — `AttributeError: type object 'ImageProcessor' has no attribute 'rotate'`

- [ ] **Step 2: Implement rotation methods in ImageProcessor**

Read the current `core_analysis/engine/image_processor.py`, then append these 4 new static methods at the end of the class (before the end of the class definition):

```python
    @staticmethod
    def rotate(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by angle (degrees). Positive = counter-clockwise."""
        h, w = image.shape[:2]
        center = (w / 2, h / 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        matrix[0, 2] += new_w / 2 - center[0]
        matrix[1, 2] += new_h / 2 - center[1]
        return cv2.warpAffine(image, matrix, (new_w, new_h),
                              borderMode=cv2.BORDER_CONSTANT,
                              borderValue=(200, 200, 200))

    @staticmethod
    def flip_horizontal(image: np.ndarray) -> np.ndarray:
        return cv2.flip(image, 1)

    @staticmethod
    def flip_vertical(image: np.ndarray) -> np.ndarray:
        return cv2.flip(image, 0)

    @staticmethod
    def detect_orientation(image: np.ndarray) -> float:
        """Detect dominant line orientation in degrees. Returns angle (0-180)."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50,
                                minLineLength=30, maxLineGap=10)
        if lines is None or len(lines) == 0:
            return 0.0
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            angles.append(angle % 180)
        if not angles:
            return 0.0
        return float(np.median(angles))

    @staticmethod
    def auto_rotate(image: np.ndarray) -> np.ndarray:
        """Auto-detect orientation and rotate to horizontal."""
        angle = ImageProcessor.detect_orientation(image)
        correction = angle if angle <= 90 else angle - 180
        if abs(correction) < 2:
            return image
        return ImageProcessor.rotate(image, correction)
```

Run: `python -m pytest tests/test_rotation.py -v`
Expected: 7 passed

- [ ] **Step 3: Commit**

```bash
git add core_analysis/engine/image_processor.py tests/test_rotation.py
git commit -m "feat: add rotation and flip methods to ImageProcessor"
```

---

### Task 2: Region Rotation — MorphologyEngine

**Files:**
- Modify: `core_analysis/engine/morphology_engine.py`
- Modify: `tests/test_rotation.py` (add region rotation test)

- [ ] **Step 1: Add failing test for region rotation**

Append to `tests/test_rotation.py`:
```python
class TestRegionRotation:
    def test_rotate_region_stays_valid(self):
        """Region rotated 90° should still produce a valid MaskRegion."""
        import cv2
        from core_analysis.data.models import MaskRegion
        from core_analysis.engine.morphology_engine import MorphologyEngine

        # Create a line-shaped region
        mask = np.zeros((100, 100), dtype=np.uint8)
        cv2.rectangle(mask, (20, 45), (80, 55), 255, -1)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        region = MaskRegion(
            contour=cnts[0].squeeze(1).tolist(),
            area_px=cv2.contourArea(cnts[0]),
            centroid=(50, 50),
            bbox=(20, 45, 60, 10)
        )
        result = MorphologyEngine.rotate_region(region, 90, (100, 100))
        assert result is not None
        assert result.area_px > 0
```

Run: `python -m pytest tests/test_rotation.py::TestRegionRotation -v`
Expected: FAIL — `AttributeError: type object 'MorphologyEngine' has no attribute 'rotate_region'`

- [ ] **Step 2: Implement rotate_region**

Append to `core_analysis/engine/morphology_engine.py`:
```python
    @staticmethod
    def rotate_region(region: MaskRegion, angle: float,
                      image_shape: tuple) -> Optional[MaskRegion]:
        """Rotate a MaskRegion by angle. Returns new MaskRegion or None."""
        h, w = image_shape
        center = (w / 2, h / 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)
        matrix[0, 2] += new_w / 2 - center[0]
        matrix[1, 2] += new_h / 2 - center[1]

        mask = np.zeros(image_shape, dtype=np.uint8)
        pts = np.array(region.contour, dtype=np.int32)
        if pts.ndim == 2 and pts.shape[0] >= 3:
            cv2.drawContours(mask, [pts], -1, 255, -1)
        rotated_mask = cv2.warpAffine(mask, matrix, (new_w, new_h),
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=0)

        return MorphologyEngine._mask_to_region(rotated_mask, 0, 0)
```

Note: need to add `from core_analysis.data.models import MaskRegion` at top of morphology_engine.py, and verify `Optional` is imported.

Run: `python -m pytest tests/test_rotation.py::TestRegionRotation -v`
Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add core_analysis/engine/morphology_engine.py tests/test_rotation.py
git commit -m "feat: add rotate_region to MorphologyEngine"
```

---

### Task 3: ImageCanvas — Region Rotation Support

**Files:**
- Modify: `core_analysis/ui/image_canvas.py`

- [ ] **Step 1: Add rotate_regions method to ImageCanvas**

Read `core_analysis/ui/image_canvas.py`. Add this method to the class:

```python
    def rotate_regions(self, angle: float):
        """Rotate all overlay regions by given angle (degrees)."""
        if not self._regions or self._image_bgr is None:
            return
        h, w = self._image_bgr.shape[:2]
        updated = []
        for r in self._regions:
            result = MorphologyEngine.rotate_region(r, angle, (h, w))
            if result is not None:
                updated.append(result)
        self._regions = updated
        self._refresh_overlay()
```

Note: add import at top: `from core_analysis.engine.morphology_engine import MorphologyEngine`

- [ ] **Step 2: Verify import works**

```bash
python -c "from core_analysis.ui.image_canvas import ImageCanvas; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/image_canvas.py
git commit -m "feat: add rotate_regions method to ImageCanvas"
```

---

### Task 4: MainWindow — Rotation UI

**Files:**
- Modify: `core_analysis/ui/main_window.py`

- [ ] **Step 1: Add rotation menu and toolbar buttons**

Read `core_analysis/ui/main_window.py`. 

In `_setup_ui()`, after the line `process_menu.addAction("自动色阶", self._auto_levels)`, add rotation submenu:

```python
        rotate_menu = process_menu.addMenu("旋转")
        rotate_menu.addAction("↺ 90°左转", lambda: self._rotate_image(90))
        rotate_menu.addAction("↻ 90°右转", lambda: self._rotate_image(-90))
        rotate_menu.addAction("180°旋转", lambda: self._rotate_image(180))
        rotate_menu.addAction("↔ 水平翻转", self._flip_horizontal)
        rotate_menu.addAction("↕ 竖直翻转", self._flip_vertical)
        rotate_menu.addSeparator()
        rotate_menu.addAction("自动旋转校正", self._auto_rotate_image)
        rotate_menu.addAction("自定义角度...", self._rotate_custom)
```

In the toolbar setup section, after `toolbar.addAction("👁️ 图层", self._toggle_overlay)`, add:

```python
        toolbar.addSeparator()
        toolbar.addAction("↺ 左转", lambda: self._rotate_image(90))
        toolbar.addAction("↻ 右转", lambda: self._rotate_image(-90))
        toolbar.addAction("↔ 翻转", self._flip_horizontal)
```

- [ ] **Step 2: Add rotation slot methods to MainWindow**

Append to the class (before `_toggle_overlay`):

```python
    def _rotate_image(self, angle: float):
        if self._canvas.image_bgr is None: return
        rotated = ImageProcessor.rotate(self._canvas.image_bgr, angle)
        self._canvas.load_image_from_array(rotated)
        self._canvas.rotate_regions(angle)

    def _flip_horizontal(self):
        if self._canvas.image_bgr is None: return
        flipped = ImageProcessor.flip_horizontal(self._canvas.image_bgr)
        self._canvas.load_image_from_array(flipped)

    def _flip_vertical(self):
        if self._canvas.image_bgr is None: return
        flipped = ImageProcessor.flip_vertical(self._canvas.image_bgr)
        self._canvas.load_image_from_array(flipped)

    def _auto_rotate_image(self):
        if self._canvas.image_bgr is None: return
        angle = ImageProcessor.detect_orientation(self._canvas.image_bgr)
        correction = angle if angle <= 90 else angle - 180
        if abs(correction) < 2:
            QMessageBox.information(self, "自动旋转", f"图像方向已接近水平 (偏差{correction:.1f}°)")
            return
        self._rotate_image(correction)

    def _rotate_custom(self):
        if self._canvas.image_bgr is None: return
        from PySide6.QtWidgets import QInputDialog
        angle, ok = QInputDialog.getDouble(self, "自定义旋转", "角度 (正值=逆时针):",
                                           0, -180, 180, 1)
        if ok:
            self._rotate_image(angle)
```

- [ ] **Step 3: Verify import**

```bash
python -c "from core_analysis.ui.main_window import MainWindow; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add core_analysis/ui/main_window.py
git commit -m "feat: add rotation buttons and menu to MainWindow"
```

---

### Task 5: Sedimentary Knowledge JSON

**Files:**
- Create: `core_analysis/data/sedimentary_knowledge.json`

- [ ] **Step 1: Write knowledge base data**

Write `core_analysis/data/sedimentary_knowledge.json`:
```json
{
  "categories": {
    "沉积岩分类": {
      "碳酸盐岩": {
        "definition": "主要由碳酸盐矿物（方解石、白云石）组成的沉积岩。常见类型包括灰岩、白云岩、礁灰岩等。是石油天然气的重要储集岩类。碳酸盐岩中的孔、洞、缝构成油气渗滤运移的通道和储集空间。",
        "related": ["灰岩", "白云岩", "礁灰岩", "碎屑岩"]
      },
      "碎屑岩": {
        "definition": "由母岩机械破碎产物（碎屑）经搬运、沉积、压实和胶结而形成的岩石。包括砾岩、砂岩、粉砂岩、泥岩等。碎屑岩的孔隙以原生粒间孔为主。",
        "related": ["砂岩", "砾岩", "泥岩", "碳酸盐岩"]
      },
      "蒸发岩": {
        "definition": "在封闭或半封闭环境中由于蒸发作用使水中的盐类矿物沉淀而形成的沉积岩。常见类型有石膏岩、盐岩、钾盐岩等。",
        "related": ["石膏", "化学沉积"]
      },
      "灰岩": {
        "definition": "以方解石（CaCO₃）为主要成分的碳酸盐岩。常含生物碎屑，是石油天然气的重要储层岩石。孔隙类型以次生溶蚀孔洞为主。",
        "related": ["碳酸盐岩", "白云岩", "方解石"]
      },
      "白云岩": {
        "definition": "以白云石（CaMg(CO₃)₂）为主要成分的碳酸盐岩。多由灰岩经白云石化作用形成，孔隙度通常高于灰岩。",
        "related": ["碳酸盐岩", "灰岩", "白云石"]
      }
    },
    "沉积构造": {
      "层理": {
        "definition": "沉积岩中最常见的构造特征，由沉积物成分、结构、颜色等在垂向上的变化形成。分为水平层理、交错层理、递变层理等。",
        "related": ["交错层理", "递变层理", "波痕"]
      },
      "交错层理": {
        "definition": "沉积层与主层面相交形成的层理，常见于水流或风成沉积环境中。可作为判断古水流方向的标志。",
        "related": ["层理", "古水流", "波痕"]
      },
      "波痕": {
        "definition": "沉积物表面因水流或波浪作用形成的波状起伏构造。对称波痕指示双向水流，不对称波痕指示单向水流。",
        "related": ["层理", "交错层理"]
      },
      "缝合线": {
        "definition": "碳酸盐岩中常见的锯齿状压溶构造，通常被泥质或不溶残余物充填。可作为岩层变形的指示标志。沿缝合线可发生后期溶蚀形成缝中缝。",
        "related": ["压溶作用", "缝中缝", "碳酸盐岩"]
      },
      "泥裂": {
        "definition": "泥质沉积物脱水收缩形成的多边形裂缝，常见于干旱或间歇性暴露环境。",
        "related": ["沉积环境"]
      }
    },
    "成岩作用": {
      "压实作用": {
        "definition": "沉积物在上覆压力和构造应力作用下体积缩小、孔隙度降低的过程。是碎屑岩孔隙度降低的主要成岩作用之一。",
        "related": ["胶结作用", "成岩作用", "孔隙度"]
      },
      "胶结作用": {
        "definition": "孔隙水中溶解的矿物质在颗粒间沉淀，将松散沉积物固结成岩的过程。常见胶结物有硅质、钙质（方解石）、铁质等。",
        "related": ["压实作用", "方解石", "石英"]
      },
      "溶解作用": {
        "definition": "地下水或酸性流体溶解岩石中的可溶性矿物（主要是碳酸盐矿物），形成次生孔隙和溶洞的过程。是碳酸盐岩储层孔隙形成的关键机制。",
        "related": ["次生孔隙", "溶洞", "碳酸盐岩", "交代作用"]
      },
      "交代作用": {
        "definition": "一种矿物被另一种矿物逐步替换的过程，保持原有结构形态。白云石化（方解石→白云石）是最常见的交代作用之一。",
        "related": ["溶解作用", "白云岩", "白云石"]
      },
      "压溶作用": {
        "definition": "在应力作用下矿物颗粒接触点发生选择性溶解，形成缝合线等构造。被溶解的物质可在附近重新沉淀。",
        "related": ["缝合线", "溶解作用"]
      }
    },
    "孔隙类型": {
      "原生孔隙": {
        "definition": "沉积物沉积时即存在的孔隙，如粒间孔、粒内孔、生物体腔孔等。在碎屑岩中以原生粒间孔为主。",
        "related": ["次生孔隙", "粒间孔", "面孔率"]
      },
      "次生孔隙": {
        "definition": "沉积物固结成岩后经溶解、破裂、白云石化等作用形成的孔隙。碳酸盐岩储层以次生孔隙为主，包括溶蚀孔、晶间孔、裂缝等。",
        "related": ["原生孔隙", "溶解作用", "溶洞", "裂缝"]
      },
      "粒间孔": {
        "definition": "碎屑颗粒之间的孔隙。是砂岩储层最主要的储集空间类型。孔隙度受分选、磨圆、压实和胶结程度控制。",
        "related": ["原生孔隙", "砂岩", "面孔率"]
      },
      "晶间孔": {
        "definition": "矿物晶体之间的微小孔隙。常见于白云岩中，白云石化过程中因摩尔体积减小而形成的晶间孔隙。",
        "related": ["次生孔隙", "白云岩", "白云石化"]
      },
      "溶洞": {
        "definition": "因溶解作用形成的大于1mm的空洞。洞壁不规则，常有粘土附着。溶洞的发育受岩性、构造和流体条件控制。",
        "related": ["次生孔隙", "溶解作用", "晶洞", "孔洞分析"]
      },
      "晶洞": {
        "definition": "被方解石、白云石、石英等矿物的晶簇所充填或半充填的孔洞。晶洞内壁常可见完好的晶体形态。",
        "related": ["溶洞", "次生孔隙", "方解石"]
      }
    },
    "常见矿物": {
      "方解石": {
        "definition": "化学成分为碳酸钙（CaCO₃），是碳酸盐岩的主要组成矿物。遇稀盐酸强烈起泡。是储层中最常见的胶结物和充填物之一。",
        "related": ["碳酸盐岩", "灰岩", "白云石", "胶结作用"]
      },
      "白云石": {
        "definition": "化学成分为 CaMg(CO₃)₂，是白云岩的主要组成矿物。遇稀盐酸起泡微弱，需加热或研成粉末后才明显起泡。",
        "related": ["白云岩", "方解石", "交代作用"]
      },
      "石英": {
        "definition": "化学成分为 SiO₂，是砂岩的主要碎屑成分，也是常见的胶结物。硬度7，化学性质稳定，抗风化能力强。",
        "related": ["砂岩", "碎屑岩", "胶结作用"]
      },
      "长石": {
        "definition": "架状硅酸盐矿物，是砂岩中仅次于石英的碎屑组分。常见有钾长石和斜长石。易风化为粘土矿物。",
        "related": ["砂岩", "粘土矿物", "碎屑岩"]
      },
      "石膏": {
        "definition": "化学成分为 CaSO₄·2H₂O，是蒸发岩的主要组成矿物。可作为裂缝或孔洞的充填物出现。",
        "related": ["蒸发岩", "充填物", "硬石膏"]
      },
      "黄铁矿": {
        "definition": "化学成分为 FeS₂，呈金黄色，常以立方体晶形或莓状集合体产出。在沉积岩中常见，可指示还原环境。",
        "related": ["充填物", "成岩作用"]
      },
      "高岭石": {
        "definition": "粘土矿物之一，化学成分为 Al₄Si₄O₁₀(OH)₈。常由长石风化形成，可作为裂缝或孔隙的充填物。",
        "related": ["粘土矿物", "长石", "充填物"]
      }
    },
    "常用术语": {
      "面孔率": {
        "definition": "岩石截面（图像）上可见孔隙（洞）面积占岩石总面积的百分比。计算公式：面孔率 = Σ孔洞面积 / 图像总面积 × 100%。是评价储层质量的重要参数。",
        "related": ["孔隙度", "孔洞分析", "等效直径"]
      },
      "等效直径": {
        "definition": "将不规则孔洞等效为等面积圆的直径。计算公式：Dr = 2√(A/π)。用于标准化描述孔洞大小。",
        "related": ["面孔率", "孔洞分析"]
      },
      "裂缝密度": {
        "definition": "面密度 = 裂缝累计长度(m) / 岩石面积(m²)；线密度 = 裂缝条数 / 岩心长度(m)。反映裂缝发育程度。",
        "related": ["裂缝分析", "面孔隙度"]
      },
      "连续区域": {
        "definition": "图像分割中的概念。勾选"连续区域"时，分割只在当前选取点周围满足匹配条件的像素中进行，而非全图扫描。用于精细提取单个目标区域。",
        "related": ["区域分割", "颜色匹配度"]
      },
      "颜色匹配度": {
        "definition": "区域分割参数，控制与采样颜色的匹配容差。数值越小，提取的颜色范围越窄，与选定颜色越接近；数值越大，匹配范围越宽。",
        "related": ["区域分割", "连续区域"]
      },
      "地层": {
        "definition": "具有一定层位和形成时代的一层或一组岩层。包含盆地→坳陷→组→层的分级体系。",
        "related": ["沉积岩分类", "层理"]
      }
    }
  }
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python -c "import json; data=json.load(open('core_analysis/data/sedimentary_knowledge.json','r',encoding='utf-8')); cats=list(data['categories'].keys()); entries=sum(len(v) for v in data['categories'].values()); print(f'{len(cats)} categories, {entries} entries, JSON valid')"
```

Expected: `6 categories, 30 entries, JSON valid`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/data/sedimentary_knowledge.json
git commit -m "feat: add sedimentary knowledge base JSON — 6 categories, 30 entries"
```

---

### Task 6: Knowledge Dialog UI

**Files:**
- Create: `core_analysis/ui/knowledge_dialog.py`

- [ ] **Step 1: Write KnowledgeDialog**

Write `core_analysis/ui/knowledge_dialog.py`:
```python
"""KnowledgeDialog — searchable sedimentary knowledge base browser."""

import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QTextBrowser, QSplitter,
    QLabel
)
from PySide6.QtCore import Qt


class KnowledgeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("沉积知识库")
        self.resize(800, 500)
        self._data = {}
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索知识库...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        # Splitter: left tree + right detail
        splitter = QSplitter(Qt.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self._tree)

        self._detail = QTextBrowser()
        self._detail.setOpenExternalLinks(False)
        self._detail.anchorClicked.connect(self._on_link_clicked)
        splitter.addWidget(self._detail)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self._populate_tree()

    def _populate_tree(self, filter_text: str = ""):
        self._tree.clear()
        categories = self._data.get("categories", {})
        for cat_name, entries in categories.items():
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setData(0, Qt.UserRole, ("category", cat_name))
            for entry_name, entry_data in entries.items():
                match_in_name = filter_text.lower() in entry_name.lower() if filter_text else True
                match_in_def = filter_text.lower() in entry_data.get("definition", "").lower() if filter_text else True
                if not filter_text or match_in_name or match_in_def:
                    item = QTreeWidgetItem([entry_name])
                    item.setData(0, Qt.UserRole, ("entry", cat_name, entry_name))
                    cat_item.addChild(item)
            if cat_item.childCount() > 0 or not filter_text:
                self._tree.addTopLevelItem(cat_item)
        self._tree.expandAll()

    def _on_item_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data is None: return
        if data[0] == "entry":
            self._show_entry(data[1], data[2])

    def _show_entry(self, category: str, entry_name: str):
        entries = self._data.get("categories", {}).get(category, {})
        entry = entries.get(entry_name, {})
        definition = entry.get("definition", "")
        related = entry.get("related", [])

        html = f"<h3>{entry_name}</h3><p style='line-height:1.8;'>{definition}</p>"
        if related:
            html += "<hr><b>相关条目:</b><ul>"
            for r in related:
                html += f'<li><a href="#{r}">{r}</a></li>'
            html += "</ul>"
        self._detail.setHtml(html)

    def _on_link_clicked(self, url):
        target = url.toString().lstrip("#")
        self._search.setText("")
        self._populate_tree()
        # Find and expand the target entry
        for i in range(self._tree.topLevelItemCount()):
            cat_item = self._tree.topLevelItem(i)
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                data = child.data(0, Qt.UserRole)
                if data and data[0] == "entry" and data[2] == target:
                    cat_item.setExpanded(True)
                    self._tree.setCurrentItem(child)
                    self._show_entry(data[1], data[2])
                    return

    def _on_search(self, text: str):
        self._populate_tree(text)
        self._tree.expandAll()
```

- [ ] **Step 2: Verify import**

```bash
python -c "from core_analysis.ui.knowledge_dialog import KnowledgeDialog; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/knowledge_dialog.py
git commit -m "feat: add KnowledgeDialog with searchable category tree"
```

---

### Task 7: MainWindow — Knowledge Base Menu Entry

**Files:**
- Modify: `core_analysis/ui/main_window.py`

- [ ] **Step 1: Add Help menu with Knowledge Base**

Read `core_analysis/ui/main_window.py`.

In `_setup_ui()`, at the end of the menu setup (after `analysis_menu`), add:

```python
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("沉积知识库", self._open_knowledge)
```

At top of file, verify/add import:
```python
from core_analysis.ui.knowledge_dialog import KnowledgeDialog
```

In the class, add the slot method (append near the end of the class):

```python
    def _open_knowledge(self):
        dialog = KnowledgeDialog(self)
        dialog.exec()
```

- [ ] **Step 2: Verify**

```bash
python -c "from core_analysis.ui.main_window import MainWindow; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add core_analysis/ui/main_window.py
git commit -m "feat: add Help menu with Knowledge Base entry"
```

---

### Task 8: Final Tests & Integration Verification

**Files:**
- Create: `tests/test_knowledge.py`
- Modify: `tests/test_rotation.py` (already created)

- [ ] **Step 1: Write knowledge base tests**

Write `tests/test_knowledge.py`:
```python
"""Tests for sedimentary knowledge base."""
import json
import os


class TestKnowledgeBase:
    def test_json_loads_correctly(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "categories" in data
        cats = data["categories"]
        assert len(cats) == 6
        total = sum(len(entries) for entries in cats.values())
        assert total >= 30

    def test_all_entries_have_definition(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for cat_name, entries in data["categories"].items():
            for entry_name, entry_data in entries.items():
                assert "definition" in entry_data, f"Missing definition in {cat_name}/{entry_name}"
                assert isinstance(entry_data["definition"], str)
                assert len(entry_data["definition"]) > 20

    def test_required_categories_exist(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        required = ["沉积岩分类", "沉积构造", "成岩作用", "孔隙类型", "常见矿物", "常用术语"]
        for cat in required:
            assert cat in data["categories"], f"Missing category: {cat}"
```

- [ ] **Step 2: Run all tests**

```bash
cd D:/vscode/VscodeProject/pj01 && python -m pytest tests/ -v
```

Expected: All tests pass (~48 test cases)

- [ ] **Step 3: Commit**

```bash
git add tests/test_knowledge.py
git commit -m "test: add knowledge base structure validation tests"
```

---

### Task 9: Smoke Test — Full Rotation + Knowledge Pipeline

- [ ] **Step 1: Run full rotation pipeline test without Qt**

```bash
cd D:/vscode/VscodeProject/pj01 && python -c "
import cv2, numpy as np
from core_analysis.engine.image_processor import ImageProcessor
from core_analysis.data import models
from core_analysis.engine import morphology_engine as me

# Create test image
img = np.ones((100, 200, 3), dtype=np.uint8) * 200
cv2.line(img, (30, 50), (170, 50), (30,30,30), 3)

# Test rotation chain
angle = ImageProcessor.detect_orientation(img)
print(f'Detected angle: {angle:.1f} deg')
rotated = ImageProcessor.rotate(img, 90)
print(f'Rotated shape: {rotated.shape}')
flipped = ImageProcessor.flip_horizontal(img)
print(f'Flipped shape: {flipped.shape}')

# Test JSON knowledge base
import json, os
json_path = os.path.join('core_analysis', 'data', 'sedimentary_knowledge.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
entries = sum(len(v) for v in data['categories'].values())
print(f'Knowledge entries: {entries}')
print('All checks passed!')
"
```

Expected: `All checks passed!` with reasonable angle and shape values.

- [ ] **Step 2: Full test suite**

```bash
python -m pytest tests/ -q
```

---

## Summary

| Task | Component | Files |
|---|---|---|
| 1 | Rotation Engine | `engine/image_processor.py` + `tests/test_rotation.py` |
| 2 | Region Rotation | `engine/morphology_engine.py` + test |
| 3 | Canvas Rotation | `ui/image_canvas.py` |
| 4 | Rotation UI | `ui/main_window.py` |
| 5 | Knowledge JSON | `data/sedimentary_knowledge.json` |
| 6 | Knowledge Dialog | `ui/knowledge_dialog.py` |
| 7 | Knowledge Menu | `ui/main_window.py` |
| 8 | Final Tests | `tests/test_knowledge.py` |
| 9 | Smoke Test | manual verification |
