<template>
  <aside 
    class="macos-sidebar right-sidebar agent-panel" 
    :class="{ 'is-collapsed': !isOpen }"
  >
    <div class="agent-header">
      <span class="font-semibold">Agent 助手</span>
      <button class="icon-btn close-agent-btn" @click="emit('toggleFromSelf')" title="收起 Agent 助手">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- 聊天记录列表 -->
    <div class="chat-list-section">
      <div class="chat-list-header">
        <span class="chat-list-title">聊天记录</span>
        <button class="new-chat-btn" @click="createNewChat" type="button" title="新建对话">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
          新对话
        </button>
      </div>
      <div class="chat-list">
        <div 
          v-for="chat in chatList" 
          :key="chat.id"
          class="chat-item"
          :class="{ active: currentChatId === chat.id }"
          @click="switchChat(chat.id)"
        >
          <svg class="chat-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <div class="chat-info">
            <div class="chat-title">{{ chat.title }}</div>
            <div class="chat-time">{{ formatTime(chat.updatedAt) }}</div>
          </div>
          <button class="delete-chat-btn" @click.stop="deleteChat(chat.id)" title="删除">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div v-if="chatList.length === 0" class="chat-empty">
          暂无聊天记录，点击"新对话"开始
        </div>
      </div>
    </div>

    <!-- 对话框区域 -->
    <div class="dialog-section">
      <div class="messages-list" ref="messagesContainer">
        <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
          <template v-for="(segment, si) in parseMessage(msg.text)" :key="si">
            <div v-if="segment.type === 'text'" class="message-content markdown-body" v-html="renderMarkdown(segment.content)"></div>
            <ThemeSuggestionWidget
              v-else-if="segment.type === 'theme-suggestion'"
              :tokens="segment.tokens"
              @accept="applyThemeSuggestion(segment.tokens)"
            />
          </template>
        </div>
        <div v-if="messages.length === 0" class="placeholder-text">
          在这里与 Agent 对话...
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputText"
          class="message-input"
          placeholder="输入你的问题... (Shift+Enter 换行)"
          @keydown.enter.exact.prevent="sendMessage"
          rows="3"
        ></textarea>
        <button class="send-btn" @click.prevent="sendMessage" type="button" :disabled="isSending">
          {{ isSending ? '发送中...' : '发送' }}
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useAuthStore } from '../../stores/auth.js'
import { useThemeStore } from '../../stores/theme.js'
import { useMessageParser } from '../../composables/useMessageParser.js'
import { agentAPI } from '../../services/api.js'
import { marked } from 'marked'
import ThemeSuggestionWidget from '../agent/ThemeSuggestionWidget.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggleFromSelf'])

const authStore = useAuthStore()
const themeStore = useThemeStore()
const { parse: parseMessage } = useMessageParser()

// 状态
const messages = ref([])
const inputText = ref('')
const wsRef = ref(null)
const isSending = ref(false)
const hasInitialized = ref(false)
const messagesContainer = ref(null)

// 聊天记录列表
const chatList = ref([])
const currentChatId = ref('')
const STORAGE_KEY = 'proagent_chat_history'

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false
    })
    return marked.parse(text)
  } catch (e) {
    return text
  }
}

// 生成唯一ID
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  
  return date.toLocaleDateString('zh-CN')
}

// 从 localStorage 加载聊天记录列表
const loadChatList = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      chatList.value = JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load chat list:', e)
    chatList.value = []
  }
}

// 保存聊天记录列表到 localStorage
const saveChatList = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chatList.value))
  } catch (e) {
    console.error('Failed to save chat list:', e)
  }
}

// 获取当前聊天记录的存储key
const getChatStorageKey = (chatId) => {
  return `${STORAGE_KEY}_messages_${chatId}`
}

// 保存当前聊天记录
const saveCurrentChat = () => {
  if (!currentChatId.value || messages.value.length === 0) return
  
  try {
    localStorage.setItem(
      getChatStorageKey(currentChatId.value),
      JSON.stringify(messages.value)
    )
    
    // 更新聊天记录列表中的时间
    const chat = chatList.value.find(c => c.id === currentChatId.value)
    if (chat) {
      chat.updatedAt = Date.now()
      saveChatList()
    }
  } catch (e) {
    console.error('Failed to save chat:', e)
  }
}

// 加载指定聊天记录
const loadChatMessages = (chatId) => {
  if (!chatId) return
  
  try {
    const stored = localStorage.getItem(getChatStorageKey(chatId))
    if (stored) {
      messages.value = JSON.parse(stored)
    } else {
      messages.value = []
    }
  } catch (e) {
    console.error('Failed to load chat messages:', e)
    messages.value = []
  }
}

// 创建新对话
const createNewChat = () => {
  // 先保存当前对话
  if (currentChatId.value) {
    saveCurrentChat()
  }
  
  const newChat = {
    id: generateId(),
    title: '新对话 ' + (chatList.value.length + 1),
    createdAt: Date.now(),
    updatedAt: Date.now()
  }
  
  chatList.value.unshift(newChat)
  saveChatList()
  
  currentChatId.value = newChat.id
  messages.value = []
  
  // 清空后端会话
  agentAPI.clearLocalSession('default').catch(console.error)
}

// 切换对话
const switchChat = (chatId) => {
  if (chatId === currentChatId.value) return
  
  // 保存当前对话
  saveCurrentChat()
  
  // 切换
  currentChatId.value = chatId
  loadChatMessages(chatId)
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

// 删除对话
const deleteChat = (chatId) => {
  const index = chatList.value.findIndex(c => c.id === chatId)
  if (index === -1) return
  
  // 删除消息存储
  localStorage.removeItem(getChatStorageKey(chatId))
  
  // 从列表移除
  chatList.value.splice(index, 1)
  saveChatList()
  
  // 如果删除的是当前对话，切换到第一个或创建新对话
  if (currentChatId.value === chatId) {
    if (chatList.value.length > 0) {
      switchChat(chatList.value[0].id)
    } else {
      createNewChat()
    }
  }
}

// 自动生成标题（基于第一条用户消息）
const autoGenerateTitle = () => {
  if (!currentChatId.value) return
  
  const chat = chatList.value.find(c => c.id === currentChatId.value)
  if (!chat || chat.title !== '新对话 ' + chatList.value.length) return
  
  // 找第一条用户消息
  const firstUserMsg = messages.value.find(m => m.role === 'user')
  if (firstUserMsg) {
    // 截取前20个字符作为标题
    let title = firstUserMsg.text.substring(0, 20)
    if (firstUserMsg.text.length > 20) title += '...'
    chat.title = title
    saveChatList()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 连接 WebSocket
const connectWebSocket = () => {
  if (!authStore.isAuthenticated) return

  disconnectWebSocket()
  wsRef.value = agentAPI.connectWebSocket(
    'default',
    (data) => {
      if (data.role === 'assistant') {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
          lastMsg.text += data.content
        } else {
          messages.value.push({ role: 'assistant', text: data.content, done: false })
        }
        scrollToBottom()
      }
    },
    () => {},
    (error) => {
      messages.value.push({
        role: 'agent',
        text: `❌ 错误: ${error.message || '连接失败'}`,
        done: true
      })
      scrollToBottom()
    },
    () => {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg) {
        lastMsg.done = true
      }
      saveCurrentChat()
      autoGenerateTitle()
    }
  )
}

// 断开 WebSocket
const disconnectWebSocket = () => {
  if (wsRef.value) {
    wsRef.value.close()
    wsRef.value = null
  }
}

// 发送消息
const sendMessage = () => {
  if (!inputText.value.trim() || isSending.value) return

  isSending.value = true
  const message = inputText.value.trim()

  messages.value.push({ role: 'user', text: message, done: true })
  inputText.value = ''
  
  scrollToBottom()
  saveCurrentChat()
  autoGenerateTitle()

  if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
    wsRef.value.send(JSON.stringify({ type: 'chat', message }))
    isSending.value = false
  } else {
    sendViaREST(message).finally(() => {
      isSending.value = false
      saveCurrentChat()
      autoGenerateTitle()
    })
  }
}

// REST 发送
const sendViaREST = async (message) => {
  try {
    const result = await agentAPI.chatLocal(message, 'default')
    messages.value.push({
      role: 'agent',
      text: result.response || '没有响应',
      done: true
    })
    scrollToBottom()
  } catch (err) {
    messages.value.push({
      role: 'agent',
      text: `❌ 发送失败: ${err.message}`,
      done: true
    })
    scrollToBottom()
  }
}

// Apply theme suggestion from agent
  const applyThemeSuggestion = (tokens) => {
    themeStore.applySuggestion(tokens)
  }

  onMounted(() => {
  loadChatList()
  
  // 如果没有聊天记录，创建一个
  if (chatList.value.length === 0) {
    createNewChat()
  } else {
    // 加载最近的对话
    currentChatId.value = chatList.value[0].id
    loadChatMessages(currentChatId.value)
  }
  
  if (authStore.isAuthenticated && !hasInitialized.value) {
    hasInitialized.value = true
    connectWebSocket()
  }
})

onUnmounted(() => {
  saveCurrentChat()
  disconnectWebSocket()
})

watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && !hasInitialized.value) {
    hasInitialized.value = true
    connectWebSocket()
  } else if (!isAuth) {
    disconnectWebSocket()
  }
})
</script>

<style scoped>
.right-sidebar {
  width: 320px;
  flex-shrink: 0;
  background-color: var(--clr-bg-agent, rgba(235, 235, 235, 0.65));
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.right-sidebar.is-collapsed {
  width: 0;
  border-left: none;
}

.agent-header {
  height: 52px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  flex-shrink: 0;
}

.close-agent-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.5);
  transition: all 0.2s ease;
}

.close-agent-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
}

/* 聊天记录列表 */
.chat-list-section {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  max-height: 180px;
  display: flex;
  flex-direction: column;
}

.chat-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
}

.chat-list-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #1d1d1f;
  cursor: pointer;
  transition: all 0.2s ease;
}

.new-chat-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.new-chat-btn svg {
  stroke-width: 2;
}

.chat-list {
  overflow-y: auto;
  padding: 0 8px 8px;
  flex: 1;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  margin-bottom: 2px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.chat-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.chat-item.active {
  background-color: rgba(0, 0, 0, 0.08);
}

.chat-item.active .chat-title {
  font-weight: 600;
}

.chat-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.4);
}

.chat-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.chat-title {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
  margin-top: 1px;
}

.delete-chat-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  background: transparent;
  border: none;
  color: rgba(0, 0, 0, 0.3);
  opacity: 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chat-item:hover .delete-chat-btn {
  opacity: 1;
}

.delete-chat-btn:hover {
  background: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.chat-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.4);
}

/* 对话框区域 */
.dialog-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message {
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 90%;
}

.message.user {
  background: white;
  color: #1d1d1f;
  align-self: flex-end;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.agent {
  background: white;
  color: #1d1d1f;
  align-self: flex-start;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-content {
  word-break: break-word;
}

.placeholder-text {
  color: #86868b;
  font-size: 12px;
  text-align: center;
  padding: 40px 20px;
}

/* Markdown 样式 */
.markdown-body {
  line-height: 1.5;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  margin: 8px 0 4px 0;
  font-weight: 600;
}

.markdown-body h1 { font-size: 14px; }
.markdown-body h2 { font-size: 13px; }
.markdown-body h3 { font-size: 12px; }

.markdown-body p { margin: 4px 0; }

.markdown-body ul, .markdown-body ol {
  margin: 4px 0;
  padding-left: 16px;
}

.markdown-body li { margin: 2px 0; }

.markdown-body code {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: ui-monospace, monospace;
  font-size: 11px;
}

/* 输入区域 */
.input-area {
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  resize: none;
  max-height: 80px;
  background: rgba(255, 255, 255, 0.8);
  color: #1d1d1f;
}

.message-input:focus {
  outline: none;
  border-color: #007aff;
  background: white;
}

.message-input::placeholder {
  color: rgba(0, 0, 0, 0.4);
}

.send-btn {
  padding: 6px 14px;
  background: white;
  color: #1d1d1f;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  align-self: flex-end;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.send-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.send-btn:disabled {
  background: rgba(0, 0, 0, 0.05);
  color: rgba(0, 0, 0, 0.3);
  cursor: not-allowed;
}
</style>
