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
        <div class="nav-item" :class="{ active: appMode === 'agent-settings' }" @click="emit('setAppMode', 'agent-settings')">
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Agent 设置
        </div>
      </div>

      <div class="divider dashed"></div>

      <div class="nav-group">
        <div class="nav-title">通知</div>

        <!-- 新邮件通知 -->
        <div
          v-for="n in emailStore.notifications"
          :key="n.id"
          class="notif-card"
          @click="goToEmail"
        >
          <span class="notif-badge">📧</span>
          <span class="notif-title">{{ n.title }}</span>
          <button class="notif-dismiss" @click.stop="emailStore.dismissNotification(n.id)">✕</button>
        </div>
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
        <span class="avatar">{{ avatarLetters }}</span>
        <span class="user-meta">
          <span class="user-name">{{ displayName }}</span>
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
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth.js'
import { useEmailStore } from '../../stores/email.js'

const router = useRouter()
const auth = useAuthStore()
const emailStore = useEmailStore()

const displayName = computed(() => {
  const name = auth.user?.full_name || auth.user?.email?.split('@')[0] || ''
  return name || 'User'
})

const avatarLetters = computed(() => {
  const name = displayName.value
  if (name.length >= 2) return name.slice(0, 2).toUpperCase()
  return name.slice(0, 1).toUpperCase() || 'U'
})

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
  if (props.appMode === 'settings') {
    emit('setAppMode', 'main')
  } else {
    emit('setAppMode', 'settings')
  }
}

const goToEmail = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'email')
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
}

/* 新邮件通知 */
.notif-group {
  padding: 4px 8px;
}

.notif-card {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  margin: 2px 0;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  background: rgba(0, 122, 255, 0.06);
  border: 1px solid rgba(0, 122, 255, 0.12);
  transition: background 0.15s;
}
.notif-card:hover {
  background: rgba(0, 122, 255, 0.12);
}

.notif-badge {
  flex-shrink: 0;
  font-size: 13px;
}

.notif-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1d1d1f;
}

.notif-dismiss {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 11px;
  cursor: pointer;
  padding: 0 2px;
  line-height: 1;
}
.notif-dismiss:hover {
  color: #ff3b30;
}
</style>