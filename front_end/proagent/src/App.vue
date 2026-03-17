<template>
  <div class="macos-app-container">
    <SidebarLeft
      :current-view="currentView"
      :is-settings-open="isSettingsOpen"
      @toggleSettings="toggleSettings"
    />

    <div class="macos-main-column">
      <TopBar
        v-if="!isSettingsOpen"
        :current-view="currentView"
        :is-agent-open="isAgentOpen"
        @update:currentView="currentView = $event"
        @toggleAgent="toggleAgent"
      />

      <main class="macos-content-area">
        <UserSettingsView v-if="isSettingsOpen" />
        <KeepAlive v-else>
          <component :is="viewComponent" />
        </KeepAlive>
      </main>
    </div>

    <AgentSidebar :is-open="isAgentOpen && !isSettingsOpen" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SidebarLeft from './components/layout/SidebarLeft.vue'
import TopBar from './components/layout/TopBar.vue'
import AgentSidebar from './components/layout/AgentSidebar.vue'
import DashboardView from './views/DashboardView.vue'
import CalendarView from './views/CalendarView.vue'
import UserSettingsView from './views/UserSettingsView.vue'

const isAgentOpen = ref(true)
const currentView = ref('dashboard')
const isSettingsOpen = ref(false)

const viewComponent = computed(() => {
  return currentView.value === 'dashboard' ? DashboardView : CalendarView
})

const toggleAgent = () => {
  isAgentOpen.value = !isAgentOpen.value
}

const toggleSettings = () => {
  isSettingsOpen.value = !isSettingsOpen.value
}
</script>

<style>
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
  background-color: #f5f5f7;
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
  background: rgba(255, 255, 255, 0.85);
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden; 
  min-width: 0;
}
</style>