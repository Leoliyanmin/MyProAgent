<template>
  <div v-if="!isAuthReady" class="macos-app-container flex-center">
    <div class="loading-spinner"></div>
  </div>
  <div v-else-if="route.meta.requiresAuth === false" class="macos-app-container">
    <router-view />
  </div>
  <div v-else class="macos-app-container">
    <SidebarLeft
      :current-view="currentView"
      :app-mode="appMode"
      @setAppMode="setAppMode"
      @update:currentView="currentView = $event"
    />

    <div class="macos-main-column">
      <TopBar
        v-if="appMode !== 'settings'"
        :current-view="currentView"
        :is-agent-open="isAgentOpen"
        @update:currentView="currentView = $event"
        @toggleAgent="toggleAgent"
      />

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
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'
import SidebarLeft from './components/layout/SidebarLeft.vue'
import TopBar from './components/layout/TopBar.vue'
import AgentSidebar from './components/layout/AgentSidebar.vue'
import ThemeOverlayEditor from './components/layout/ThemeOverlayEditor.vue'
import { useThemeStore } from './stores/theme.js'

const themeStore = useThemeStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const isAuthReady = ref(false)

onMounted(async () => {
  themeStore.applyToRoot()
  await authStore.initAuth()
  isAuthReady.value = true
})

const isAgentOpen = ref(true)
const currentView = ref('dashboard')
const appMode = ref('main')

// Update currentView based on route
watch(() => route.name, (newName) => {
  if (['dashboard', 'calendar', 'files', 'self-portrait', 'user-settings'].includes(newName)) {
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
    'selfPortrait': 'self-portrait'
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

const toggleAgent = () => {
  isAgentOpen.value = !isAgentOpen.value
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
  flex: 1; /* 占据除左右侧边栏外的所有剩余空间 */
  display: flex;
  flex-direction: column;
  min-width: 0; /* 关键：防止内部 Grid/Flex 子元素撑破容器宽度 */
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
</style>