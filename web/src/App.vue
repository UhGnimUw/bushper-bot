<template>
  <div id="app">
    <header>
      <h1>🤖 Agent Chat</h1>
      <nav>
        <router-link to="/">对话</router-link>
        <router-link to="/monitor">监控</router-link>
        <router-link to="/feishu">飞书会话</router-link>
      </nav>
      <button v-if="$route.name === 'chat'" id="clear-btn" @click="doClear">清除历史</button>
    </header>
    <router-view />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
const doClear = () => { router.go(0) }
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
header { background: #fff; border-bottom: 1px solid #e1e4e8; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
header h1 { font-size: 16px; font-weight: 600; color: #1d2129; }
header nav { display: flex; gap: 16px; }
header nav a { color: #606770; text-decoration: none; font-size: 14px; padding: 4px 8px; border-radius: 4px; }
header nav a:hover, header nav a.router-link-active { color: #0084ff; background: #f0f8ff; }
#clear-btn { background: none; border: 1px solid #d0d4da; border-radius: 6px; padding: 5px 12px; font-size: 13px; cursor: pointer; color: #606770; }
#clear-btn:hover { background: #f7f8fa; }
</style>
