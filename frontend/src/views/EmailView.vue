<template>
  <div class="email-wrapper">
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

    <!-- Main content: two columns -->
    <div class="email-main">
      <!-- Left column: Send email form -->
      <div class="email-compose-panel mac-panel">
        <h3 class="panel-title">发送邮件</h3>
        <form class="compose-form" @submit.prevent="handleSend">
          <div class="field-row">
            <label class="field-label">收件人</label>
            <input
              v-model="composeForm.to"
              class="text-input"
              type="email"
              placeholder="recipient@sustech.edu.cn"
              :disabled="!bindStatus.is_bound || sending"
              required
            />
          </div>
          <div class="field-row">
            <label class="field-label">主题</label>
            <input
              v-model="composeForm.subject"
              class="text-input"
              type="text"
              placeholder="邮件主题"
              :disabled="!bindStatus.is_bound || sending"
              required
            />
          </div>
          <div class="field-row">
            <label class="field-label">正文</label>
            <textarea
              v-model="composeForm.body"
              class="text-input text-area"
              rows="8"
              placeholder="邮件正文内容..."
              :disabled="!bindStatus.is_bound || sending"
              required
            ></textarea>
          </div>
          <button
            type="submit"
            class="mac-btn-primary send-btn"
            :disabled="!bindStatus.is_bound || sending"
            :class="{ 'is-loading': sending }"
          >
            {{ sending ? '发送中...' : '发送' }}
          </button>
          <p v-if="sendSuccess" class="status-text status-success">邮件发送成功</p>
        </form>
        <div v-if="!bindStatus.is_bound" class="unbound-overlay">
          <p>请先在<a href="/user-settings" class="bind-link">用户设置</a>中绑定邮箱</p>
        </div>
      </div>

      <!-- Right column: Messages list -->
      <div class="email-messages-panel mac-panel">
        <div class="panel-header-row">
          <h3 class="panel-title">收件箱</h3>
          <select v-model="sortBy" class="sort-select">
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
            :class="{ 'is-prioritized': prioritizedSet.has(msg.id) || store.isStarred(msg.id) }"
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
    </div>
  </div>

  <!-- Email detail modal -->
  <Teleport to="body">
    <div v-if="selectedIndex !== null" class="email-modal-overlay" @click.self="closeModal">
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
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useEmailStore } from '../stores/email.js'

const store = useEmailStore()

const bindStatus = computed(() => store.bindStatus)
const messages = computed(() => store.messages)
const loading = computed(() => store.loading)
const syncing = computed(() => store.syncing)
const sending = computed(() => store.sending)

const selectedIndex = ref(null)
const syncResult = ref(null)
const sendSuccess = ref(false)
const sortBy = ref('time-desc')
const showTrash = ref(false)

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
  for (const p of store.prioritizedEmails) {
    ids.add(p.id)
  }
  return ids
})

const priorityReasons = computed(() => {
  const map = {}
  for (const p of store.prioritizedEmails) {
    map[p.id] = p.reason || ''
  }
  return map
})

const starReasons = computed(() => {
  const map = {}
  for (const s of store.starredEmails) {
    map[s.id] = s.star_reason || ''
  }
  return map
})

const sortedMessages = computed(() => {
  const list = [...store.messages]

  const aiIds = new Set()
  for (const p of store.prioritizedEmails) {
    aiIds.add(p.id)
  }

  const manualStarIds = new Set()
  for (const s of store.starredEmails) {
    if (!aiIds.has(s.id)) {
      manualStarIds.add(s.id)
    }
  }

  const aiStarred = []
  const manualStarred = []
  const unstarred = []

  for (const msg of list) {
    if (aiIds.has(msg.id)) {
      aiStarred.push(msg)
    } else if (manualStarIds.has(msg.id)) {
      manualStarred.push(msg)
    } else {
      unstarred.push(msg)
    }
  }

  const sortFn = (a, b) => {
    switch (sortBy.value) {
      case 'time-asc':
        return (a.release_time || '').localeCompare(b.release_time || '')
      case 'time-desc':
        return (b.release_time || '').localeCompare(a.release_time || '')
      case 'sender':
        return (a.sender || '').localeCompare(b.sender || '')
      case 'title':
        return (a.title || '').localeCompare(b.title || '')
      default:
        return (b.release_time || '').localeCompare(a.release_time || '')
    }
  }

  aiStarred.sort(sortFn)
  manualStarred.sort(sortFn)
  unstarred.sort(sortFn)

  return [...aiStarred, ...manualStarred, ...unstarred]
})

const composeForm = reactive({
  to: '',
  subject: '',
  body: '',
})

function openEmail(idx) {
  selectedIndex.value = idx
}

function closeModal() {
  selectedIndex.value = null
}

function prevEmail() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--
  }
}

function nextEmail() {
  if (selectedIndex.value < sortedMessages.value.length - 1) {
    selectedIndex.value++
  }
}

function handleStarToggle() {
  const email = selectedEmail.value
  if (!email) return
  store.toggleStar(email.id, '手动标注')
}

function formatTime(time) {
  if (!time) return ''
  const raw = String(time)
  return raw.slice(0, 16).replace('T', ' ')
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

async function handleRefresh() {
  await store.fetchMessages()
  store.clearPrioritized()
}

async function handlePrioritize() {
  await store.prioritize()
  await store.fetchStarred()
}

async function openTrash() {
  showTrash.value = true
  await store.fetchTrash()
}

async function handleRestore(msgId) {
  await store.restoreMessage(msgId)
}

async function handlePermanentDelete(msgId) {
  await store.permanentDelete(msgId)
}

async function handleEmptyTrash() {
  if (confirm('确定清空回收站？此操作不可恢复')) {
    await store.emptyTrash()
  }
}

async function handleSend() {
  sendSuccess.value = false
  const result = await store.send(composeForm.subject, composeForm.body, composeForm.to)
  if (result.success) {
    composeForm.to = ''
    composeForm.subject = ''
    composeForm.body = ''
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
.email-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.email-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.view-title {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1d1d1f;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bind-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.bind-badge.bound {
  background: #e8f5e9;
  color: #2e7d32;
}

.bind-badge.unbound {
  background: #fff3e0;
  color: #e65100;
}

.bind-link {
  color: #007aff;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
}

.bind-link:hover {
  text-decoration: underline;
}

.mac-btn-primary {
  border: none;
  background: #007aff;
  color: #fff;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.mac-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mac-btn-primary.is-loading {
  opacity: 0.7;
}

.mac-btn-secondary {
  border: 1px solid rgba(0,0,0,0.15);
  background: #fff;
  color: #1d1d1f;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}
.mac-btn-secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.mac-btn-secondary.is-loading {
  opacity: 0.7;
}

.trash-btn {
  font-size: 14px;
}

/* Trash modal */
.trash-modal {
  max-width: 560px;
}

.trash-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trash-item-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: #dc2626;
}

.dismiss-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #dc2626;
  padding: 0 4px;
}

.sync-result {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: #16a34a;
}

.email-main {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 14px;
  min-height: 0;
}

.mac-panel {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  background: var(--clr-bg-card, #ffffff);
  padding: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.panel-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.sort-select {
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #4b5563;
  background: #fff;
  cursor: pointer;
  outline: none;
}
.sort-select:focus {
  border-color: #007aff;
}

/* Compose panel */
.email-compose-panel {
  position: relative;
}

.compose-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 12px;
  font-weight: 600;
  color: #4b5563;
}

.text-input {
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  color: #111827;
  background: var(--clr-bg-card, #ffffff);
  font-family: inherit;
}

.text-input:focus {
  outline: none;
  border-color: #007aff;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.text-input:disabled {
  opacity: 0.5;
}

.text-area {
  resize: vertical;
  min-height: 120px;
  line-height: 1.5;
}

.send-btn {
  align-self: flex-end;
  margin-top: 4px;
}

.status-text {
  margin: 4px 0 0;
  font-size: 12px;
}

.status-success {
  color: #16a34a;
}

.unbound-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 14px;
  color: #6b7280;
}

/* Messages panel */
.email-messages-panel {
  overflow: hidden;
}

.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 14px;
}

.hint {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.message-item {
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.message-item:hover {
  background: rgba(0, 0, 0, 0.03);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.msg-id {
  font-size: 11px;
  font-weight: 500;
  color: #9ca3af;
  font-family: ui-monospace, monospace;
  flex-shrink: 0;
}

.msg-title {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.msg-sender {
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.msg-time {
  font-size: 11px;
  color: #9ca3af;
  flex-shrink: 0;
}

.delete-msg-btn {
  opacity: 0;
  background: none;
  border: none;
  color: #ff3b30;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0 6px;
  flex-shrink: 0;
}
.message-item:hover .delete-msg-btn {
  opacity: 1;
}

.priority-badge {
  flex-shrink: 0;
  font-size: 14px;
  cursor: help;
}

.priority-reason {
  margin-top: 4px;
  font-size: 11px;
  color: #b45309;
  background: #fef3c7;
  border-radius: 4px;
  padding: 2px 8px;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message-item.is-prioritized {
  border-color: #f59e0b;
  background: #fffbeb;
}

.prioritize-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706) !important;
  border-color: #d97706 !important;
}
.prioritize-btn:hover {
  background: linear-gradient(135deg, #fbbf24, #f59e0b) !important;
}

/* ========== Email Detail Modal ========== */
.email-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.email-modal {
  background: #fff;
  border-radius: 14px;
  width: min(780px, 92vw);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
  animation: slideUp 0.2s ease;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.modal-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  flex-shrink: 0;
}

.nav-btn {
  border: 1px solid rgba(0,0,0,0.12);
  background: #fff;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
}

.nav-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: rgba(0,0,0,0.2);
}

.nav-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.nav-counter {
  font-size: 12px;
  color: #9ca3af;
  margin: 0 8px;
  flex-shrink: 0;
}

.modal-actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.pin-btn {
  color: #007aff;
  border-color: rgba(0,122,255,0.2);
}

.pin-btn:disabled {
  color: #34c759;
  border-color: rgba(52,199,89,0.2);
  background: #f0fdf4;
}

.star-toggle { background: none; border: none; font-size: 18px; cursor: pointer; color: #d4a017; padding: 0 2px; flex-shrink: 0; line-height: 1; }
.star-toggle:hover { color: #b8860b; }

.star-btn { color: #d4a017; border-color: rgba(212,160,23,0.2); font-size: 14px; }
.star-btn:hover:not(:disabled) { background: #fefce8; border-color: rgba(212,160,23,0.4); }
.star-btn:disabled { opacity: 0.4; cursor: default; }

.close-btn {
  color: #6b7280;
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.modal-subject {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  line-height: 1.4;
}

.modal-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  font-size: 13px;
  color: #6b7280;
}

.modal-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.7;
  user-select: text;
}

.modal-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>
