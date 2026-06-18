"""FastAPI analysis engine — wraps engine modules."""

import os
import sys
import base64
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

app = FastAPI(title="Core Analysis Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class AnalysisRequest(BaseModel):
    image_base64: str
    analysis_type: str  # "hole" | "fracture" | "grain"
    scale_mm_per_px: float = 0.05
    match_tolerance: int = 30
    denoise_threshold: int = 10
    core_length_m: float = 1.0


@app.get("/engine/health")
def health():
    return {"status": "ok", "engine": "v1.0"}


@app.post("/engine/analyze")
def analyze(req: AnalysisRequest):
    """Run analysis on base64-encoded image."""
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

        return {"regions": regions_json, "summary": summary, "status": "done"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
