<template>
  <aside 
    class="macos-sidebar right-sidebar agent-panel" 
    :class="{ 'is-collapsed': !isOpen }"
  >
    <div class="agent-header">
      <span class="font-semibold">Agent 助手</span>
      
      <button class="icon-btn close-agent-btn" @click="emit('toggleFromSelf')" title="收起 Agent 助手">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
      </button>
    </div>
    <div class="agent-body">
      <div class="placeholder-text">在这里与 Agent 对话...</div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

// ⭐ 新增：定义组件自身触发的折叠事件
const emit = defineEmits(['toggleFromSelf'])
</script>

<style scoped>
/* 右侧侧边栏核心容器样式 */
.right-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: rgba(235, 235, 235, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
  overflow: hidden;
}

.right-sidebar.is-collapsed {
  width: 0;
  border-left: none;
}

/* 内部结构样式 */
.agent-header {
  height: 52px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between; /* ⭐ 核心：标题在左，按钮在右 */
  padding: 0 12px 0 16px; /* 调整 Padding 给按钮预留空间 */
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  flex-shrink: 0;
  white-space: nowrap; 
}

/* ⭐ 新增：收起按钮样式 */
.close-agent-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.close-agent-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
}

.agent-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  white-space: nowrap;
}

.placeholder-text {
  color: #86868b;
  font-size: 13px;
}
</style>