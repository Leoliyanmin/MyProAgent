import { defineStore } from 'pinia'
import { ref } from 'vue'

const STORAGE_KEY = 'proagent_chat_history'

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

export const useAgentChatStore = defineStore('agentChat', () => {
  const messages = ref([])
  const chatList = ref([])
  const currentChatId = ref('')
  const isSending = ref(false)
  const isThinking = ref(false)

  function loadChatList() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) chatList.value = JSON.parse(stored)
    } catch { chatList.value = [] }
  }

  function saveChatList() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(chatList.value)) } catch {}
  }

  function getStorageKey(chatId) { return `${STORAGE_KEY}_messages_${chatId}` }

  function saveCurrentChat() {
    if (!currentChatId.value || messages.value.length === 0) return
    try {
      localStorage.setItem(getStorageKey(currentChatId.value), JSON.stringify(messages.value))
      const chat = chatList.value.find(c => c.id === currentChatId.value)
      if (chat) { chat.updatedAt = Date.now(); saveChatList() }
    } catch {}
  }

  function loadChatMessages(chatId) {
    try {
      const stored = localStorage.getItem(getStorageKey(chatId))
      messages.value = stored ? JSON.parse(stored) : []
    } catch { messages.value = [] }
  }

  function createNewChat() {
    if (currentChatId.value) saveCurrentChat()
    const chat = { id: generateId(), title: '新对话 ' + (chatList.value.length + 1), createdAt: Date.now(), updatedAt: Date.now() }
    chatList.value.unshift(chat)
    saveChatList()
    currentChatId.value = chat.id
    messages.value = []
  }

  function switchChat(chatId) {
    if (chatId === currentChatId.value) return
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
    messages.value.push(msg)
  }

  function setMessages(arr) {
    messages.value = arr
  }

  function appendToLastAssistant(content) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant' && !last.done) {
      last.text += content
    } else {
      messages.value.push({ role: 'assistant', text: content, done: false })
    }
  }

  function markLastDone() {
    const last = messages.value[messages.value.length - 1]
    if (last) last.done = true
  }

  function init() {
    loadChatList()
    if (chatList.value.length > 0) {
      currentChatId.value = chatList.value[0].id
      loadChatMessages(currentChatId.value)
    } else {
      createNewChat()
    }
  }

  return {
    messages, chatList, currentChatId, isSending, isThinking,
    loadChatList, saveChatList, saveCurrentChat, loadChatMessages,
    createNewChat, switchChat, deleteChat,
    addMessage, setMessages, appendToLastAssistant, markLastDone, init,
  }
})
