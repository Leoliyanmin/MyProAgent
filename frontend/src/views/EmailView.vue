<template>
  <div class="email-engine">
    <!-- Toolbar -->
    <div class="email-toolbar">
      <h2 class="view-title">邮件管理</h2>
      <div class="toolbar-actions">
        <span v-if="bindStatus.is_bound" class="bind-badge bound">
          已绑定 {{ bindStatus.email_address }}
        </span>
        <span v-else class="bind-badge unbound">
          未绑定
          <router-link to="/user-settings" class="bind-link">前往设置绑定</router-link>
        </span>
        <button
          class="mac-btn-primary"
          :disabled="!bindStatus.is_bound || syncing"
          :class="{ 'is-loading': syncing }"
          @click="handleSync"
        >
          {{ syncing ? '同步中...' : '同步邮件' }}
        </button>
        <button
          class="mac-btn-secondary"
          :disabled="!bindStatus.is_bound || loading"
          :class="{ 'is-loading': loading }"
          @click="handleRefresh"
        >
          {{ loading ? '加载中...' : '刷新' }}
        </button>
        <button
          class="mac-btn-secondary trash-btn"
          :disabled="!bindStatus.is_bound"
          @click="openTrash"
        >
          🗑 {{ trashCount > 0 ? trashCount : '' }}
        </button>
        <button
          class="mac-btn-primary prioritize-btn"
          :disabled="!bindStatus.is_bound || store.prioritizing"
          :class="{ 'is-loading': store.prioritizing }"
          @click="handlePrioritize"
          :title="store.priorityStrategy === 'llm' ? 'AI 分析' : store.priorityStrategy === 'rule' ? '规则分析' : ''"
        >
          {{ store.prioritizing ? '分析中...' : 'AI 智能置顶' }}
        </button>
        <select
          class="view-mode-select"
          :value="currentModeKey"
          @change="switchMode($event.target.value)"
        >
          <option value="immersive">{{ MODE_NAMES.immersive }}</option>
          <option value="preview">{{ MODE_NAMES.preview }}</option>
        </select>
        <button class="mac-btn-primary" :class="{ 'is-active': isEditing }" @click="toggleEditMode">
          {{ isEditing ? '保存布局配置' : '自定义布局' }}
        </button>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="store.error" class="error-banner">
      <span>{{ store.error }}</span>
      <button class="dismiss-btn" @click="store.error = null">&times;</button>
    </div>

    <!-- Sync result -->
    <div v-if="syncResult" class="sync-result">
      同步完成：本地共 {{ syncResult.data.db_total ?? syncResult.data.total }} 封，新增 {{ syncResult.data.new_count ?? 0 }} 封
    </div>

    <!-- Grid layout -->
    <div class="grid-wrapper">
      <grid-layout
        v-model:layout="layoutConfig"
        :col-num="12"
        :row-height="50"
        :is-draggable="isEditing"
        :is-resizable="isEditing"
        :vertical-compact="false"
        :margin="[14, 14]"
        :use-css-transforms="true"
      >
        <!-- Compose panel -->
        <grid-item
          v-if="composeLayout"
          :x="composeLayout.x" :y="composeLayout.y"
          :w="composeLayout.w" :h="composeLayout.h"
          :i="composeLayout.i"
          :min-w="composeLayout.minW" :min-h="composeLayout.minH"
          class="mac-panel grid-item"
          :class="{ 'editing-mode': isEditing }"
        >
          <div class="widget-content compose-content">
            <div class="panel-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              <span class="panel-title">发送邮件</span>
            </div>
            <form class="compose-form" @submit.prevent="handleSend">
              <div class="field-row">
                <label class="field-label">收件人</label>
                <input v-model="composeForm.to" class="text-input" type="email" placeholder="recipient@sustech.edu.cn" :disabled="!bindStatus.is_bound || sending" required />
              </div>
              <div class="field-row">
                <label class="field-label">主题</label>
                <input v-model="composeForm.subject" class="text-input" type="text" placeholder="邮件主题" :disabled="!bindStatus.is_bound || sending" required />
              </div>
              <div class="field-row">
                <label class="field-label">正文</label>
                <textarea v-model="composeForm.body" class="text-input text-area" rows="6" placeholder="邮件正文内容..." :disabled="!bindStatus.is_bound || sending" required></textarea>
              </div>
              <button type="submit" class="mac-btn-primary send-btn" :disabled="!bindStatus.is_bound || sending" :class="{ 'is-loading': sending }">
                {{ sending ? '发送中...' : '发送' }}
              </button>
              <p v-if="sendSuccess" class="status-text status-success">邮件发送成功</p>
            </form>
            <div v-if="!bindStatus.is_bound" class="unbound-overlay">
              <p>请先在<a href="/user-settings" class="bind-link">用户设置</a>中绑定邮箱</p>
            </div>
          </div>
          <div v-if="isEditing" class="drag-overlay">
            <span class="overlay-text">发送邮件</span>
          </div>
        </grid-item>

        <!-- Inbox panel -->
        <grid-item
          v-if="inboxLayout"
          :x="inboxLayout.x" :y="inboxLayout.y"
          :w="inboxLayout.w" :h="inboxLayout.h"
          :i="inboxLayout.i"
          :min-w="inboxLayout.minW" :min-h="inboxLayout.minH"
          class="mac-panel grid-item"
          :class="{ 'editing-mode': isEditing }"
        >
          <div class="widget-content inbox-content">
            <div class="panel-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              <span class="panel-title">收件箱</span>
              <button
                class="view-mode-toggle"
                :class="{ 'is-preview': previewLayout }"
                @click.stop="switchMode(previewLayout ? 'immersive' : 'preview')"
                :title="previewLayout ? '切换到' + MODE_NAMES.immersive : '切换到' + MODE_NAMES.preview"
              >{{ previewLayout ? '⊞' : '⊟' }}</button>
              <select v-model="sortBy" class="sort-select" @mousedown.stop @click.stop>
                <option value="time-desc">时间 ↓</option>
                <option value="time-asc">时间 ↑</option>
                <option value="sender">发件人</option>
                <option value="title">标题</option>
              </select>
            </div>
            <div v-if="loading" class="loading-state">加载中...</div>
            <div v-else-if="messages.length === 0" class="empty-state">
              <p>暂无邮件</p>
              <p class="hint" v-if="bindStatus.is_bound">点击「同步邮件」获取最新邮件</p>
            </div>
            <div v-else class="messages-list">
              <div
                v-for="(msg, idx) in sortedMessages"
                :key="msg.id || idx"
                class="message-item"
                :class="{ 'is-prioritized': prioritizedSet.has(msg.id) || store.isStarred(msg.id), 'is-active': idx === selectedIndex }"
                @click="openEmail(idx)"
              >
                <div class="message-header">
                  <span v-if="prioritizedSet.has(msg.id)" class="priority-badge" :title="priorityReasons[msg.id]">⚙</span>
                  <button class="star-toggle" @click.stop="store.toggleStar(msg.id)" :title="store.isStarred(msg.id) ? '取消星标' : '星标'">
                    {{ store.isStarred(msg.id) ? '★' : '☆' }}
                  </button>
                  <span class="msg-title">{{ msg.title || '(无主题)' }}</span>
                  <span class="msg-sender">{{ msg.sender || '' }}</span>
                  <span class="msg-time">{{ formatTime(msg.release_time) }}</span>
                  <button class="delete-msg-btn" @click.stop="handleDelete(msg.id, idx)" title="删除">×</button>
                </div>
                <div v-if="(prioritizedSet.has(msg.id) && priorityReasons[msg.id]) || (store.isStarred(msg.id) && starReasons[msg.id])" class="priority-reason">
                  {{ priorityReasons[msg.id] || starReasons[msg.id] }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="isEditing" class="drag-overlay">
            <span class="overlay-text">收件箱</span>
          </div>
        </grid-item>

        <!-- Preview panel (小窗模式) -->
        <grid-item
          v-if="previewLayout"
          :x="previewLayout.x" :y="previewLayout.y"
          :w="previewLayout.w" :h="previewLayout.h"
          :i="previewLayout.i"
          :min-w="previewLayout.minW" :min-h="previewLayout.minH"
          class="mac-panel grid-item"
          :class="{ 'editing-mode': isEditing }"
        >
          <div class="widget-content preview-content">
            <div class="preview-nav">
              <button class="nav-btn" :disabled="selectedIndex === null || selectedIndex <= 0" @click="prevEmail">&lsaquo; 上一封</button>
              <span class="nav-counter">{{ selectedIndex !== null ? selectedIndex + 1 : 0 }} / {{ sortedMessages.length }}</span>
              <button class="nav-btn" :disabled="selectedIndex === null || selectedIndex >= sortedMessages.length - 1" @click="nextEmail">下一封 &rsaquo;</button>
              <div class="nav-actions">
                <button class="nav-btn star-btn" @click="handleStarToggle" :disabled="!selectedEmail">
                  {{ isCurrentStarred ? '★ 取消星标' : '☆ 星标' }}
                </button>
              </div>
            </div>
            <div class="preview-body" v-if="selectedEmail">
              <h2 class="preview-subject">{{ selectedEmail.title || '(无主题)' }}</h2>
              <div class="preview-meta">
                <span>发件人：{{ selectedEmail.sender || '未知' }}</span>
                <span>时间：{{ formatTime(selectedEmail.release_time) }}</span>
              </div>
              <div class="preview-html" v-html="sanitizeHtml(selectedEmail.raw_html || selectedEmail.context) || '(无正文内容)'"></div>
            </div>
            <div v-else class="preview-empty">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              <p>点击左侧邮件查看内容</p>
            </div>
          </div>
          <div v-if="isEditing" class="drag-overlay">
            <span class="overlay-text">预览</span>
          </div>
        </grid-item>
      </grid-layout>
    </div>
  </div>

  <!-- Email detail modal (shown when no preview widget in layout) -->
  <Teleport to="body">
    <div v-if="!previewLayout && selectedIndex !== null" class="email-modal-overlay" @click.self="closeModal">
      <div class="email-modal" @click.stop>
        <div class="modal-nav">
          <button class="nav-btn" :disabled="selectedIndex <= 0" @click="prevEmail">&lsaquo; 上一封</button>
          <span class="nav-counter">{{ selectedIndex + 1 }} / {{ sortedMessages.length }}</span>
          <button class="nav-btn" :disabled="selectedIndex >= sortedMessages.length - 1" @click="nextEmail">下一封 &rsaquo;</button>
          <div class="modal-actions">
            <button class="nav-btn star-btn" @click="handleStarToggle" :disabled="!selectedEmail">
              {{ isCurrentStarred ? '★ 取消星标' : '☆ 星标' }}
            </button>
            <button class="nav-btn close-btn" @click="closeModal">✕ 关闭</button>
          </div>
        </div>
        <div class="modal-body" v-if="selectedEmail">
          <h2 class="modal-subject">{{ selectedEmail.title || '(无主题)' }}</h2>
          <div class="modal-meta">
            <span>发件人：{{ selectedEmail.sender || '未知' }}</span>
            <span>时间：{{ formatTime(selectedEmail.release_time) }}</span>
          </div>
          <div class="modal-content" v-html="sanitizeHtml(selectedEmail.raw_html || selectedEmail.context) || '(无正文内容)'"></div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Trash modal -->
  <Teleport to="body">
    <div v-if="showTrash" class="email-modal-overlay" @click.self="showTrash = false">
      <div class="email-modal trash-modal" @click.stop>
        <div class="modal-nav">
          <span class="nav-counter">回收站 ({{ trashCount }})</span>
          <div class="modal-actions">
            <button class="nav-btn" @click="handleEmptyTrash" :disabled="trashCount === 0">清空</button>
            <button class="nav-btn close-btn" @click="showTrash = false">✕ 关闭</button>
          </div>
        </div>
        <div class="modal-body">
          <div v-if="trashLoading" class="loading-state">加载中...</div>
          <div v-else-if="trashCount === 0" class="empty-state">回收站为空</div>
          <div v-else class="messages-list">
            <div v-for="msg in trashMessages" :key="msg.id" class="message-item trash-item">
              <div class="message-header">
                <span class="msg-id">#{{ msg.id }}</span>
                <span class="msg-title">{{ msg.title || '(无主题)' }}</span>
                <span class="msg-sender">{{ msg.sender || '' }}</span>
                <span class="msg-time">{{ formatTime(msg.release_time) }}</span>
              </div>
              <div class="trash-item-actions">
                <button class="nav-btn" @click="handleRestore(msg.id)">恢复</button>
                <button class="nav-btn" @click="handlePermanentDelete(msg.id)" style="color:#ff3b30">彻底删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useEmailStore } from '../stores/email.js'
import VueGridLayout from 'vue3-grid-layout'

const { GridLayout, GridItem } = VueGridLayout

const EMAIL_SORT_KEY = 'proagent_email_inbox_sort'

const store = useEmailStore()

const bindStatus = computed(() => store.bindStatus)
const messages = computed(() => store.messages)
const loading = computed(() => store.loading)
const syncing = computed(() => store.syncing)
const sending = computed(() => store.sending)

const selectedIndex = ref(null)
const syncResult = ref(null)
const sendSuccess = ref(false)
const sortBy = ref(localStorage.getItem(EMAIL_SORT_KEY) || 'time-desc')
const showTrash = ref(false)

// ===== Two-Mode Layout Manager =====
const LAYOUT_KEY_IMM = 'email_layout_immersive'
const LAYOUT_KEY_PREV = 'email_layout_preview'

const MODE_NAMES = { immersive: '沉浸模式', preview: '小窗模式' }

const PRESET_IMMERSIVE = [
  { x: 0, y: 0, w: 5, h: 8, i: 'compose', minW: 4, minH: 6 },
  { x: 5, y: 0, w: 7, h: 8, i: 'inbox', minW: 5, minH: 5 },
]
const PRESET_PREVIEW = [
  { x: 0, y: 0, w: 6, h: 16, i: 'preview', minW: 4, minH: 8 },
  { x: 6, y: 0, w: 6, h: 8, i: 'compose', minW: 4, minH: 6 },
  { x: 6, y: 8, w: 6, h: 8, i: 'inbox', minW: 4, minH: 5 },
]

function loadLayout(key, preset) {
  try {
    const saved = localStorage.getItem(key)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length === preset.length) {
        return parsed.map((item, i) => ({
          ...preset[i],
          ...item,
          minW: preset[i].minW,
          minH: preset[i].minH,
        }))
      }
    }
  } catch { /* ignore */ }
  return structuredClone(preset)
}

function saveLayout(key) {
  try {
    const toSave = layoutConfig.value.map(({ x, y, w, h, i }) => ({ x, y, w, h, i }))
    localStorage.setItem(key, JSON.stringify(toSave))
  } catch { /* ignore */ }
}

const currentModeKey = ref('immersive')
const layoutConfig = ref([])
const isEditing = ref(false)

const composeLayout = computed(() => layoutConfig.value.find(item => item.i === 'compose'))
const inboxLayout = computed(() => layoutConfig.value.find(item => item.i === 'inbox'))
const previewLayout = computed(() => layoutConfig.value.find(item => item.i === 'preview'))

function switchMode(key) {
  if (key === currentModeKey.value) return
  // Save current layout
  saveLayout(currentModeKey.value === 'immersive' ? LAYOUT_KEY_IMM : LAYOUT_KEY_PREV)
  // Load target
  currentModeKey.value = key
  const targetKey = key === 'immersive' ? LAYOUT_KEY_IMM : LAYOUT_KEY_PREV
  const targetPreset = key === 'immersive' ? PRESET_IMMERSIVE : PRESET_PREVIEW
  layoutConfig.value = loadLayout(targetKey, targetPreset)
  selectedIndex.value = null
}

function toggleEditMode() {
  isEditing.value = !isEditing.value
  if (!isEditing.value) {
    saveLayout(currentModeKey.value === 'immersive' ? LAYOUT_KEY_IMM : LAYOUT_KEY_PREV)
  }
}

// Init
layoutConfig.value = loadLayout(LAYOUT_KEY_IMM, PRESET_IMMERSIVE)

// ===== Existing logic =====
watch(sortBy, (val) => { try { localStorage.setItem(EMAIL_SORT_KEY, val) } catch {} })
watch(() => store.bindStatus.is_bound, (isBound, wasBound) => {
  if (wasBound && !isBound) {
    store.stopPolling()
    store.clearAll()
    syncResult.value = null
    sendSuccess.value = false
    selectedIndex.value = null
  }
  if (!wasBound && isBound) {
    store.fetchMessages()
    store.fetchStarred()
  }
})

const trashCount = computed(() => store.trashMessages.length)
const trashMessages = computed(() => store.trashMessages)
const trashLoading = computed(() => store.trashLoading)

const selectedEmail = computed(() => {
  if (selectedIndex.value === null) return null
  return sortedMessages.value[selectedIndex.value] || null
})

const isCurrentStarred = computed(() => {
  const email = selectedEmail.value
  if (!email) return false
  return store.isStarred(email.id)
})

const prioritizedSet = computed(() => {
  const ids = new Set()
  for (const p of store.prioritizedEmails) ids.add(p.id)
  return ids
})

const priorityReasons = computed(() => {
  const map = {}
  for (const p of store.prioritizedEmails) map[p.id] = p.reason || ''
  return map
})

const starReasons = computed(() => {
  const map = {}
  for (const s of store.starredEmails) map[s.id] = s.star_reason || ''
  return map
})

const sortedMessages = computed(() => {
  const list = [...store.messages]
  const aiIds = new Set(); for (const p of store.prioritizedEmails) aiIds.add(p.id)
  const manualStarIds = new Set(); for (const s of store.starredEmails) { if (!aiIds.has(s.id)) manualStarIds.add(s.id) }

  const aiStarred = [], manualStarred = [], unstarred = []
  for (const msg of list) {
    if (aiIds.has(msg.id)) aiStarred.push(msg)
    else if (manualStarIds.has(msg.id)) manualStarred.push(msg)
    else unstarred.push(msg)
  }

  const sortFn = (a, b) => {
    switch (sortBy.value) {
      case 'time-asc': return (a.release_time || '').localeCompare(b.release_time || '')
      case 'time-desc': return (b.release_time || '').localeCompare(a.release_time || '')
      case 'sender': return (a.sender || '').localeCompare(b.sender || '')
      case 'title': return (a.title || '').localeCompare(b.title || '')
      default: return (b.release_time || '').localeCompare(a.release_time || '')
    }
  }
  aiStarred.sort(sortFn); manualStarred.sort(sortFn); unstarred.sort(sortFn)
  return [...aiStarred, ...manualStarred, ...unstarred]
})

const composeForm = reactive({ to: '', subject: '', body: '' })

function openEmail(idx) { selectedIndex.value = idx }
function closeModal() { selectedIndex.value = null }
function prevEmail() { if (selectedIndex.value > 0) selectedIndex.value-- }
function nextEmail() { if (selectedIndex.value < sortedMessages.value.length - 1) selectedIndex.value++ }
function handleStarToggle() { const email = selectedEmail.value; if (!email) return; store.toggleStar(email.id, '手动标注') }

function formatTime(time) {
  if (!time) return ''
  return String(time).slice(0, 16).replace('T', ' ')
}

function sanitizeHtml(html) {
  if (!html) return ''
  return html
    .replace(/<!--\[if[\s\S]*?<!\[endif\]-->/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<\/?o:p[^>]*>/gi, '')
    .replace(/<\/?(mso|w|st\d):[^>]*>/gi, '')
    .replace(/class="Mso[^"]*"/gi, '')
    .replace(/style="[^"]*mso-[^"]*"/gi, '')
    .replace(/\n\s*\n/g, '\n')
}

async function handleSync() {
  syncResult.value = null
  const result = await store.sync()
  store.clearPrioritized()
  if (result?.success) {
    syncResult.value = result
    setTimeout(() => { syncResult.value = null }, 5000)
  }
}

async function handleRefresh() { await store.fetchMessages(); store.clearPrioritized() }
async function handlePrioritize() { await store.prioritize(); await store.fetchStarred() }
async function openTrash() { showTrash.value = true; await store.fetchTrash() }
async function handleRestore(msgId) { await store.restoreMessage(msgId) }
async function handlePermanentDelete(msgId) { await store.permanentDelete(msgId) }

async function handleEmptyTrash() {
  if (confirm('确定清空回收站？此操作不可恢复')) await store.emptyTrash()
}

async function handleSend() {
  sendSuccess.value = false
  const result = await store.send(composeForm.subject, composeForm.body, composeForm.to)
  if (result.success) {
    composeForm.to = ''; composeForm.subject = ''; composeForm.body = ''
    sendSuccess.value = true
    setTimeout(() => { sendSuccess.value = false }, 3000)
  }
}

async function handleDelete(msgId, idx) {
  if (selectedIndex.value === idx) closeModal()
  await store.deleteMessage(msgId)
}

onMounted(async () => {
  await store.fetchStatus()
  if (store.bindStatus.is_bound) {
    store.fetchMessages()
    store.fetchStarred()
  }
})
</script>

<style scoped>
.email-engine {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.email-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 0 4px;
}

.view-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bind-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}
.bind-badge.bound { background: #e8f5e9; color: #2e7d32; }
.bind-badge.unbound { background: #fff3e0; color: #e65100; }
.bind-link { color: #007aff; text-decoration: none; font-weight: 600; margin-left: 4px; }
.bind-link:hover { text-decoration: underline; }

.mac-btn-primary {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  color: #1d1d1f;
}
.mac-btn-primary:hover { background: #f3f4f6; border-color: rgba(0,0,0,0.25); }
.mac-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.mac-btn-primary.is-loading { opacity: 0.7; }
.mac-btn-primary.is-active {
  background: #007aff;
  color: #ffffff;
  border-color: #007aff;
}

.prioritize-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border-color: #d97706 !important;
  color: #fff !important;
}
.prioritize-btn:hover {
  background: linear-gradient(135deg, #fbbf24, #f59e0b) !important;
}

.mac-btn-secondary {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  transition: all 0.2s;
}
.mac-btn-secondary:hover { background: #ffffff; border-color: rgba(0,0,0,0.2); }
.mac-btn-secondary:disabled { opacity: 0.4; cursor: not-allowed; }
.mac-btn-secondary.is-loading { opacity: 0.7; }
.trash-btn { font-size: 14px; }

.error-banner {
  display: flex; align-items: center; justify-content: space-between;
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; color: #dc2626; margin-bottom: 8px;
}
.dismiss-btn { background: none; border: none; font-size: 18px; cursor: pointer; color: #dc2626; padding: 0 4px; }

.sync-result {
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; color: #16a34a; margin-bottom: 8px;
}

/* ── Grid ── */
.grid-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  margin: -14px -14px 0;
}

/* mac-panel — same as Dashboard */
.mac-panel {
  background: var(--clr-bg-card, #ffffff);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-clip: padding-box;
}

.widget-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Panel header bar */
.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(0, 0, 0, 0.015);
}
.panel-title {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}
.sort-select {
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 5px;
  padding: 3px 6px;
  font-size: 11px;
  color: #4b5563;
  background: #fff;
  cursor: pointer;
  outline: none;
  flex-shrink: 0;
}
.sort-select:focus { border-color: #007aff; }

.view-mode-select {
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 5px;
  padding: 3px 4px;
  font-size: 11px;
  color: #007aff;
  background: rgba(0,122,255,0.03);
  cursor: pointer;
  outline: none;
  flex-shrink: 0;
  font-weight: 600;
  max-width: 100px;
}
.view-mode-select:focus { border-color: #007aff; box-shadow: 0 0 0 2px rgba(0,122,255,0.1); }

.view-mode-toggle {
  width: 26px; height: 26px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 5px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: rgba(0,0,0,0.35);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  padding: 0;
}
.view-mode-toggle:hover { background: rgba(0,0,0,0.04); color: rgba(0,0,0,0.6); }
.view-mode-toggle.is-preview { color: #007aff; border-color: rgba(0,122,255,0.3); background: rgba(0,122,255,0.04); }

/* Compose form */
.compose-content { padding: 0; }
.compose-form { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 10px 14px; overflow-y: auto; }
.field-row { display: flex; flex-direction: column; gap: 3px; }
.field-label { font-size: 11px; font-weight: 600; color: #4b5563; }
.text-input {
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 7px;
  padding: 7px 9px;
  font-size: 13px;
  color: #111827;
  background: var(--clr-bg-card, #ffffff);
  font-family: inherit;
  outline: none;
}
.text-input:focus { border-color: #007aff; box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12); }
.text-input:disabled { opacity: 0.5; }
.text-area { resize: vertical; min-height: 100px; line-height: 1.5; }
.send-btn { align-self: flex-end; margin-top: 2px; }
.status-text { margin: 2px 0 0; font-size: 12px; }
.status-success { color: #16a34a; }

.unbound-overlay {
  position: absolute; inset: 0;
  background: rgba(255,255,255,0.85);
  display: flex; align-items: center; justify-content: center;
  border-radius: 10px; font-size: 14px; color: #6b7280;
}

/* Inbox */
.inbox-content { padding: 0; }
.loading-state, .empty-state {
  flex: 1;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  color: #9ca3af; font-size: 14px; padding: 10px 14px;
}
.hint { margin-top: 4px; font-size: 12px; color: #6b7280; }

/* Preview widget */
.preview-content {
  display: flex; flex-direction: column; padding: 0;
}
.preview-nav {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  flex-shrink: 0;
}
.nav-actions { margin-left: auto; display: flex; gap: 4px; }
.preview-body {
  flex: 1; overflow-y: auto; padding: 14px 16px;
}
.preview-subject {
  margin: 0 0 10px;
  font-size: 16px; font-weight: 700;
  color: #111827; line-height: 1.4;
}
.preview-meta {
  display: flex; gap: 16px; margin-bottom: 12px; padding-bottom: 10px;
  border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 12px; color: #6b7280;
}
.preview-html {
  font-size: 13px; color: #374151; line-height: 1.65; user-select: text;
}
.preview-html :deep(img) { max-width: 100%; height: auto; }
.preview-empty {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 10px; color: rgba(0,0,0,0.2); font-size: 13px;
}

.messages-list {
  flex: 1; overflow-y: auto;
  display: flex; flex-direction: column;
  gap: 2px; padding: 8px 12px;
}
.message-item {
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
  transition: background 0.15s;
}
.message-item:hover { background: rgba(0,0,0,0.03); }
.message-item.is-active {
  border-color: #007aff;
  background: rgba(0, 122, 255, 0.04);
  box-shadow: inset 3px 0 0 #007aff;
}
.message-header { display: flex; align-items: center; gap: 8px; min-width: 0; }
.msg-id { font-size: 11px; font-weight: 500; color: #9ca3af; font-family: ui-monospace, monospace; flex-shrink: 0; }
.msg-title { flex: 1; font-size: 13px; font-weight: 600; color: #111827; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.msg-sender { font-size: 12px; color: #6b7280; flex-shrink: 0; max-width: 140px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.msg-time { font-size: 11px; color: #9ca3af; flex-shrink: 0; }

.delete-msg-btn { opacity: 0; background: none; border: none; color: #ff3b30; cursor: pointer; font-size: 15px; padding: 0 4px; flex-shrink: 0; }
.message-item:hover .delete-msg-btn { opacity: 1; }

.priority-badge { flex-shrink: 0; font-size: 14px; cursor: help; }
.priority-reason {
  margin-top: 3px; font-size: 11px; color: #b45309;
  background: #fef3c7; border-radius: 4px; padding: 2px 6px;
  line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.message-item.is-prioritized { border-color: #f59e0b; background: #fffbeb; }
.star-toggle { background: none; border: none; font-size: 16px; cursor: pointer; color: #d4a017; padding: 0 2px; flex-shrink: 0; line-height: 1; }
.star-toggle:hover { color: #b8860b; }

/* Trash */
.trash-modal { max-width: 560px; }
.trash-item { display: flex; flex-direction: column; gap: 6px; }
.trash-item-actions { display: flex; gap: 8px; justify-content: flex-end; }

/* ===== Edit mode — EXACTLY like Dashboard ===== */
.grid-item.editing-mode {
  border: 1.5px dashed #007aff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: grab;
}
.grid-item.editing-mode:active { cursor: grabbing; }

.drag-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(2px);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.overlay-text {
  font-size: 14px;
  font-weight: 600;
  color: #007aff;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* ===== Resize handle — same as Dashboard ===== */
:deep(.vue-resizable-handle) {
  width: 16px !important;
  height: 16px !important;
  background: none !important;
  border-right: 3px solid rgba(0, 0, 0, 0.15) !important;
  border-bottom: 3px solid rgba(0, 0, 0, 0.15) !important;
  border-radius: 2px !important;
  right: 6px !important;
  bottom: 6px !important;
  opacity: 0;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.grid-item.editing-mode :deep(.vue-resizable-handle) { opacity: 1; }
.grid-item.editing-mode :deep(.vue-resizable-handle:hover),
.grid-item.editing-mode :deep(.vue-resizable-handle:active) {
  border-right-color: #86868b !important;
  border-bottom-color: #86868b !important;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
  transform: scale(1.1);
  cursor: se-resize !important;
}

/* Placeholder — macOS style */
:deep(.vue-grid-item.vue-grid-placeholder) {
  background: rgba(0, 0, 0, 0.04) !important;
  border: 1.5px dashed rgba(0, 0, 0, 0.2) !important;
  border-radius: 12px !important;
  opacity: 1 !important;
  box-shadow: none !important;
}

/* ===== Modals ===== */
.email-modal-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.email-modal {
  background: #fff; border-radius: 14px;
  width: min(780px, 92vw); max-height: 85vh;
  display: flex; flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  animation: slideUp 0.2s ease;
}
@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.modal-nav {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.08); flex-shrink: 0;
}
.nav-btn {
  border: 1px solid rgba(0,0,0,0.12); background: #fff; border-radius: 6px;
  padding: 6px 14px; font-size: 13px; font-weight: 500; color: #374151;
  cursor: pointer; transition: all 0.15s;
}
.nav-btn:hover:not(:disabled) { background: #f3f4f6; border-color: rgba(0,0,0,0.2); }
.nav-btn:disabled { opacity: 0.35; cursor: default; }
.nav-counter { font-size: 12px; color: #9ca3af; margin: 0 8px; flex-shrink: 0; }
.modal-actions { margin-left: auto; display: flex; gap: 6px; }
.star-btn { color: #d4a017; border-color: rgba(212,160,23,0.2); font-size: 14px; }
.star-btn:hover:not(:disabled) { background: #fefce8; border-color: rgba(212,160,23,0.4); }
.star-btn:disabled { opacity: 0.4; cursor: default; }
.close-btn { color: #6b7280; }
.modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
.modal-subject { margin: 0 0 12px; font-size: 18px; font-weight: 700; color: #111827; line-height: 1.4; }
.modal-meta {
  display: flex; gap: 24px; margin-bottom: 16px; padding-bottom: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 13px; color: #6b7280;
}
.modal-content { font-size: 14px; color: #374151; line-height: 1.7; user-select: text; }
.modal-content :deep(img) { max-width: 100%; height: auto; }
</style>
