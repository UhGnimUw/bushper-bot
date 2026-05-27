<template>
  <div class="monitor-view">
    <div class="container">
      <div class="card">
        <h2>24小时统计概览</h2>
        <div class="stats-grid">
          <div class="stat"><div class="stat-label">总请求数</div><div class="stat-value">{{ stats.total_requests || 0 }}</div></div>
          <div class="stat"><div class="stat-label">平均响应时间</div><div class="stat-value">{{ stats.avg_response_time ? stats.avg_response_time.toFixed(2) + 'ms' : '-' }}</div></div>
          <div class="stat"><div class="stat-label">最大响应时间</div><div class="stat-value">{{ stats.max_response_time ? stats.max_response_time.toFixed(2) + 'ms' : '-' }}</div></div>
          <div class="stat"><div class="stat-label">平均CPU</div><div class="stat-value">{{ stats.avg_cpu ? stats.avg_cpu.toFixed(1) + '%' : '-' }}</div></div>
        </div>
      </div>
      <div class="card">
        <h2>最近请求记录</h2>
        <table>
          <thead><tr><th>时间</th><th>响应时间(ms)</th><th>请求数</th></tr></thead>
          <tbody>
            <tr v-for="m in metrics" :key="m.id">
              <td>{{ new Date(m.timestamp).toLocaleString() }}</td>
              <td>{{ m.response_time_ms ? m.response_time_ms.toFixed(2) : '-' }}</td>
              <td>{{ m.request_count || 0 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { monitorAPI } from '@/api/agent.js'
const stats = ref({}), metrics = ref([])
const loadStats = async () => { try { const res = await monitorAPI.stats(); if (res.data.ok) stats.value = res.data.summary } catch (e) { console.error(e) } }
const loadRecent = async () => { try { const res = await monitorAPI.recent(); if (res.data.ok) metrics.value = res.data.metrics } catch (e) { console.error(e) } }
onMounted(() => { loadStats(); loadRecent(); setInterval(() => { loadStats(); loadRecent(); }, 30000) })
</script>

<style scoped>
.monitor-view { flex: 1; overflow: hidden; }
.container { flex: 1; padding: 20px; overflow-y: auto; }
.card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
.card h2 { font-size: 16px; color: #1d2129; margin-bottom: 12px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.stat { padding: 16px; background: #f7f8fa; border-radius: 6px; }
.stat-label { font-size: 13px; color: #606770; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 600; color: #1d2129; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #e1e4e8; }
th { font-size: 13px; color: #606770; font-weight: 500; }
td { font-size: 14px; color: #1d2129; }
tr:hover { background: #f7f8fa; }
</style>
