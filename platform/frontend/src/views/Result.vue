<template>
  <div class="result-page">
    <h2>分析结果</h2>
    <div v-if="loading">⏳ 加载中...</div>
    <div v-else-if="error" class="error">❌ {{ error }}</div>
    <div v-else-if="analysis">
      <p>状态: <b>{{ statusText }}</b></p>
      <div v-if="analysis.status === 'pending'">
        <p>分析正在后台处理中...</p>
        <button @click="refresh">🔄 刷新状态</button>
      </div>
      <div v-if="analysis.status === 'failed'">
        <p>分析失败: {{ analysis.results?.error }}</p>
      </div>
      <div v-if="analysis.status === 'done' && results">
        <h3>统计摘要</h3>
        <table>
          <tr v-for="(val, key) in results.summary" :key="key">
            <td><b>{{ key }}</b></td>
            <td>{{ typeof val === 'object' ? JSON.stringify(val) : val }}</td>
          </tr>
        </table>
        <h3>检测区域</h3>
        <p>共检测到 {{ results.regions?.length || 0 }} 个区域</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/index.js';

const route = useRoute();
const loading = ref(true);
const error = ref(null);
const analysis = ref(null);
const results = ref(null);

const statusText = computed(() => {
  const map = { pending: '处理中', processing: '计算中', done: '已完成', failed: '失败' };
  return map[analysis.value?.status] || analysis.value?.status;
});

async function load() {
  try {
    const res = await api.getAnalysis(route.params.id);
    analysis.value = res.data;
    if (res.data.results) results.value = res.data.results;
  } catch (e) {
    error.value = e.response?.data?.error || e.message;
  } finally {
    loading.value = false;
  }
}

function refresh() { loading.value = true; load(); }

onMounted(load);
</script>

<style scoped>
.result-page { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; }
td, th { border: 1px solid #ddd; padding: 8px; font-size: 13px; }
.error { color: #c0392b; }
button { padding: 10px 20px; background: #2c3e50; color: white; border: none; border-radius: 4px; cursor: pointer; margin: 8px 0; }
</style>
