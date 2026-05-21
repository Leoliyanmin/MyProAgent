import { defineStore } from 'pinia'
import { ref } from 'vue'
import { emailAPI } from '../services/api.js'

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
      if (fresh.length > 0) {
        for (const m of fresh.slice(0, 3)) {
          const id = ++_uid
          notifications.value.unshift({
            id, title: m.title || '(无主题)', sender: m.sender || '',
          })
          setTimeout(() => dismissNotification(id), 5000)
        }
      }
      _knownIds.clear()
      current.forEach(m => _knownIds.add(m.id))
      messages.value = current
    } catch { /* silent */ }
  }

  async function checkNewEmails() {
    if (!bindStatus.value.is_bound) return
    try {
      const res = await emailAPI.getMessages()
      if (!res.success || !res.messages) return
      const current = res.messages
      const fresh = current.filter(m => !_knownIds.has(m.id))
      if (fresh.length > 0) {
        for (const m of fresh.slice(0, 3)) {
          const id = ++_uid
          notifications.value.unshift({
            id, title: m.title || '(无主题)', sender: m.sender || '', release_time: m.release_time,
          })
          setTimeout(() => dismissNotification(id), 5000)
        }
      }
      _knownIds.clear()
      current.forEach(m => _knownIds.add(m.id))
      messages.value = current
    } catch { /* silent */ }
  }

  function startPolling() {
    if (_pollTimer) return
    _pollTimer = setInterval(checkNewEmails, 30000)
  }

  function stopPolling() {
    if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null }
  }

  // store 创建时自动启动
  startPolling()

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

  return {
    bindStatus, messages, loading, syncing, sending, error,
    fetchStatus, fetchMessages, sync, send, deleteMessage,
    trashMessages, trashLoading, fetchTrash, restoreMessage, permanentDelete, emptyTrash,
    notifications, checkNewEmails, dismissNotification, startPolling, stopPolling,
  }
})
