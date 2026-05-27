import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import ChatView from './views/ChatView.vue'
import MonitorView from './views/MonitorView.vue'
import FeishuConvView from './views/FeishuConvView.vue'
import GraphView from './views/GraphView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'chat', component: ChatView },
    { path: '/monitor', name: 'monitor', component: MonitorView },
    { path: '/feishu', name: 'feishu', component: FeishuConvView },
    { path: '/graph', name: 'graph', component: GraphView }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
