import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { emailAPI } from '../services/api.js'
import { useAuthStore } from './auth.js'

const LAST_CHECK_KEY = 'email_last_check_time'

function loadLastCheckTime() {
  try {
    return localStorage.getItem(LAST_CHECK_KEY) || ''
  } catch { return '' }
}

function saveLastCheckTime(t) {
  try { localStorage.setItem(LAST_CHECK_KEY, t) } catch { /* ignore */ }
}

export const useEmailStore = defineStore('email', () => {
  const bindStatus = ref({
    is_bound: false,
    email_address: '',
    bind_time: '',
    last_sync_time: '',
  })
  const messages = ref([])
  const loading = ref(false)
  const syncing = ref(false)
  const sending = ref(false)
  const error = ref(null)

  // ---- 通知 ----
  const notifications = ref([])
  const _knownIds = new Set()
  let _uid = 0
  let _firstRun = true
  let _pollTimer = null

  function dismissNotification(id) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  async function checkNewEmails() {
    if (!bindStatus.value.is_bound) return
    try {
      const res = await emailAPI.getMessages()
      if (!res.success || !res.messages) return
      const current = res.messages
      const fresh = current.filter(m => !_knownIds.has(m.id))
      if (!_firstRun && fresh.length > 0) {
        for (const m of fresh.slice(0, 3)) {
          const id = ++_uid
          notifications.value.unshift({
            id, title: m.title || '(无主题)', sender: m.sender || '',
          })
          setTimeout(() => dismissNotification(id), 30000)
        }
      }
      _knownIds.clear()
      current.forEach(m => _knownIds.add(m.id))
      _firstRun = false
      messages.value = current
    } catch { /* silent */ }
  }

  function startPolling() {
    if (_pollTimer) return
    fetchStatus()
    _pollTimer = setInterval(checkNewEmails, 60000)
  }

  function stopPolling() {
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null }
    _knownIds.clear()
    _firstRun = true
  }

  const auth = useAuthStore()
  watch(() => auth.token, (newToken) => {
    if (!newToken) stopPolling()
  })

  // store 创建时自动启动

  function clearAll() {
    messages.value = []
    notifications.value = []
    _knownIds.clear()
    _firstRun = true
  }

  // ---- 原有方法 ----
  async function fetchStatus() {
    try {
      const res = await emailAPI.getStatus()
      if (res.success) {
        bindStatus.value = {
          is_bound: res.is_bound || false,
          email_address: res.email_address || '',
          bind_time: res.bind_time || '',
          last_sync_time: res.last_sync_time || '',
        }
        if (bindStatus.value.is_bound) startPolling()
      }
    } catch (err) {
      error.value = err?.message || '获取邮箱状态失败'
    }
  }

  async function fetchMessages() {
    loading.value = true
    error.value = null
    try {
      const res = await emailAPI.getMessages()
      if (res.success) {
        messages.value = res.messages || []
      } else {
        error.value = res.message || '获取邮件列表失败'
      }
    } catch (err) {
      error.value = err?.message || '获取邮件列表失败'
    } finally {
      loading.value = false
    }
  }

  async function sync(maxMessages) {
    syncing.value = true
    error.value = null
    try {
      const res = await emailAPI.sync(maxMessages)
      if (res.success) {
        await fetchMessages()
        await fetchStatus()
        return res
      } else {
        error.value = res.message || '同步失败'
      }
    } catch (err) {
      error.value = err?.message || '同步失败'
    } finally {
      syncing.value = false
    }
  }

  async function send(title, context, receiver) {
    sending.value = true
    error.value = null
    try {
      const res = await emailAPI.send(title, context, receiver)
      if (res.success) {
        return { success: true }
      } else {
        error.value = res.message || '发送失败'
        return { success: false, message: error.value }
      }
    } catch (err) {
      error.value = err?.message || '发送失败'
      return { success: false, message: error.value }
    } finally {
      sending.value = false
    }
  }

  async function deleteMessage(messageId) {
    try {
      const res = await emailAPI.deleteMessage(messageId)
      if (res.success) {
        messages.value = messages.value.filter(m => m.id !== messageId)
      } else {
        error.value = res.message || '删除失败'
      }
    } catch (err) {
      error.value = err?.message || '删除失败'
    }
  }

  // ---- 回收站 ----
  const trashMessages = ref([])
  const trashLoading = ref(false)

  async function fetchTrash() {
    trashLoading.value = true
    try {
      const res = await emailAPI.getTrash()
      if (res.success) {
        trashMessages.value = res.messages || []
      }
    } catch (err) {
      error.value = err?.message || '获取回收站失败'
    } finally {
      trashLoading.value = false
    }
  }

  async function restoreMessage(messageId) {
    try {
      const res = await emailAPI.restoreMessage(messageId)
      if (res.success) {
        trashMessages.value = trashMessages.value.filter(m => m.id !== messageId)
        await fetchMessages()
      }
    } catch (err) {
      error.value = err?.message || '恢复失败'
    }
  }

  async function permanentDelete(messageId) {
    try {
      const res = await emailAPI.permanentDelete(messageId)
      if (res.success) {
        trashMessages.value = trashMessages.value.filter(m => m.id !== messageId)
      }
    } catch (err) {
      error.value = err?.message || '彻底删除失败'
    }
  }

  async function emptyTrash() {
    try {
      const res = await emailAPI.emptyTrash()
      if (res.success) {
        trashMessages.value = []
      }
    } catch (err) {
      error.value = err?.message || '清空失败'
    }
  }

  const prioritizedEmails = ref([])
  const prioritizing = ref(false)
  const priorityStrategy = ref('')

  async function prioritize() {
    prioritizing.value = true
    try {
      const res = await emailAPI.prioritize()
      if (res.success) {
        prioritizedEmails.value = res.prioritized || []
        priorityStrategy.value = res.strategy_used || ''
      }
    } catch (err) {
      error.value = err?.message || '分析失败'
    } finally {
      prioritizing.value = false
    }
  }

  function clearPrioritized() {
    prioritizedEmails.value = []
    priorityStrategy.value = ''
  }

  // ---- Starred Emails ----
  const starredEmails = ref([])
  const starredLoading = ref(false)

  async function fetchStarred() {
    starredLoading.value = true
    try {
      const res = await emailAPI.starred.list()
      if (res.success) {
        starredEmails.value = res.messages || []
      }
    } catch (err) {
      error.value = err?.message || '获取星标邮件失败'
    } finally {
      starredLoading.value = false
    }
  }

  async function toggleStar(emailId, reason) {
    try {
      const idx = starredEmails.value.findIndex(e => e.id === emailId)
      if (idx !== -1) {
        starredEmails.value.splice(idx, 1)
        await emailAPI.starred.unstar(emailId)
        const pi = prioritizedEmails.value.findIndex(p => p.id === emailId)
        if (pi !== -1) {
          prioritizedEmails.value.splice(pi, 1)
        }
      } else {
        const res = await emailAPI.starred.star(emailId, reason || '手动标注')
        if (res.success) {
          await fetchStarred()
        }
      }
    } catch (err) {
      error.value = err?.message || '星标操作失败'
      await fetchStarred()
    }
  }

  function isStarred(emailId) {
    return starredEmails.value.some(e => e.id === emailId || e.id === Number(emailId))
  }

  return {
    bindStatus, messages, loading, syncing, sending, error,
    fetchStatus, fetchMessages, sync, send, deleteMessage,
    trashMessages, trashLoading, fetchTrash, restoreMessage, permanentDelete, emptyTrash,
    notifications, checkNewEmails, dismissNotification, startPolling, stopPolling, clearAll,
    prioritizedEmails, prioritizing, priorityStrategy, prioritize, clearPrioritized,
    starredEmails, starredLoading, fetchStarred, toggleStar, isStarred,
  }
})
