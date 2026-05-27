<template>
  <div class="chat-view">
    <div id="chat">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">{{ msg.text }}</div>
      <div v-if="thinking" class="msg assistant thinking">思考中...</div>
    </div>
    <div id="input-bar">
      <input v-model="inputText" placeholder="输入消息..." @keydown.enter="sendMsg">
      <button @click="sendMsg" :disabled="busy">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { chatAPI } from '@/api/agent.js'
const messages = ref([]), inputText = ref(''), busy = ref(false), thinking = ref(false), sessionId = ref('')
const addMsg = (role, text) => messages.value.push({ role, text })
const sendMsg = async () => {
  if (busy.value) return
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  addMsg('user', text)
  busy.value = true
  thinking.value = true
  try {
    const res = await chatAPI.send(text, sessionId.value || null)
    const data = res.data
    sessionId.value = data.session_id
    thinking.value = false
    addMsg('assistant', data.response)
    if (data.needs_human_input) addMsg('assistant', '💡 请补充上述信息后再次发送')
  } catch (e) {
    thinking.value = false
    addMsg('error', '错误: ' + e.message)
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.chat-view { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
#chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
.msg { max-width: 72%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
.msg.user { align-self: flex-end; background: #0084ff; color: #fff; border-bottom-right-radius: 4px; }
.msg.assistant { align-self: flex-start; background: #fff; color: #1d2129; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }
.msg.error { background: #fff2f0; color: #c00; }
.thinking { color: #8a8a8a; font-size: 13px; }
#input-bar { background: #fff; border-top: 1px solid #e1e4e8; padding: 12px 16px; display: flex; gap: 10px; }
#input { flex: 1; border: 1px solid #d0d4da; border-radius: 8px; padding: 8px 12px; font-size: 14px; outline: none; }
#input:focus { border-color: #0084ff; }
button { background: #0084ff; color: #fff; border: none; border-radius: 8px; padding: 8px 16px; font-size: 14px; cursor: pointer; }
button:disabled { opacity: 0.5; cursor: default; }
</style>
