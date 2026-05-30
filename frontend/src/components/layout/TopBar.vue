<template>
  <header class="macos-topbar">
    <div class="topbar-left"></div>

    <div class="topbar-center"></div>

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