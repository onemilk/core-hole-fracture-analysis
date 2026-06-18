<template>
  <div class="home">
    <h1>岩心孔洞裂缝分析系统</h1>
    <p>企业级数字岩心分析平台 v1.0</p>
    <div class="modules">
      <div class="card" v-for="m in modules" :key="m.key">
        <h3>{{ m.name }}</h3>
        <p>{{ m.desc }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const modules = [
  { key: 'hole', name: '孔洞分析', desc: '自动检测岩心孔洞区域，计算等效直径、面孔率、充填特征' },
  { key: 'fracture', name: '裂缝分析', desc: '识别裂缝并计算长度、宽度、密度、有效性评价' },
  { key: 'grain', name: '粒度分析', desc: '颗粒Feret直径、圆度、Udden-Wentworth粒级分类' },
]
</script>

<style scoped>
.home { max-width: 1200px; margin: 0 auto; padding: 40px 20px; text-align: center; }
.modules { display: flex; gap: 20px; margin-top: 40px; justify-content: center; flex-wrap: wrap; }
.card { border: 1px solid #ddd; border-radius: 8px; padding: 24px; width: 280px; text-align: left; }
.card h3 { margin-top: 0; color: #2c3e50; }
</style>
