import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth.js'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

async function startBackend() {
  // Dev mode: backends already started by dev.js before Tauri opens
  if (import.meta.env.DEV) {
    console.log('[ProAgent] Dev mode: backends managed by dev.js, skipping spawn')
    return
  }

  try {
    const { Command } = await import('@tauri-apps/plugin-shell')
    const cmd = Command.sidecar('binaries/python-backend')
    cmd.spawn()
    console.log('[ProAgent] Backend sidecar spawned')
  } catch (e) {
    // Not running in Tauri, skip (use external backend)
    console.log('[ProAgent] Not in Tauri environment, using external backend')
  }
}

async function init() {
  try {
    await startBackend()
    const authStore = useAuthStore()
    await authStore.initAuth()
  } catch (e) {
    console.error('[ProAgent] Init error, mounting app anyway:', e)
  }
  app.use(router)
  app.mount('#app')
}

init()