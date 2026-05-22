<template>
  <div class="widget-container">
    <div class="panel-header">
      <div class="source-tags">
        <button 
          v-for="src in sources" 
          :key="src.id"
          class="circle-tag" 
          :class="{ active: activeSource === src.id }"
          @click="activeSource = src.id"
        >
          {{ src.name }}
        </button>
      </div>
    </div>
    <div class="panel-body">
      <ul class="message-list">
        <!-- Email tab -->
        <template v-if="activeSource === 'email'">
          <li v-if="emailStore.messages.length === 0" class="message-item empty-hint">
            暂无置顶邮件，去「邮件管理」添加
          </li>
          <li v-for="item in emailStore.messages" :key="item.id" class="message-item"
            :class="{ 'is-pinned': isPinned(item.id), 'is-expanded': expandedEmailId === item.id }">
            <div class="msg-row" @click="toggleExpand(item.id)">
              <div class="msg-meta">
                <span class="msg-sender">{{ item.sender || '未知发件人' }}</span>
                <span class="msg-time">{{ formatEmailTime(item) }}</span>
              </div>
              <div class="msg-content">{{ item.title || '(无主题)' }}</div>
              <button v-if="isPinned(item.id)" class="unpin-btn" @click.stop="handleUnpin(item.id)" title="取消置顶">✕</button>
              <span class="expand-icon" :class="{ 'is-open': expandedEmailId === item.id }">▸</span>
            </div>
            <div v-if="expandedEmailId === item.id" class="email-detail" @click.stop>
              <div class="email-detail-body" v-html="sanitizeHtml(item.html || item.context || '')"></div>
            </div>
          </li>
        </template>
        <!-- BlackBoard tab -->
        <template v-else>
          <li v-for="item in displayItems" :key="item.id" class="message-item">
            <div class="msg-meta">
              <span class="msg-time">{{ item.time }}</span>
            </div>
            <div class="msg-content">{{ item.content }}</div>
          </li>
        </template>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from '../../stores/dashboard.js'
import { useEmailStore } from '../../stores/email.js'

const dashboardStore = useDashboardStore()
const emailStore = useEmailStore()
const pinnedItems = computed(() => dashboardStore.pinnedEmails)

const sources = [
  { id: 'email', name: 'Email' },
  { id: 'blackboard', name: 'BlackBoard' }
]

const activeSource = ref('blackboard')
const expandedEmailId = ref(null)

const staticMessages = ref([
  { id: 1001, source: 'blackboard', time: '10:30 AM', content: 'CS310: Midterm grades have been posted.', unread: true },
  { id: 1002, source: 'blackboard', time: 'Yesterday', content: 'CS305: New reading assignment available.', unread: false }
])

const displayItems = computed(() => {
  return staticMessages.value.filter(m => m.source === activeSource.value)
})

function isPinned(id) {
  return pinnedItems.value.some(p => p.id === id)
}

function toggleExpand(id) {
  expandedEmailId.value = expandedEmailId.value === id ? null : id
}

function formatEmailTime(item) {
  if (item.time) {
    const raw = String(item.time)
    return raw.slice(0, 16).replace('T', ' ')
  }
  return ''
}

function handleUnpin(id) {
  dashboardStore.unpinEmail(id)
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
</script>

<style scoped>
.widget-container { display: flex; flex-direction: column; height: 100%; }
.panel-header { display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.source-tags { display: flex; gap: 8px; }
.circle-tag { background: transparent; border: 1px solid rgba(0,0,0,0.15); border-radius: 16px; padding: 4px 12px; font-size: 11px; font-weight: 500; cursor: pointer; color: #1d1d1f; transition: all 0.2s; }
.circle-tag.active { border-color: #1d1d1f; background: #1d1d1f; color: #ffffff; }
.panel-body { flex: 1; padding: 0; overflow-y: auto; }
.message-list { list-style: none; padding: 0; margin: 0; }
.message-item { padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.04); cursor: pointer; }
.message-item:hover { background: rgba(0,0,0,0.02); }
.msg-row { display: flex; flex-direction: column; gap: 2px; position: relative; }
.msg-meta { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.msg-sender { font-size: 11px; color: #1d1d1f; font-weight: 500; }
.msg-time { font-size: 11px; color: #86868b; }
.unread-dot { width: 6px; height: 6px; background-color: #007aff; border-radius: 50%; }
.msg-content { font-size: 13px; color: #1d1d1f; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.empty-hint {
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
  padding: 20px !important;
  cursor: default !important;
  border: none !important;
}

.is-pinned {
  background: rgba(0, 122, 255, 0.03);
  border-left: 3px solid #007aff;
  padding-left: 13px !important;
}

.unpin-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 12px;
  padding: 0 4px;
  position: absolute;
  right: 24px;
  top: 0;
}

.unpin-btn:hover {
  color: #ff3b30;
}

.expand-icon {
  position: absolute;
  right: 4px;
  top: 0;
  font-size: 11px;
  color: #86868b;
  transition: transform 0.2s ease;
  user-select: none;
}

.expand-icon.is-open {
  transform: rotate(90deg);
}

.is-expanded {
  background: rgba(0, 0, 0, 0.015);
}

.email-detail {
  margin-top: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  max-height: 200px;
  overflow-y: auto;
}

.email-detail-body {
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  word-break: break-word;
}

.email-detail-body :deep(img) {
  max-width: 100%;
  height: auto;
}

.email-detail-body :deep(a) {
  color: #007aff;
  text-decoration: none;
}

.email-detail-body :deep(table) {
  max-width: 100%;
  overflow-x: auto;
  display: block;
}
</style>