<template>
  <aside class="macos-sidebar left-sidebar">
    <div class="sidebar-content">
      <div class="sidebar-top-spacer"></div>

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

    <div class="sidebar-footer">
      <button
        class="user-profile-btn"
        :class="{ active: isSettingsOpen }"
        type="button"
        title="用户设置"
        @click="emit('toggleSettings')"
      >
        <span class="avatar">YM</span>
        <span class="user-meta">
          <span class="user-name">Yanmin</span>
          <span class="user-role">用户设置</span>
        </span>
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  currentView: {
    type: String,
    default: 'dashboard'
  },
  isSettingsOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggleSettings'])
</script>

<style scoped>
/* 基础侧边栏布局 */
.left-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(235, 235, 235, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

.sidebar-top-spacer {
  height: 12px; /* 替代原本窗口控制块的高度位置 */
}

/* 🛑 已移除：.window-controls 和 .mac-dot 相关 CSS */

/* 菜单内容区排版 */
.sidebar-content {
  padding: 0 12px;
  flex: 1;
  overflow-y: auto;
}

.sidebar-footer {
  padding: 10px 12px 14px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.user-profile-btn {
  width: 100%;
  border: none;
  border-radius: 10px;
  background: transparent;
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-align: left;
}

.user-profile-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-profile-btn.active {
  background: rgba(0, 122, 255, 0.12);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  background: linear-gradient(135deg, #111827, #4b5563);
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  color: #1d1d1f;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.user-role {
  color: rgba(0, 0, 0, 0.5);
  font-size: 11px;
  line-height: 1.2;
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