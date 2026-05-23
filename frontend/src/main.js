import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth.js'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

async function startBackend() {
  try {
    const { Command } = await import('@tauri-apps/plugin-shell')
    const cmd = Command.sidecar('binaries/python-backend')
    cmd.spawn()
    console.log('[ProAgent] Backend sidecar started')
    // Wait for backend to be ready
    await new Promise(resolve => setTimeout(resolve, 3000))
  } catch (e) {
    // Not running in Tauri, skip (use external backend)
    console.log('[ProAgent] Not in Tauri environment, using external backend')
  }
}

async function init() {
  await startBackend()
  const authStore = useAuthStore()
  await authStore.initAuth()
  app.use(router)
  app.mount('#app')
}

init()