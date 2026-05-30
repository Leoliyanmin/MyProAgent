<template>
  <aside class="macos-sidebar left-sidebar">
    <div class="sidebar-content">
      <div class="sidebar-top-spacer"></div>

      <div class="nav-group">
        <div class="nav-title">通用功能</div>
        <div class="nav-item nav-item-home" :class="{ active: appMode === 'main' && currentView === 'dashboard' }" @click="goHome">
          <svg class="icon-svg home-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>
          </svg>
          <span class="nav-label">主界面</span>
        </div>
        <div
          class="nav-item nav-item-calendar"
          :class="{ active: appMode === 'main' && currentView === 'calendar' }"
          @click="goToCalendar"
          @mouseenter="hoverCalendar = true"
          @mouseleave="hoverCalendar = false"
        >
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/><path d="M16 18h.01"/>
          </svg>
          <span class="nav-label">日程规划</span>
          <span v-show="hoverCalendar" class="nav-item-actions">
            <button class="mini-icon-btn" @click.stop="openTodo" title="待办">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            </button>
          </span>
        </div>
        <div
          class="nav-item nav-item-files"
          :class="{ active: appMode === 'main' && currentView === 'fileManager' }"
          @click="goToFileManager"
          @mouseenter="hoverFiles = true"
          @mouseleave="hoverFiles = false"
        >
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
          </svg>
          <span class="nav-label">文件管理</span>
          <span v-show="hoverFiles" class="nav-item-actions">
            <button class="mini-icon-btn" @click.stop="openNote" title="笔记">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </button>
          </span>
        </div>
        <div
          class="nav-item nav-item-email"
          :class="{ active: appMode === 'main' && currentView === 'email' }"
          @click="goToEmailNav"
          @mouseenter="hoverEmail = true"
          @mouseleave="hoverEmail = false"
        >
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
          </svg>
          <span class="nav-label">邮件管理</span>
          <span v-show="hoverEmail" class="nav-item-actions">
            <button class="mini-icon-btn" @click.stop="openCompose" title="写邮件">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
            <button class="mini-icon-btn" @click.stop="openInbox" title="收件箱">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
            </button>
          </span>
        </div>
        <div
          class="nav-item nav-item-self"
          :class="{ active: appMode === 'main' && currentView === 'selfPortrait' }"
          @click="goToSelfPortrait"
          @mouseenter="hoverSelf = true"
          @mouseleave="hoverSelf = false"
        >
          <svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span class="nav-label">自我画像</span>
          <span v-show="hoverSelf" class="nav-item-actions">
            <button class="mini-icon-btn" @click.stop="openHeatmap" title="热力图">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            </button>
          </span>
        </div>
        <div class="nav-item nav-item-theme" :class="{ active: appMode === 'theme' }" @click="emit('setAppMode', 'theme')">
          <svg class="icon-svg theme-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          <span class="nav-label">主题设置</span>
        </div>

        <div
          class="nav-item nav-item-agent"
          @click="emit('toggleAgent')"
          @mouseenter="hoverAgent = true"
          @mouseleave="hoverAgent = false"
        >
          <svg class="icon-svg agent-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M15 3v18"/>
          </svg>
          <span class="nav-label">Agent 助手</span>
          <span v-show="hoverAgent" class="nav-item-actions">
            <button class="mini-icon-btn" @click.stop="openAgent" title="对话窗">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </button>
          </span>
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
import { computed, ref } from 'vue'
import { useAuthStore } from '../../stores/auth.js'
import { useEmailStore } from '../../stores/email.js'
import { useDashboardStore } from '../../stores/dashboard.js'

const router = useRouter()
const auth = useAuthStore()
const emailStore = useEmailStore()
const dashboardStore = useDashboardStore()
const hoverEmail = ref(false)
const hoverFiles = ref(false)
const hoverCalendar = ref(false)
const hoverSelf = ref(false)
const hoverAgent = ref(false)

const displayName = computed(() => {
  const name = auth.user?.full_name || 'User'
  return name
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

const emit = defineEmits(['setAppMode', 'update:currentView', 'toggleAgent'])

const goHome = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const goToCalendar = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'calendar')
}

const goToFileManager = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'fileManager')
}

const goToEmailNav = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'email')
}

const goToSelfPortrait = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'selfPortrait')
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

const openCompose = () => {
  dashboardStore.toggleMiniWidget('compose')
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const openInbox = () => {
  dashboardStore.toggleMiniWidget('inbox')
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const openNote = () => {
  dashboardStore.toggleMiniWidget('note')
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const openTodo = () => {
  dashboardStore.toggleMiniWidget('todo')
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const openHeatmap = () => {
  dashboardStore.toggleMiniWidget('heatmap')
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
}

const openAgent = () => {
  emit('setAppMode', 'main')
  emit('update:currentView', 'dashboard')
  const hasAgentMini = dashboardStore.layoutConfig.some(item => item.i === 'mini-agent')
  window.dispatchEvent(new CustomEvent(hasAgentMini ? 'agent-retract-to-sidebar' : 'agent-pop-to-dashboard'))
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
  color: #007aff;
}

/* ── hover 展开 mini 窗口按钮 ── */
.nav-item-email {
  position: relative;
}

.nav-label {
  flex: 1;
  min-width: 0;
}

.nav-item-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  margin-left: auto;
}

.mini-icon-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 5px;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.35);
  transition: all 0.15s;
  flex-shrink: 0;
}

.mini-icon-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: #007aff;
}

/* 主题设置 hover */
.nav-item-theme:hover .theme-icon {
  animation: grid-pulse 0.5s ease;
  color: #007aff;
}

/* 主界面 hover */
.nav-item-home:hover .home-icon {
  animation: grid-pulse 0.5s ease;
  color: #007aff;
}
@keyframes grid-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
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
