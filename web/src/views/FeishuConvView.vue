<template>
  <div class="feishu-view">
    <div class="container">
      <div class="sessions">
        <h2>会话列表</h2>
        <div v-for="s in sessions" :key="s.session_id" :class="['session-item', { active: selectedSession === s.session_id }]" @click="selectSession(s.session_id)">
          <div class="session-name">{{ s.user_name || s.session_id }}</div>
          <div class="session-meta">{{ s.message_count }}条消息 | {{ new Date(s.last_message).toLocaleString() }}</div>
        </div>
      </div>
      <div class="conversations">
        <h2>对话详情</h2>
        <div v-if="!selectedSession" class="empty">请选择左侧会话查看详情</div>
        <div v-else>
          <div v-for="c in conversations" :key="c.id" class="conv-item">
            <div class="conv-user">用户: {{ c.message }}</div>
            <div v-if="c.response" class="conv-assistant">助手: {{ c.response }}</div>
            <div class="conv-time">{{ new Date(c.timestamp).toLocaleString() }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { feishuAPI } from '@/api/agent.js'
const sessions = ref([]), selectedSession = ref(null), conversations = ref([])
const loadSessions = async () => { try { const res = await feishuAPI.sessions(); if (res.data.ok) sessions.value = res.data.sessions } catch (e) { console.error(e) } }
const selectSession = async (sessionId) => {
  selectedSession.value = sessionId
  try { const res = await feishuAPI.conversations(sessionId); if (res.data.ok) conversations.value = res.data.conversations.reverse() } catch (e) { console.error(e) }
}
onMounted(() => { loadSessions(); setInterval(loadSessions, 30000) })
</script>

<style scoped>
.feishu-view { flex: 1; overflow: hidden; }
.container { flex: 1; padding: 20px; display: flex; gap: 20px; overflow: hidden; }
.sessions, .conversations { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.08); overflow-y: auto; }
.sessions { width: 300px; }
.conversations { flex: 1; }
.sessions h2, .conversations h2 { font-size: 16px; color: #1d2129; margin-bottom: 12px; }
.session-item { padding: 12px; border-radius: 6px; cursor: pointer; margin-bottom: 8px; }
.session-item:hover { background: #f7f8fa; }
.session-item.active { background: #e8f0fe; }
.session-name { font-size: 14px; font-weight: 500; color: #1d2129; }
.session-meta { font-size: 12px; color: #606770; margin-top: 4px; }
.conv-item { padding: 12px; border-bottom: 1px solid #e1e4e8; }
.conv-user { font-size: 14px; font-weight: 500; color: #0084ff; }
.conv-assistant { font-size: 14px; color: #1d2129; margin-top: 8px; }
.conv-time { font-size: 12px; color: #606770; margin-top: 4px; }
.empty { text-align: center; color: #606770; padding: 40px; }
</style>
