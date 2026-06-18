<template>
  <div class="upload-page">
    <h2>岩心图像上传与分析</h2>
    <div class="step" v-if="!sampleId">
      <h3>1. 创建样本</h3>
      <form @submit.prevent="createSample">
        <input v-model="form.basin" placeholder="盆地（如塔里木盆地）" required />
        <input v-model="form.well_id" placeholder="井号（如J12-01）" required />
        <input v-model.number="form.top_depth" type="number" step="0.01" placeholder="起始深度(m)" required />
        <input v-model.number="form.bottom_depth" type="number" step="0.01" placeholder="结束深度(m)" required />
        <button type="submit">创建样本</button>
      </form>
    </div>
    <div class="step" v-if="sampleId">
      <h3>2. 上传图像</h3>
      <input type="file" @change="uploadImage" accept="image/*" />
      <p v-if="uploaded">✅ 上传成功 (样本ID: {{ sampleId }})</p>
    </div>
    <div class="step" v-if="uploaded">
      <h3>3. 开始分析</h3>
      <select v-model="analysisType">
        <option value="hole">孔洞分析</option>
        <option value="fracture">裂缝分析</option>
        <option value="grain">粒度分析</option>
      </select>
      <div style="margin:8px 0">
        <label>分割模型：</label>
        <select v-model="modelType">
          <option value="classic">经典颜色分割</option>
          <option value="unet">U-Net 深度学习</option>
        </select>
      </div>
      <button @click="startAnalysis" :disabled="analyzing">
        {{ analyzing ? '分析中...' : '开始分析' }}
      </button>
      <p v-if="analysisId">
        ✅ 任务已提交
        <router-link :to="'/result/' + analysisId">查看结果 →</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '../api/index.js';

const sampleId = ref(null);
const uploaded = ref(false);
const analyzing = ref(false);
const analysisType = ref('hole');
const modelType = ref('classic');
const analysisId = ref(null);
const form = ref({ basin: '', well_id: '', top_depth: null, bottom_depth: null });

async function createSample() {
  const sid = `${form.value.basin}-${form.value.well_id}-${Date.now()}`;
  const res = await api.createSample({ ...form.value, sample_id: sid });
  sampleId.value = res.data._id;
}

async function uploadImage(e) {
  const fd = new FormData();
  fd.append('image', e.target.files[0]);
  await api.uploadImage(sampleId.value, fd);
  uploaded.value = true;
}

async function startAnalysis() {
  analyzing.value = true;
  const res = await api.submitAnalysis({
    sample_id: sampleId.value,
    type: analysisType.value,
    model: modelType.value,
    image_path: null,
    params: {}
  });
  analysisId.value = res.data.task_id;
  analyzing.value = false;
}
</script>

<style scoped>
.upload-page { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
.step { margin: 24px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
input, select, button { display: block; width: 100%; margin: 8px 0; padding: 10px; font-size: 14px; box-sizing: border-box; }
button { background: #2c3e50; color: white; border: none; cursor: pointer; border-radius: 4px; }
button:disabled { background: #999; }
a { color: #2c3e50; }
</style>
