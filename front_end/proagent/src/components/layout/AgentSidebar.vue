<template>
  <aside 
    class="macos-sidebar right-sidebar agent-panel" 
    :class="{ 'is-collapsed': !isOpen }"
  >
    <div class="agent-header">
      <span class="font-semibold">Agent 助手</span>
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
</script>

<style scoped>
/* 右侧侧边栏核心容器样式 */
.right-sidebar {
  width: 300px; /* 展开时的固定宽度 */
  flex-shrink: 0; /* 关键：防止被左侧和中间的工作区挤压 */
  background: rgba(235, 235, 235, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  /* 宽度变化的平滑过渡动画 */
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
  overflow: hidden; /* 关键：折叠时隐藏内部超出边界的内容 */
}

/* 折叠状态样式 */
.right-sidebar.is-collapsed {
  width: 0;
  border-left: none; /* 折叠时去掉左边框，使其完全消失 */
}

/* 内部结构样式 */
.agent-header {
  height: 52px; /* 与左侧 TopBar 的高度严格对齐 */
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  flex-shrink: 0;
  /* 关键：防止在折叠动画过程中文字自动换行导致布局闪烁 */
  white-space: nowrap; 
}

.agent-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  white-space: nowrap; /* 同理，保护内部布局在折叠时不断行 */
}

.placeholder-text {
  color: #86868b;
  font-size: 13px;
}
</style>