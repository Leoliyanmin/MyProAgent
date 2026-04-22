<template>
  <header class="macos-topbar">
    <div class="topbar-left"></div>

    <div class="topbar-center">
      <div class="segmented-control">
        <button 
          class="segment" 
          :class="{ active: currentView === 'dashboard' }"
          @click="emit('update:currentView', 'dashboard')"
        >
          <svg class="segment-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>
          <span>主界面</span>
        </button>
        
        <button 
          class="segment" 
          :class="{ active: currentView === 'calendar' }"
          @click="emit('update:currentView', 'calendar')"
        >
          <svg class="segment-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/></svg>
          <span>日程规划</span>
        </button>

        <button 
          class="segment" 
          :class="{ active: currentView === 'fileManager' }"
          @click="emit('update:currentView', 'fileManager')"
        >
          <svg class="segment-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
          <span>文件管理</span>
        </button>

        <button 
          class="segment" 
          :class="{ active: currentView === 'selfPortrait' }"
          @click="emit('update:currentView', 'selfPortrait')"
        >
          <svg class="segment-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span>自我画像</span>
        </button>
      </div>
    </div>
    
    <div class="topbar-right">
      <button 
        class="icon-btn agent-toggle-btn" 
        :class="{ 'is-active': isAgentOpen }"
        @click="emit('toggleAgent')" 
        title="切换 Agent 助手"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M15 3v18"/></svg>
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  currentView: {
    type: String,
    required: true
  },
  isAgentOpen: {
    type: Boolean,
    required: true
  }
})

// 增加 toggleAgent 事件派发
const emit = defineEmits(['update:currentView', 'toggleAgent'])
</script>

<style scoped>
.macos-topbar {
  height: 52px;
  background-color: var(--clr-bg-topbar, rgba(235, 235, 235, 0.65));
  background-image: var(--clr-bg-topbar-image, none);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between; /* 采用 Flex Space Between 布局 */
  padding: 0 16px;
  flex-shrink: 0;
}

.topbar-left, .topbar-right {
  flex: 1;
  display: flex;
  align-items: center;
}

.topbar-right {
  justify-content: flex-end; /* 右侧按钮靠右对齐 */
}

.topbar-center {
  display: flex;
  justify-content: center;
}

/* 分段控制器样式保持不变 */
.segmented-control {
  display: flex;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px;
  border-radius: 8px;
  gap: 1px;
}

.segment {
  background: transparent;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  color: rgba(0, 0, 0, 0.7);
  font-size: 13px;
  font-weight: 500;
}

.segment-icon {
  color: rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}

.segment:hover { color: #000; }

.segment.active {
  background: #ffffff;
  color: #000;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  font-weight: 600;
}

.segment.active .segment-icon { color: #007aff; }

/* 全局侧边栏控制按钮样式 */
.agent-toggle-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.5);
  transition: all 0.2s ease;
}

.agent-toggle-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
}

/* 当侧边栏处于打开状态时，图标可以呈现激活态的高亮 */
.agent-toggle-btn.is-active {
  background: rgba(0, 0, 0, 0.08);
  color: #1d1d1f;
}
</style>