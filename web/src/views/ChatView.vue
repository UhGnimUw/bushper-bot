<template>
  <div class="chat-layout">
    <!-- Left Sidebar -->
    <div class="sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewChat">
          <span>+</span> 新建对话
        </button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          :class="['session-item', { active: currentSessionId === session.id }]"
          @click="loadSession(session.id)"
        >
          <span class="session-title">{{ session.title }}</span>
          <button class="delete-btn" @click.stop="deleteSession(session.id)">×</button>
        </div>
      </div>
    </div>

    <!-- Right Chat Area -->
    <div class="chat-area">
      <div class="chat-header">
        <span class="chat-title">{{ currentSessionTitle }}</span>
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
            placeholder="输入消息... (Enter发送)"
            @keydown.enter.exact.prevent="sendMsg"
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
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatAPI } from '@/api/agent.js'

const SESSIONS_KEY = 'chat_sessions'
const messages = ref([])
const inputText = ref('')
const busy = ref(false)
const thinking = ref(false)
const currentSessionId = ref(null)
const currentSessionTitle = ref('新对话')
const sessions = ref([])
const messagesEl = ref(null)

const now = () => {
  const d = new Date()
  return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
}

const loadSessionsFromStorage = () => {
  try {
    const stored = localStorage.getItem(SESSIONS_KEY)
    if (stored) {
      sessions.value = JSON.parse(stored)
    }
  } catch (e) {
    sessions.value = []
  }
}

const saveSessionsToStorage = () => {
  try {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.value))
  } catch (e) {
    console.error('Failed to save sessions:', e)
  }
}

const createNewChat = () => {
  const id = Date.now().toString()
  const title = '新对话'
  sessions.value.unshift({ id, title, messages: [] })
  saveSessionsToStorage()
  currentSessionId.value = id
  currentSessionTitle.value = title
  messages.value = []
}

const loadSession = (id) => {
  const session = sessions.value.find(s => s.id === id)
  if (session) {
    currentSessionId.value = id
    currentSessionTitle.value = session.title
    messages.value = session.messages || []
    scrollToBottom()
  }
}

const saveCurrentSession = () => {
  const session = sessions.value.find(s => s.id === currentSessionId.value)
  if (session) {
    session.messages = messages.value
    if (messages.value.length > 0) {
      const firstUserMsg = messages.value.find(m => m.role === 'user')
      if (firstUserMsg) {
        session.title = firstUserMsg.text.slice(0, 20) + (firstUserMsg.text.length > 20 ? '...' : '')
      }
    }
    saveSessionsToStorage()
  }
}

const deleteSession = (id) => {
  sessions.value = sessions.value.filter(s => s.id !== id)
  saveSessionsToStorage()
  if (currentSessionId.value === id) {
    if (sessions.value.length > 0) {
      loadSession(sessions.value[0].id)
    } else {
      createNewChat()
    }
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

const addMsg = (role, text) => {
  messages.value.push({ role, text, time: now() })
  scrollToBottom()
}

const sendMsg = async () => {
  if (busy.value) return
  const text = inputText.value.trim()
  if (!text) return

  inputText.value = ''
  addMsg('user', text)
  saveCurrentSession()

  busy.value = true
  thinking.value = true

  try {
    const res = await chatAPI.send(text, currentSessionId.value || null)
    const data = res.data
    currentSessionId.value = data.session_id
    thinking.value = false
    addMsg('assistant', data.response)
    if (data.needs_human_input) {
      addMsg('assistant', '请补充上述信息后再次发送')
    }
    saveCurrentSession()
  } catch (e) {
    thinking.value = false
    addMsg('error', '错误: ' + (e.message || '网络错误'))
  } finally {
    busy.value = false
  }
}

onMounted(() => {
  loadSessionsFromStorage()
  if (sessions.value.length === 0) {
    createNewChat()
  } else {
    loadSession(sessions.value[0].id)
  }
})
</script>

<style scoped>
.chat-layout {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  background: rgba(255,255,255,0.95);
  border-right: 1px solid #e1e4e8;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e1e4e8;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  background: #0084ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.new-chat-btn:hover {
  background: #0073e6;
}

.new-chat-btn span {
  font-size: 18px;
  font-weight: bold;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
}

.session-item:hover {
  background: #f0f8ff;
}

.session-item.active {
  background: #e8f0fe;
}

.session-title {
  font-size: 13px;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.delete-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: #8a8a8a;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #c00;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.chat-header {
  background: rgba(255,255,255,0.95);
  padding: 12px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.2);
}

.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d2129;
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
  max-width: 75%;
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
