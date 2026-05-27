<template>
  <div class="chat-view">
    <div class="chat-header">
      <span class="chat-title">智能对话</span>
      <span class="session-info" v-if="sessionId">会话ID: {{ sessionId.slice(0,8) }}...</span>
    </div>
    <div class="chat-messages" ref="messagesEl">
      <div v-if="messages.length === 0" class="empty-hint">
        <div class="hint-icon">💬</div>
        <div class="hint-text">开始对话吧！试试问问我关于城市、知识图谱的问题</div>
      </div>
      <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">
        <div class="msg-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="msg-content">
          <div class="msg-bubble">{{ msg.text }}</div>
          <div class="msg-time">{{ msg.time }}</div>
        </div>
      </div>
      <div v-if="thinking" class="msg assistant thinking">
        <div class="msg-avatar">🤖</div>
        <div class="msg-content">
          <div class="msg-bubble typing">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="chat-input-bar">
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          placeholder="输入消息... (Shift+Enter换行，Enter发送)"
          @keydown.enter.exact.prevent="sendMsg"
          @keydown.shift.enter="handleShiftEnter"
          ref="inputEl"
          rows="1"
        ></textarea>
        <button class="send-btn" @click="sendMsg" :disabled="busy || !inputText.trim()">
          <span v-if="!busy">发送</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatAPI } from '@/api/agent.js'

const messages = ref([])
const inputText = ref('')
const busy = ref(false)
const thinking = ref(false)
const sessionId = ref('')
const messagesEl = ref(null)
const inputEl = ref(null)

const now = () => {
  const d = new Date()
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

const addMsg = (role, text) => {
  messages.value.push({ role, text, time: now() })
  scrollToBottom()
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

const handleShiftEnter = (e) => {
  // Allow default textarea behavior for Shift+Enter
}

const autoResize = () => {
  if (inputEl.value) {
    inputEl.value.style.height = 'auto'
    inputEl.value.style.height = Math.min(inputEl.value.scrollHeight, 120) + 'px'
  }
}

const sendMsg = async () => {
  if (busy.value) return
  const text = inputText.value.trim()
  if (!text) return

  inputText.value = ''
  if (inputEl.value) inputEl.value.style.height = 'auto'
  addMsg('user', text)

  busy.value = true
  thinking.value = true

  try {
    const res = await chatAPI.send(text, sessionId.value || null)
    const data = res.data
    sessionId.value = data.session_id
    thinking.value = false
    addMsg('assistant', data.response)
    if (data.needs_human_input) {
      addMsg('assistant', '请补充上述信息后再次发送')
    }
  } catch (e) {
    thinking.value = false
    addMsg('error', '错误: ' + (e.message || '网络错误'))
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.chat-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 0;
  min-height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.chat-header {
  background: rgba(255,255,255,0.95);
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
}

.session-info {
  font-size: 12px;
  color: #8a8a8a;
  font-family: monospace;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.8);
  gap: 12px;
}

.hint-icon {
  font-size: 48px;
  opacity: 0.6;
}

.hint-text {
  font-size: 14px;
  opacity: 0.7;
}

.msg {
  display: flex;
  gap: 10px;
  max-width: 80%;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg.assistant {
  align-self: flex-start;
}

.msg.error {
  align-self: flex-start;
}

.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.msg-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.msg.user .msg-content {
  align-items: flex-end;
}

.msg-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 100%;
}

.msg.user .msg-bubble {
  background: #0084ff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg.assistant .msg-bubble {
  background: #fff;
  color: #1d2129;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.msg.error .msg-bubble {
  background: #fff2f0;
  color: #c00;
  border: 1px solid #fcb;
}

.msg-time {
  font-size: 11px;
  color: rgba(255,255,255,0.6);
}

.msg.assistant .msg-time {
  color: rgba(0,0,0,0.4);
}

.typing .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #8a8a8a;
  border-radius: 50%;
  margin: 0 2px;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing .dot:nth-child(1) { animation-delay: -0.32s; }
.typing .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.chat-input-bar {
  background: rgba(255,255,255,0.98);
  padding: 16px 20px;
  border-top: 1px solid rgba(255,255,255,0.2);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  max-width: 900px;
  margin: 0 auto;
}

.input-wrapper textarea {
  flex: 1;
  border: 2px solid #e1e4e8;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  max-height: 120px;
  overflow-y: auto;
}

.input-wrapper textarea:focus {
  border-color: #0084ff;
}

.send-btn {
  background: #0084ff;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  min-width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: #0073e6;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
