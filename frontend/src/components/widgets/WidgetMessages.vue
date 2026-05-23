<template>
  <div class="widget-container">
    <!-- Menu Bar: sort dropdown + count -->
    <div class="menu-bar">
      <span class="star-count">星标邮件 ({{ starredEmails.length }})</span>
      <select v-model="sortBy" class="sort-select">
        <option value="time-desc">时间 ↓</option>
        <option value="time-asc">时间 ↑</option>
        <option value="sender">发件人</option>
        <option value="title">标题</option>
      </select>
    </div>

    <div class="panel-body">
      <ul class="message-list">
        <li v-if="sortedStarred.length === 0" class="message-item empty-hint">
          暂无星标邮件，去「邮件管理」星标重要邮件
        </li>
        <li v-for="item in sortedStarred" :key="item.id" class="message-item"
          :class="{ 'is-expanded': expandedEmailId === item.id }">
          <div class="msg-row" @click="toggleExpand(item.id)">
            <div class="msg-meta">
              <span class="source-badge" :title="item.star_source === 'ai' ? 'AI 置顶' : '手动星标'">
                {{ item.star_source === 'ai' ? '⚙' : '☺' }}
              </span>
              <span class="msg-sender">{{ item.sender || '未知发件人' }}</span>
              <button class="star-toggle" @click.stop="emailStore.toggleStar(item.id)" :title="'取消星标'">★</button>
              <span class="msg-time">{{ formatEmailTime(item) }}</span>
            </div>
            <div class="msg-content">{{ item.title || '(无主题)' }}</div>
            <span class="expand-icon" :class="{ 'is-open': expandedEmailId === item.id }">▸</span>
          </div>
          <div v-if="item.star_reason" class="priority-reason">{{ item.star_reason }}</div>
          <div v-if="expandedEmailId === item.id" class="email-detail" @click.stop>
            <div class="email-detail-body" v-html="sanitizeHtml(item.raw_html || item.context || '')"></div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useEmailStore } from '../../stores/email.js'

const SORT_STORAGE_KEY = 'proagent_starred_sort'

const emailStore = useEmailStore()
const starredEmails = computed(() => emailStore.starredEmails)

const expandedEmailId = ref(null)

function loadSortPreference() {
  try {
    return localStorage.getItem(SORT_STORAGE_KEY) || 'time-desc'
  } catch { return 'time-desc' }
}

const sortBy = ref(loadSortPreference())

watch(sortBy, (val) => {
  try { localStorage.setItem(SORT_STORAGE_KEY, val) } catch {}
})

onMounted(() => {
  emailStore.fetchStarred()
})

const sortedStarred = computed(() => {
  const list = [...starredEmails.value]
  const aiItems = list.filter(m => m.star_source === 'ai')
  const manualItems = list.filter(m => m.star_source !== 'ai')

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

  aiItems.sort(sortFn)
  manualItems.sort(sortFn)

  return [...aiItems, ...manualItems]
})

function toggleExpand(id) {
  expandedEmailId.value = expandedEmailId.value === id ? null : id
}

function formatEmailTime(item) {
  if (item.release_time) {
    const raw = String(item.release_time)
    return raw.slice(0, 16).replace('T', ' ')
  }
  return ''
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

.menu-bar { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; border-bottom: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; }
.star-count { font-size: 12px; font-weight: 600; color: #1d1d1f; }
.sort-select { border: 1px solid rgba(0,0,0,0.12); border-radius: 6px; padding: 3px 8px; font-size: 11px; color: #4b5563; background: #fff; cursor: pointer; outline: none; }
.sort-select:focus { border-color: #007aff; }

.panel-body { flex: 1; padding: 0; overflow-y: auto; }
.message-list { list-style: none; padding: 0; margin: 0; }
.message-item { padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.04); cursor: pointer; }
.message-item:hover { background: rgba(0,0,0,0.02); }
.msg-row { display: flex; flex-direction: column; gap: 2px; position: relative; }
.msg-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.source-badge { flex-shrink: 0; font-size: 16px; opacity: 0.7; }
.msg-sender { font-size: 11px; color: #1d1d1f; font-weight: 500; flex: 1; }
.msg-time { font-size: 11px; color: #86868b; flex-shrink: 0; }
.msg-content { font-size: 13px; color: #1d1d1f; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.star-toggle { background: none; border: none; font-size: 14px; cursor: pointer; color: #f59e0b; padding: 0 2px; flex-shrink: 0; line-height: 1; }
.star-toggle:hover { color: #d97706; }

.empty-hint { text-align: center; color: #9ca3af; font-size: 12px; padding: 20px !important; cursor: default !important; border: none !important; }

.priority-reason { margin-top: 4px; font-size: 11px; color: #b45309; background: #fef3c7; border-radius: 4px; padding: 2px 8px; line-height: 1.4; }

.expand-icon { position: absolute; right: 4px; top: 0; font-size: 11px; color: #86868b; transition: transform 0.2s ease; user-select: none; }
.expand-icon.is-open { transform: rotate(90deg); }
.is-expanded { background: rgba(0, 0, 0, 0.015); }

.email-detail { margin-top: 8px; padding: 10px 12px; background: rgba(0, 0, 0, 0.02); border-radius: 6px; border: 1px solid rgba(0, 0, 0, 0.06); max-height: 200px; overflow-y: auto; }
.email-detail-body { font-size: 12px; line-height: 1.5; color: #333; word-break: break-word; }
.email-detail-body :deep(img) { max-width: 100%; height: auto; }
.email-detail-body :deep(a) { color: #007aff; text-decoration: none; }
.email-detail-body :deep(table) { max-width: 100%; overflow-x: auto; display: block; }
</style>
