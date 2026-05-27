import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

export const chatAPI = {
  send: (message, sessionId = null) => axios.post('/chat', { message, session_id: sessionId }),
  clear: (sessionId) => axios.delete(`/clear/${sessionId}`)
}

export const monitorAPI = {
  stats: () => api.get('/monitor/stats'),
  recent: (hours = 24, limit = 100) => api.get(`/monitor/recent?hours=${hours}&limit=${limit}`)
}

export const feishuAPI = {
  conversations: (sessionId = null, limit = 50) => api.get(`/feishu/conversations?session_id=${sessionId || ''}&limit=${limit}`),
  sessions: (limit = 20) => api.get(`/feishu/sessions?limit=${limit}`)
}

export default api
