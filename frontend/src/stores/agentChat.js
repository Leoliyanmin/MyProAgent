import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'proagent_chat_history'
const TEMP_TTL_MS = 7 * 24 * 60 * 60 * 1000

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2)
}

function normalizeMessage(message) {
  if (!message || typeof message !== 'object') return null
  const role = typeof message.role === 'string' ? message.role : 'assistant'
  const rawText = message.text ?? message.content ?? ''
  const text = typeof rawText === 'string'
    ? rawText
    : (() => {
        try { return JSON.stringify(rawText) } catch { return '' }
      })()

  return {
    ...message,
    role,
    text,
    done: message.done !== false
  }
}

function normalizeMessages(value) {
  if (!Array.isArray(value)) return []
  return value.map(normalizeMessage).filter(Boolean)
}

export const useAgentChatStore = defineStore('agentChat', () => {
  const messages = ref([])
  const chatList = ref([])
  const currentChatId = ref('')
  const activeModels = ref([])
  const currentProvider = ref('')
  const currentModel = ref('')
  const noKeyModalVisible = ref(false)
  let _initialized = false

  function getStorageKey(chatId) {
    return `${STORAGE_KEY}_messages_${chatId}`
  }

  function loadChatList() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = stored ? JSON.parse(stored) : []
      chatList.value = Array.isArray(parsed)
        ? parsed.map(c => ({ ...c, isTemporary: !!c.isTemporary }))
        : []
    } catch {
      chatList.value = []
    }
    cleanupExpiredTempChats()
  }

  function saveChatList() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(chatList.value)) } catch {}
  }

  function saveChatMessages(chatId, messagesArray) {
    if (!chatId) return
    const normalized = normalizeMessages(messagesArray)
    try {
      localStorage.setItem(getStorageKey(chatId), JSON.stringify(normalized))
      const chat = chatList.value.find(c => c.id === chatId)
      if (chat) {
        chat.updatedAt = Date.now()
        saveChatList()
      }
    } catch {}
  }

  function loadChatMessagesFromStorage(chatId) {
    if (!chatId) return []
    try {
      const stored = localStorage.getItem(getStorageKey(chatId))
      return stored ? normalizeMessages(JSON.parse(stored)) : []
    } catch {
      return []
    }
  }

  function saveCurrentChat() {
    if (!currentChatId.value) return
    saveChatMessages(currentChatId.value, messages.value)
  }

  function loadChatMessages(chatId) {
    messages.value = loadChatMessagesFromStorage(chatId)
  }

  function createNewChat(openTemporary = false) {
    if (currentChatId.value) saveCurrentChat()
    const chat = {
      id: generateId(),
      title: `新对话 ${chatList.value.length + 1}`,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      ...(openTemporary ? { isTemporary: true } : {})
    }
    chatList.value.unshift(chat)
    currentChatId.value = chat.id
    messages.value = []
    saveChatList()
    return chat
  }

  function switchChat(chatId) {
    if (!chatId || chatId === currentChatId.value) return
    saveCurrentChat()
    currentChatId.value = chatId
    loadChatMessages(chatId)
  }

  function deleteChat(chatId) {
    const idx = chatList.value.findIndex(c => c.id === chatId)
    if (idx === -1) return
    localStorage.removeItem(getStorageKey(chatId))
    chatList.value.splice(idx, 1)
    saveChatList()
    if (currentChatId.value === chatId) {
      if (chatList.value.length > 0) switchChat(chatList.value[0].id)
      else createNewChat()
    }
  }

  function addMessage(msg) {
    const normalized = normalizeMessage(msg)
    if (normalized) messages.value.push(normalized)
  }

  function setMessages(arr) {
    messages.value = normalizeMessages(arr)
  }

  function appendToLastAssistant(content) {
    const text = typeof content === 'string' ? content : String(content ?? '')
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant' && !last.done) {
      last.text += text
    } else {
      messages.value.push({ role: 'assistant', text, done: false })
    }
  }

  function markLastDone() {
    const last = messages.value[messages.value.length - 1]
    if (last) last.done = true
  }

  function markChatTemporary(chatId) {
    const chat = chatList.value.find(c => c.id === chatId)
    if (chat) {
      chat.isTemporary = true
      saveChatList()
    }
  }

  function markChatPermanent(chatId) {
    const chat = chatList.value.find(c => c.id === chatId)
    if (chat) {
      chat.isTemporary = false
      saveChatList()
    }
  }

  function isChatTemporary(chatId) {
    const chat = chatList.value.find(c => c.id === chatId)
    return !!chat?.isTemporary
  }

  function cleanupExpiredTempChats() {
    const now = Date.now()
    const expired = chatList.value.filter(c => c.isTemporary && now - c.updatedAt > TEMP_TTL_MS)
    if (expired.length === 0) return
    for (const chat of expired) localStorage.removeItem(getStorageKey(chat.id))
    chatList.value = chatList.value.filter(c => !expired.some(exp => exp.id === c.id))
    saveChatList()
  }

  function formatTime(timestamp) {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const diff = Date.now() - date.getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
    return date.toLocaleDateString('zh-CN')
  }

  function setActiveModels(models) {
    activeModels.value = Array.isArray(models) ? models : []
  }

  function setCurrentModel(provider = '', model = '') {
    currentProvider.value = provider || ''
    currentModel.value = model || ''
  }

  function showNoKeyModal() {
    noKeyModalVisible.value = true
  }

  function dismissNoKeyModal() {
    noKeyModalVisible.value = false
  }

  function init() {
    if (_initialized) return
    _initialized = true
    loadChatList()
    if (chatList.value.length > 0) {
      currentChatId.value = chatList.value[0].id
      loadChatMessages(currentChatId.value)
    } else {
      createNewChat()
    }
  }

  return {
    messages,
    chatList,
    currentChatId,
    activeModels,
    currentProvider,
    currentModel,
    noKeyModalVisible,
    loadChatList,
    saveChatList,
    saveCurrentChat,
    loadChatMessages,
    loadChatMessagesFromStorage,
    saveChatMessages,
    createNewChat,
    switchChat,
    deleteChat,
    addMessage,
    setMessages,
    appendToLastAssistant,
    markLastDone,
    markChatTemporary,
    markChatPermanent,
    isChatTemporary,
    cleanupExpiredTempChats,
    formatTime,
    getStorageKey,
    setActiveModels,
    setCurrentModel,
    showNoKeyModal,
    dismissNoKeyModal,
    init
  }
})
