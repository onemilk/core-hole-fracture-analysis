# 企业平台 第四期：深度学习 U-Net 孔洞分割 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 训练轻量 U-Net 孔洞分割模型，集成到 engine-api，作为颜色分割的增强替代方案。

**Architecture:** PyTorch U-Net → 355对 MFAPNet 数据训练 → TorchScript 导出 → engine-api 加载推理 → `/engine/analyze` 加 `model` 参数选择 `classic` 或 `unet`。

**Tech Stack:** Python 3.10, PyTorch 2.x, torchvision, CUDA 13.1, RTX 5060 8GB

---

### Task 1: PyTorch Environment + GPU Verification

**Files:** None new. Verify existing GPU environment.

- [ ] **Step 1: Install PyTorch with CUDA**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

- [ ] **Step 2: Verify GPU and CUDA**

```bash
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
x = torch.randn(3, 512, 512).cuda()
print(f'Allocation test: OK')
"
```
Expected: `CUDA available: True`, `GPU: NVIDIA GeForce RTX 5060`, `Memory: ~8.0 GB`

- [ ] **Step 3: Commit env record**

```bash
git add platform/data/ -f .gitkeep 2>/dev/null
echo "torch==2.x" > platform/engine-api/requirements-ml.txt
git add platform/engine-api/requirements-ml.txt
git commit -m "chore: add ML requirements with PyTorch CUDA"
```

---

### Task 2: Data Preprocessing Pipeline

**Files:**
- Create: `platform/data/preprocess.py`
- Create: `platform/data/dataset.py`

- [ ] **Step 1: Write preprocessing script**

Create `platform/data/preprocess.py`:
```python
"""Preprocess MFAPNet dataset for U-Net training."""
import os
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

RAW_DIR = "raw/MFAPNet/CHA355"
PROCESSED_DIR = "processed"

class CoreHoleDataset(Dataset):
    def __init__(self, split='train', train_ratio=0.85):
        self.image_dir = os.path.join(RAW_DIR, "JPEGImages")
        self.mask_dir = os.path.join(RAW_DIR, "SegmentationClass")
        self.files = sorted([f.replace('.jpg', '') for f in os.listdir(self.image_dir)])
        split_idx = int(len(self.files) * train_ratio)
        if split == 'train':
            self.files = self.files[:split_idx]
        else:
            self.files = self.files[split_idx:]

        self.img_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])
        self.mask_transform = transforms.Compose([
            transforms.Resize((256, 256), interpolation=transforms.InterpolationMode.NEAREST),
            transforms.ToTensor()
        ])

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        name = self.files[idx]
        img = Image.open(os.path.join(self.image_dir, f"{name}.jpg")).convert('RGB')
        mask = Image.open(os.path.join(self.mask_dir, f"{name}.png"))
        mask = np.array(mask)
        mask = (mask > 0).astype(np.float32)  # binary: 0=bg, 1=pore
        mask = Image.fromarray((mask * 255).astype(np.uint8))

        return self.img_transform(img), self.mask_transform(mask)

def get_dataloaders(batch_size=8):
    train_ds = CoreHoleDataset(split='train')
    val_ds = CoreHoleDataset(split='val')
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2)
    return train_loader, val_loader

if __name__ == "__main__":
    train_loader, val_loader = get_dataloaders()
    imgs, masks = next(iter(train_loader))
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches: {len(val_loader)}")
    print(f"Image shape: {imgs.shape}, Mask shape: {masks.shape}")
    print("Preprocessing OK")
```

- [ ] **Step 2: Run preprocessing test**

```bash
cd platform/data && python preprocess.py
```
Expected: `Train batches: ~37`, `Val batches: ~7`, `Preprocessing OK`

---

### Task 3: U-Net Model + Training

**Files:**
- Create: `platform/data/train.py`
- Create: `platform/data/model.py`

- [ ] **Step 1: Write U-Net model**

Create `platform/data/model.py`:
```python
"""Lightweight U-Net for pore segmentation."""
import torch
import torch.nn as nn
import torch.nn.functional as F

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.conv(x)

class UNet(nn.Module):
    def __init__(self, in_ch=3, out_ch=1, features=[32, 64, 128, 256]):
        super().__init__()
        self.downs = nn.ModuleList()
        self.ups = nn.ModuleList()
        self.pool = nn.MaxPool2d(2)

        for f in features:
            self.downs.append(ConvBlock(in_ch, f))
            in_ch = f

        self.bottleneck = ConvBlock(features[-1], features[-1] * 2)

        for f in reversed(features):
            self.ups.append(nn.ConvTranspose2d(f * 2, f, kernel_size=2, stride=2))
            self.ups.append(ConvBlock(f * 2, f))

        self.out_conv = nn.Conv2d(features[0], out_ch, 1)

    def forward(self, x):
        skip_connections = []
        for down in self.downs:
            x = down(x)
            skip_connections.append(x)
            x = self.pool(x)

        x = self.bottleneck(x)

        for i in range(0, len(self.ups), 2):
            skip = skip_connections[-(i//2 + 1)]
            x = self.ups[i](x)
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:])
            x = torch.cat([x, skip], dim=1)
            x = self.ups[i+1](x)

        return torch.sigmoid(self.out_conv(x))
```

- [ ] **Step 2: Write training script**

Create `platform/data/train.py`:
```python
"""Train U-Net on MFAPNet dataset."""
import os
import torch
import torch.nn as nn
from tqdm import tqdm
from model import UNet
from preprocess import get_dataloaders

MODEL_DIR = "../models"
os.makedirs(MODEL_DIR, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

model = UNet(in_ch=3, out_ch=1).to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)

train_loader, val_loader = get_dataloaders(batch_size=8)
epochs = 100
best_loss = float("inf")

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for imgs, masks in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
        imgs, masks = imgs.to(device), masks.to(device)
        optimizer.zero_grad()
        outputs = model(imgs)
        loss = criterion(outputs, masks)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    train_loss /= len(train_loader)

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for imgs, masks in val_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            outputs = model(imgs)
            val_loss += criterion(outputs, masks).item()
    val_loss /= len(val_loader)

    scheduler.step(val_loss)
    print(f"Epoch {epoch+1}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

    if val_loss < best_loss:
        best_loss = val_loss
        torch.save(model.state_dict(), os.path.join(MODEL_DIR, "unet_best.pt"))
        print(f"  Saved best model (val_loss={val_loss:.4f})")

# Export to TorchScript for production inference
model.load_state_dict(torch.load(os.path.join(MODEL_DIR, "unet_best.pt")))
model.eval()
example = torch.randn(1, 3, 256, 256).to(device)
traced = torch.jit.trace(model, example)
traced.save(os.path.join(MODEL_DIR, "unet_traced.pt"))
print(f"Model exported to {MODEL_DIR}/unet_traced.pt")
```

- [ ] **Step 3: Run training**

```bash
cd platform/data && pip install tqdm && python train.py
```
Expected: Training progresses, model saved to `platform/data/models/unet_best.pt` and `unet_traced.pt`.

---

### Task 4: Engine API Integration

**Files:**
- Create: `platform/engine-api/unet_model.py`
- Modify: `platform/engine-api/main.py`

- [ ] **Step 1: Create U-Net inference wrapper**

Create `platform/engine-api/unet_model.py`:
```python
"""U-Net inference wrapper for engine integration."""
import os
import numpy as np
import cv2
import torch
from torchvision import transforms

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "models", "unet_traced.pt")
_model = None

def _get_model():
    global _model
    if _model is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = torch.jit.load(MODEL_PATH, map_location=device)
        _model.eval()
    return _model

def unet_segment_image(bgr_image: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Run U-Net inference on BGR image, returns binary mask (255=pore, 0=bg)."""
    h, w = bgr_image.shape[:2]
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    tensor = transform(rgb).unsqueeze(0)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = _get_model()
    with torch.no_grad():
        output = model(tensor.to(device)).cpu().squeeze().numpy()

    mask_resized = cv2.resize(output, (w, h), interpolation=cv2.INTER_LINEAR)
    binary_mask = (mask_resized > threshold).astype(np.uint8) * 255
    return binary_mask

def unet_extract_regions(bgr_image: np.ndarray) -> list:
    """Run U-Net and return MaskRegion list (same format as color segmentation)."""
    from engine.models import MaskRegion

    mask = unet_segment_image(bgr_image)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:
            continue
        M = cv2.moments(cnt)
        cx = M["m10"] / M["m00"] if M["m00"] != 0 else 0.0
        cy = M["m01"] / M["m00"] if M["m00"] != 0 else 0.0
        x, y, w, h = cv2.boundingRect(cnt)
        regions.append(MaskRegion(
            contour=cnt.squeeze(1).tolist() if len(cnt.shape) == 3 else [],
            area_px=area,
            centroid=(cx, cy),
            bbox=(x, y, w, h)
        ))
    return regions
```

- [ ] **Step 2: Update main.py to support model selection**

Read `platform/engine-api/main.py`. Add import:
```python
from unet_model import unet_extract_regions
```

Update `analyze` endpoint to accept optional `model` field in `AnalysisRequest`:
```python
class AnalysisRequest(BaseModel):
    image_base64: str
    analysis_type: str
    model: str = "classic"  # "classic" | "unet"
    scale_mm_per_px: float = 0.05
    match_tolerance: int = 30
    denoise_threshold: int = 10
    core_length_m: float = 1.0
```

Update the region extraction block in `analyze()`:
```python
        if req.model == "unet":
            regions = unet_extract_regions(bgr)
        else:
            preprocessed = ImageProcessor.auto_levels(bgr)
            center_color = preprocessed[h // 2, w // 2]
            regions = RegionExtractor.extract_by_color_sample(
                preprocessed, center_color, req.match_tolerance)
            regions = MorphologyEngine.denoise_by_area(regions, req.denoise_threshold)
```

- [ ] **Step 3: Commit**

```bash
git add platform/engine-api/unet_model.py platform/engine-api/main.py platform/data/train.py platform/data/model.py platform/data/preprocess.py
git commit -m "feat: add U-Net model, training pipeline, and engine integration"
```

---

### Task 5: Frontend — Model Selection Toggle

**Files:**
- Modify: `platform/frontend/src/views/Upload.vue`
- Modify: `platform/frontend/src/api/index.js`

- [ ] **Step 1: Add model param to API helper**

Edit `platform/frontend/src/api/index.js` — update submitAnalysis:
```javascript
  submitAnalysis: (data) => api.post('/analysis', data),
```
(already supports extra fields, just ensure `model` field is passed)

- [ ] **Step 2: Add model toggle to Upload.vue**

Edit `platform/frontend/src/views/Upload.vue` — add between Step 3's analysis type select and the submit button:
```html
      <div style="margin:8px 0">
        <label>分割模型：</label>
        <select v-model="modelType">
          <option value="classic">经典颜色分割</option>
          <option value="unet">U-Net 深度学习</option>
        </select>
      </div>
```

Add to script:
```javascript
const modelType = ref('classic');
```

Update startAnalysis to include model:
```javascript
  const res = await api.submitAnalysis({
    sample_id: sampleId.value,
    type: analysisType.value,
    model: modelType.value,
    image_path: null,
    params: {}
  });
```

- [ ] **Step 3: Build**

```bash
cd platform/frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add platform/frontend/
git commit -m "feat: add model selection toggle (classic/unet) to Upload page"
```

---

### Task 6: Training Execution + Verification

- [ ] **Step 1: Run training**

```bash
cd platform/data && python train.py
```

- [ ] **Step 2: Verify model inference**

```bash
cd platform/data && python -c "
from unet_model import unet_segment_image
import cv2, numpy as np
img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
mask = unet_segment_image(img)
print(f'Inference OK: mask shape={mask.shape}')
"
```
Expected: `Inference OK: mask shape=(256, 256)`

- [ ] **Step 3: Run desktop tests**

```bash
python -m pytest tests/ -q
```

- [ ] **Step 4: Commit model + verification**

```bash
git add platform/data/models/unet_traced.pt -f  # track the model
git add -A && git commit -m "chore: Phase 4 training complete + model verified" && git push origin v3.0-platform
```

---

## Summary

| Task | Component | Key Files |
|---|---|---|
| 1 | GPU Env | PyTorch CUDA verification |
| 2 | Data Pipeline | preprocess.py, dataset.py |
| 3 | U-Net + Training | model.py, train.py |
| 4 | Engine Integration | unet_model.py, main.py |
| 5 | Frontend Toggle | Upload.vue |
| 6 | Training + Verify | Model export + tests |
