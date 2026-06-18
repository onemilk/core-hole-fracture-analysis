import axios from 'axios';
import fs from 'fs';

const ENGINE_URL = process.env.ENGINE_URL || 'http://localhost:5001';

export async function runAnalysis(imagePath, analysisType, params = {}) {
  const imageBuffer = fs.readFileSync(imagePath);
  const imageBase64 = imageBuffer.toString('base64');

  const response = await axios.post(`${ENGINE_URL}/engine/analyze`, {
    image_base64: imageBase64,
    analysis_type: analysisType,
    scale_mm_per_px: params.scale || 0.05,
    match_tolerance: params.tolerance || 30,
    denoise_threshold: params.denoise || 10,
    core_length_m: params.coreLength || 1.0
  }, { timeout: 120000 });

  return response.data;
}
