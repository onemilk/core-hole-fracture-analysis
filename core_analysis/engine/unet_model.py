"""U-Net inference wrapper for engine integration."""
import os
import sys
import io
import numpy as np
import cv2
import torch
from torchvision import transforms

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "platform", "data", "models", "unet_best.pt")
_model = None

def _get_model():
    global _model
    if _model is None:
        device = torch.device("cpu")
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                buffer = io.BytesIO(f.read())
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "platform", "data"))
            from model import UNet
            _model = UNet(in_ch=3, out_ch=1)
            _model.load_state_dict(torch.load(buffer, map_location=device, weights_only=True))
            _model.to(device)
            _model.eval()
        else:
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train.py first.")
    return _model

def unet_segment_image(bgr_image: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Run U-Net inference, returns binary mask (255=pore, 0=bg)."""
    h, w = bgr_image.shape[:2]
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    tensor = transform(rgb).unsqueeze(0)

    model = _get_model()
    with torch.no_grad():
        output = model(tensor).squeeze().numpy()

    mask_resized = cv2.resize(output, (w, h), interpolation=cv2.INTER_LINEAR)
    binary_mask = (mask_resized > threshold).astype(np.uint8) * 255
    return binary_mask

def unet_extract_regions(bgr_image: np.ndarray) -> list:
    """Run U-Net and return MaskRegion list."""
    from core_analysis.data.models import MaskRegion

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
