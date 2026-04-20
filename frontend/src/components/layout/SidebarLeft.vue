<template>
  <aside class="macos-sidebar left-sidebar">
    <div class="sidebar-content">
      <div class="sidebar-top-spacer"></div>

      <div class="nav-group">
        <div class="nav-title">通用功能</div>
        <div class="nav-item" :class="{ active: appMode === 'main' && currentView === 'dashboard' }" @click="goHome">
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          工作区主页
        </div>
        <div class="nav-item" :class="{ active: appMode === 'theme' }" @click="emit('setAppMode', 'theme')">
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          主题设置
        </div>
        <div class="nav-item">
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
          通用接口 B
        </div>
      </div>

      <div class="divider dashed"></div>

      <div class="nav-group">
        <div class="nav-title">
          {{ currentView === 'dashboard' ? '主界面特有' : currentView === 'calendar' ? '日程特有' : currentView === 'fileManager' ? '文件管理特有' : currentView === 'selfPortrait' ? '自我画像特有' : '功能' }}
        </div>

        <template v-if="currentView === 'dashboard'">
          <div class="nav-item">工作流配置</div>
          <div class="nav-item">消息源管理</div>
        </template>

        <template v-else-if="currentView === 'calendar'">
          <div class="nav-item">日历订阅</div>
          <div class="nav-item">时区设置</div>
        </template>

        <template v-else-if="currentView === 'fileManager'">
          <div class="nav-item">本地挂载点</div>
          <div class="nav-item">云存储同步</div>
        </template>

        <template v-else-if="currentView === 'selfPortrait'">
          <div class="nav-item">画像维度</div>
          <div class="nav-item">展示预览</div>
        </template>
      </div>
    </div>

    <div class="sidebar-footer">
      <button
        class="user-profile-btn"
        :class="{ active: appMode === 'settings' }"
        type="button"
        title="用户设置"
        @click="toggleSettings"
      >
        <span class="avatar">YM</span>
        <span class="user-meta">
          <span class="user-name">Yanmin</span>
          <span class="user-role">用户设置</span>
        </span>
      </button>
      <button
        class="logout-btn"
        type="button"
        title="退出登录"
        @click="handleLogout"
      >
        Sign Out
      </button>
    </div>
  </aside>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

const handleLogout = () => {
  auth.logout()
  router.push('/login')
}

const props = defineProps({
  currentView: {
    type: String,
    default: 'dashboard'
  },
  appMode: {
    type: String,
    default: 'main'
  }
})

const emit = defineEmits(['setAppMode', 'update:currentView'])

const goHome = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const toggleSettings = () => {
  // 如果已在设置页面，点击返回 main；否则进入设置页面
  if (props.appMode === 'settings') {
    emit('setAppMode', 'main')
  } else {
    emit('setAppMode', 'settings')
  }
}
</script>

<style scoped>
/* 基础侧边栏布局 */
.left-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background-color: var(--clr-bg-sidebar, rgba(235, 235, 235, 0.65));
  background-image: var(--clr-bg-sidebar-image, none);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.logout-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #ff3b30;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.logout-btn:hover {
  background: rgba(255, 59, 48, 0.1);
}

.user-profile-btn {
  flex: 1;
}

.user-profile-btn {
  width: 100%;
  border: 1px solid #000000;
  border-radius: 10px;
  background: #ffffff;
  padding: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  text-align: left;
}

.user-profile-btn:hover {
  background: #f5f5f5;
}

.user-profile-btn.active {
  background: #f3f4f6;
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
  color: #000000;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.user-role {
  color: rgba(0, 0, 0, 0.65);
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

.icon-svg {
  width: 18px;
  height: 18px;
  color: rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}

.nav-item.active .icon-svg {
  color: rgba(0, 0, 0, 0.8);
}

.nav-item:hover .icon-svg {
  color: rgba(0, 0, 0, 0.7);
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