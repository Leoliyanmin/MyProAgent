<template>
  <aside class="macos-sidebar left-sidebar">
    <div class="window-controls">
      <i class="mac-dot close"></i>
      <i class="mac-dot minimize"></i>
      <i class="mac-dot maximize"></i>
    </div>

    <div class="sidebar-content">
      <div class="nav-group">
        <div class="nav-title">通用功能</div>
        <div class="nav-item active">
          <span class="icon">⌘</span>
          通用接口 A
        </div>
        <div class="nav-item">
          <span class="icon">⇧</span>
          通用接口 B
        </div>
      </div>

      <div class="divider dashed"></div>

      <div class="nav-group">
        <div class="nav-title">
          {{ currentView === 'dashboard' ? '主界面特有' : '日程特有' }}功能
        </div>

        <template v-if="currentView === 'dashboard'">
          <div class="nav-item">工作流配置</div>
          <div class="nav-item">消息源管理</div>
        </template>

        <template v-else-if="currentView === 'calendar'">
          <div class="nav-item">日历订阅</div>
          <div class="nav-item">时区设置</div>
        </template>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { defineProps } from 'vue'

// 接收从 App.vue 传来的 currentView 状态
defineProps({
  currentView: {
    type: String,
    default: 'dashboard'
  }
})
</script>

<style scoped>
/* 基础侧边栏布局 */
.left-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  /* 背景与毛玻璃滤镜 */
  background: rgba(235, 235, 235, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

/* macOS 红黄绿窗口控制键 */
.window-controls {
  padding: 16px 20px;
  display: flex;
  gap: 8px;
}

.mac-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
}
.mac-dot.close { background-color: #ff5f56; }
.mac-dot.minimize { background-color: #ffbd2e; }
.mac-dot.maximize { background-color: #27c93f; }

/* 菜单内容区排版 */
.sidebar-content {
  padding: 0 12px;
  flex: 1;
  overflow-y: auto;
}

.nav-group {
  margin-bottom: 16px;
}

.nav-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 12px;
  margin-bottom: 4px;
}

.nav-item {
  padding: 6px 12px;
  margin-bottom: 2px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.nav-item.active {
  background-color: rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

.icon {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.5);
}

/* 虚线分割线 */
.divider {
  height: 1px;
  margin: 12px 12px;
}
.divider.dashed {
  border-top: 1px dashed rgba(0, 0, 0, 0.15);
  background-color: transparent;
}
</style>