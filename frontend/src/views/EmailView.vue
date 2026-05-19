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
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="store.error" class="error-banner">
      <span>{{ store.error }}</span>
      <button class="dismiss-btn" @click="store.error = null">&times;</button>
    </div>

    <!-- Sync result -->
    <div v-if="syncResult" class="sync-result">
      同步完成：共 {{ syncResult.data.total }} 封邮件，新增 {{ syncResult.data.synced }} 封
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
        <h3 class="panel-title">收件箱</h3>
        <div v-if="loading" class="loading-state">加载中...</div>
        <div v-else-if="messages.length === 0" class="empty-state">
          <p>暂无邮件</p>
          <p class="hint" v-if="bindStatus.is_bound">点击「同步邮件」获取最新邮件</p>
        </div>
        <div v-else class="messages-list">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-item"
            :class="{ expanded: expandedIndex === idx }"
            @click="toggleExpand(idx)"
          >
            <div class="message-header">
              <span class="msg-title">{{ msg.title || '(无主题)' }}</span>
              <span class="msg-sender">{{ msg.sender || '' }}</span>
              <span class="msg-time">{{ formatTime(msg.release_time) }}</span>
              <button class="delete-msg-btn" @click.stop="handleDelete(msg.id, idx)" title="删除">×</button>
            </div>
            <div v-if="expandedIndex === idx" class="message-body">
              <div class="body-content" v-html="sanitizeHtml(msg.raw_html || msg.context) || '(无正文内容)'"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useEmailStore } from '../stores/email.js'

const store = useEmailStore()

const bindStatus = computed(() => store.bindStatus)
const messages = computed(() => store.messages)
const loading = computed(() => store.loading)
const syncing = computed(() => store.syncing)
const sending = computed(() => store.sending)

const expandedIndex = ref(null)
const syncResult = ref(null)
const sendSuccess = ref(false)

const composeForm = reactive({
  to: '',
  subject: '',
  body: '',
})

function toggleExpand(idx) {
  expandedIndex.value = expandedIndex.value === idx ? null : idx
}

function formatTime(time) {
  if (!time) return ''
  const raw = String(time)
  return raw.slice(0, 16).replace('T', ' ')
}

function sanitizeHtml(html) {
  if (!html) return ''
  // Strip <style> tags and their content to prevent global CSS leaks
  return html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
}

async function handleSync() {
  syncResult.value = null
  const result = await store.sync(50)
  if (result?.success) {
    syncResult.value = result
    setTimeout(() => { syncResult.value = null }, 5000)
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
  if (!confirm('确认删除该邮件？')) return
  expandedIndex.value = null
  await store.deleteMessage(msgId)
}

onMounted(() => {
  store.fetchStatus()
  if (store.bindStatus.is_bound) {
    store.fetchMessages()
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
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
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

.message-item.expanded {
  background: rgba(0, 122, 255, 0.04);
  border-color: rgba(0, 122, 255, 0.15);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
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

.message-body {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.body-content {
  font-size: 13px;
  color: #374151;
  line-height: 1.6;
  word-break: break-word;
}
</style>
