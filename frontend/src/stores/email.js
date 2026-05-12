import { defineStore } from 'pinia'
import { ref } from 'vue'
import { emailAPI } from '../services/api.js'

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

  async function sync(maxMessages = 50) {
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

  return {
    bindStatus,
    messages,
    loading,
    syncing,
    sending,
    error,
    fetchStatus,
    fetchMessages,
    sync,
    send,
  }
})
