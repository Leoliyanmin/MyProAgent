<template>
  <div v-if="!isAuthReady" class="macos-app-container flex-center">
    <div class="loading-spinner"></div>
  </div>
  <div v-else-if="route.meta.requiresAuth === false" class="macos-app-container">
    <router-view />
  </div>
  <div v-else class="macos-app-container" :class="{ 'theme-editing-mode': appMode === 'theme' }">
    <SidebarLeft
      :current-view="currentView"
      :app-mode="appMode"
      @setAppMode="setAppMode"
      @update:currentView="currentView = $event"
      @toggleAgent="toggleAgent"
    />

    <div class="macos-main-column">
      <header v-if="appMode !== 'settings'" class="macos-topbar macos-mini-bar">
        <div class="mini-bar-spacer"></div>
        <button
          class="mini-bar-agent-btn"
          :class="{ 'is-active': isAgentOpen }"
          @click="toggleAgent"
          title="切换 Agent 助手"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M15 3v18"/></svg>
        </button>
      </header>

      <main class="macos-content-area">
        <router-view v-slot="{ Component }">
          <KeepAlive>
            <component :is="Component" />
          </KeepAlive>
        </router-view>
      </main>
    </div>

    <AgentSidebar
      :is-open="isAgentOpen && appMode !== 'settings'"
      @toggleFromSelf="toggleAgent"
    />

    <ThemeOverlayEditor
      v-if="appMode === 'theme'"
      @exit="setAppMode('main')"
    />
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'
import { useCalendarStore } from './stores/calendar.js'
import { useDashboardStore } from './stores/dashboard.js'
import SidebarLeft from './components/layout/SidebarLeft.vue'
import AgentSidebar from './components/layout/AgentSidebar.vue'
import ThemeOverlayEditor from './components/layout/ThemeOverlayEditor.vue'
import { useThemeStore } from './stores/theme.js'
import { useEmailStore } from './stores/email.js'

const themeStore = useThemeStore()
const emailStore = useEmailStore()
const authStore = useAuthStore()
const calendarStore = useCalendarStore()
const dashboardStore = useDashboardStore()
const route = useRoute()
const router = useRouter()

const isAuthReady = ref(true)

let pollTimer = null
const isAgentOpen = ref(!dashboardStore.layoutConfig.some(item => item.i === 'mini-agent'))
const currentView = ref('dashboard')
const appMode = ref('main')

const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    if (!authStore.isAuthenticated) return
    try {
      await Promise.all([
        calendarStore.loadSchedules(),
        dashboardStore.loadTodosFromBackend()
      ])
    } catch {
      // silent — polling runs in background
    }
  }, 60000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const loadInitialData = async () => {
  if (!authStore.isAuthenticated) return
  try {
    await Promise.all([
      calendarStore.loadSchedules(),
      dashboardStore.loadTodosFromBackend()
    ])
    try {
      await calendarStore.importBlackboardAssignments()
    } catch { /* user may not have Blackboard bound yet */ }
  } catch (err) {
    console.error('Failed to load initial data:', err)
  }
}

onMounted(() => {
  themeStore.applyToRoot()
  syncAgentShellWithLayout()
  if (authStore.isAuthenticated) {
    loadInitialData()
    emailStore.fetchStatus()
    startPolling()
  }

  window.addEventListener('auth:required', handleAuthRequired)
  window.addEventListener('agent-pop-to-dashboard', popAgentToDashboard)
  window.addEventListener('agent-retract-to-sidebar', retractAgentToSidebar)
})

onBeforeUnmount(() => {
  stopPolling()
  window.removeEventListener('auth:required', handleAuthRequired)
  window.removeEventListener('agent-pop-to-dashboard', popAgentToDashboard)
  window.removeEventListener('agent-retract-to-sidebar', retractAgentToSidebar)
})

watch(() => authStore.isAuthenticated, (newVal) => {
  if (newVal) {
    loadInitialData()
    startPolling()
  } else {
    stopPolling()
  }
})

// Update currentView based on route
watch(() => route.name, (newName) => {
  if (['dashboard', 'calendar', 'files', 'self-portrait', 'email', 'user-settings'].includes(newName)) {
    if (newName === 'user-settings') {
      appMode.value = 'settings'
    } else {
      appMode.value = 'main'
      currentView.value = newName === 'self-portrait' ? 'selfPortrait' : newName === 'files' ? 'fileManager' : newName
    }
  }
})

// Sync sidebar clicks to router
watch(currentView, (newView) => {
  const nameMap = {
    'dashboard': 'dashboard',
    'calendar': 'calendar',
    'fileManager': 'files',
    'selfPortrait': 'self-portrait',
    'email': 'email'
  }
  if (nameMap[newView] && route.name !== nameMap[newView]) {
    router.push({ name: nameMap[newView] })
  }
})

watch(appMode, (newMode) => {
  if (newMode === 'settings') {
    if (route.name !== 'user-settings') {
      router.push({ name: 'user-settings' })
    }
  } else if (newMode === 'main' && route.name === 'user-settings') {
     router.push({ name: 'dashboard' })
  }
})

const hasAgentMini = () => dashboardStore.layoutConfig.some(item => item.i === 'mini-agent')

const syncAgentShellWithLayout = () => {
  if (hasAgentMini()) isAgentOpen.value = false
}

const ensureAgentMini = () => {
  if (!hasAgentMini()) dashboardStore.toggleMiniWidget('agent')
}

const removeAgentMini = () => {
  if (hasAgentMini()) dashboardStore.toggleMiniWidget('agent')
}

const popAgentToDashboard = () => {
  ensureAgentMini()
  isAgentOpen.value = false
}

const retractAgentToSidebar = () => {
  removeAgentMini()
  isAgentOpen.value = true
}

const toggleAgent = () => {
  isAgentOpen.value = !isAgentOpen.value
  if (isAgentOpen.value) removeAgentMini()
}

const handleAuthRequired = () => {
  authStore.token = null
  router.push('/login')
}

const setAppMode = (mode) => {
  appMode.value = mode
}
</script>

<style>
.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}
.loading-spinner {
  border: 4px solid rgba(0,0,0,0.1);
  border-left-color: var(--clr-primary, #007aff);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
/* * 全局样式与外壳布局 
 * 注意：这里不使用 <style scoped>，以确保样式能作用于整个 App 骨架
 */
html, body, #app {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden; /* 防止出现全局原生滚动条 */
}

/* 核心：三栏式水平布局容器 */
.macos-app-container {
  display: flex; /* 激活水平 Flexbox */
  flex-direction: row;
  height: 100vh;
  width: 100vw;
  background-color: var(--clr-bg-app, #f5f5f7);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  color: #1d1d1f;
}

/* 中部核心区：垂直 Flexbox */
.macos-main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 窄顶栏 — 仅用于 Agent 切换按钮 */
.macos-mini-bar {
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 12px;
  background-color: var(--clr-bg-topbar, rgba(235, 235, 235, 0.65));
  background-image: var(--clr-bg-topbar-image, none);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.mini-bar-spacer {
  flex: 1;
}

.mini-bar-agent-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 4px 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.mini-bar-agent-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #1d1d1f;
}

.mini-bar-agent-btn.is-active {
  background: rgba(0, 0, 0, 0.08);
  color: #1d1d1f;
}

/* 动态内容注入区：自适应高度并允许内部滚动 */
.macos-content-area {
  flex: 1;
  background-color: var(--clr-bg-content, #f5f5f7);
  background-image: var(--clr-bg-content-image, none);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden; 
  min-width: 0;
}

/* ── Theme Editing Mode ── */
/* Hide all content inside layout zones, keeping only their backgrounds visible */
.theme-editing-mode .left-sidebar > *,
.theme-editing-mode .macos-mini-bar > *,
.theme-editing-mode .right-sidebar > * {
  visibility: hidden;
}

/* Content area: hide routed content children */
.theme-editing-mode .macos-content-area > * {
  visibility: hidden;
}

</style>
