<template>
  <aside 
    class="macos-sidebar right-sidebar agent-panel" 
    :class="{ 'is-collapsed': !isOpen }"
  >
    <div class="agent-header">
      <div class="agent-header-left">
        <span class="font-semibold">Agent 助手</span>
        <span v-if="fmStore.isDirectorySet" class="fm-badge" :title="'工作目录: ' + fmStore.workingDirectory">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          {{ shortDir }}
        </span>
      </div>
      <button class="icon-btn close-agent-btn" @click="emit('toggleFromSelf')" title="收起 Agent 助手">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
    </div>

    <!-- 聊天记录列表 -->
    <div class="chat-list-section" :class="{ 'is-collapsed': chatListCollapsed }">
      <div class="chat-list-header" @click="chatListCollapsed = !chatListCollapsed">
        <div class="chat-list-header-left">
          <svg class="chat-list-toggle-icon" :class="{ 'is-rotated': chatListCollapsed }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          <span class="chat-list-title">聊天记录</span>
        </div>
        <button class="new-chat-btn" @click.stop="createNewChat" type="button" title="新建对话">
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
        <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="[msg.role]">
          <div v-for="(segment, si) in parseMessage(msg.text)" :key="si">
            <div v-if="segment.type === 'text'" class="message-content markdown-body" v-html="renderMarkdown(segment.content)"></div>
            <ThemeSuggestionWidget
              v-else-if="segment.type === 'theme-suggestion'"
              :tokens="segment.tokens"
              :initially-dismissed="isThemeDismissed(currentChatId, idx)"
              @accept="applyThemeSuggestion(segment.tokens); markThemeDismissed(currentChatId, idx)"
              @dismiss="markThemeDismissed(currentChatId, idx)"
            />
            <DeleteConfirmWidget
              v-else-if="segment.type === 'delete-confirm'"
              :files="segment.files"
              :working-directory="fmStore.workingDirectory"
              @confirm="onDeleteConfirmed(idx, segment.files)"
              @dismiss="onDeleteDismissed(idx)"
            />
          </div>
        </div>
        <div v-if="messages.length === 0 && !isThinking" class="placeholder-text">
          在这里与 Agent 对话...
        </div>
        <div v-if="isThinking" class="thinking-indicator">
          <span class="thinking-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </span>
          <span class="thinking-text">{{ currentToolLabel || 'Agent 正在思考' }}</span>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputText"
          class="message-input"
          placeholder="输入你的问题... (Shift+Enter 换行)"
          @keydown.enter.exact="onEnterKeyDown"
          @compositionstart="onCompositionStart"
          @compositionend="onCompositionEnd"
          rows="3"
        ></textarea>
        <div class="input-actions">
          <div class="model-selector" @click.stop="toggleModelDropdown" ref="modelSelectorRef">
            <span class="model-selector-label">{{ currentModelLabel }}</span>
            <svg class="model-selector-arrow" :class="{ open: showModelDropdown }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
            <div v-if="showModelDropdown" class="model-dropdown">
              <div v-if="activeModels.length === 0" class="model-dropdown-empty">暂无可用模型</div>
              <div
                v-for="m in activeModels"
                :key="m.provider"
                class="model-dropdown-item"
                :class="{ active: currentProvider === m.provider }"
                @click.stop="switchModel(m)"
              >
                <span class="model-dropdown-name">{{ m.provider }} / {{ m.model }}</span>
                <span v-if="currentProvider === m.provider" class="model-dropdown-check">✓</span>
              </div>
            </div>
          </div>
          <button v-if="!isSending && !isThinking" class="send-btn" @click.prevent="sendMessage" type="button">
            发送
          </button>
          <button v-else class="stop-btn" @click.prevent="stopGenerating" type="button">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
            停止
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="noKeyModalVisible" class="no-key-modal-mask" @click.self="noKeyModalVisible = false">
        <div class="no-key-modal" role="dialog" aria-modal="true" aria-label="未配置 API Key">
          <h3 class="no-key-modal-title">未配置 API Key</h3>
          <p class="no-key-modal-body">当前没有可用的 AI 服务密钥，请前往用户设置绑定 API Key。</p>
          <div class="no-key-modal-actions">
            <button class="no-key-modal-btn primary" type="button" @click="router.push('/user-settings'); noKeyModalVisible = false">去设置</button>
            <button class="no-key-modal-btn ghost" type="button" @click="noKeyModalVisible = false">取消</button>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth.js'
import { useThemeStore } from '../../stores/theme.js'
import { useCalendarStore } from '../../stores/calendar.js'
import { useDashboardStore } from '../../stores/dashboard.js'
import { useFileManagerStore } from '../../stores/fileManager.js'
import { useEmailStore } from '../../stores/email.js'
import { useMessageParser } from '../../composables/useMessageParser.js'
import { agentAPI } from '../../services/api.js'
import { marked } from 'marked'
import ThemeSuggestionWidget from '../agent/ThemeSuggestionWidget.vue'
import DeleteConfirmWidget from '../agent/DeleteConfirmWidget.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggleFromSelf'])

const authStore = useAuthStore()
const themeStore = useThemeStore()
const calendarStore = useCalendarStore()
const dashboardStore = useDashboardStore()
const fmStore = useFileManagerStore()
const emailStore = useEmailStore()
const { parse: parseMessage } = useMessageParser()

const shortDir = computed(() => {
  const dir = fmStore.workingDirectory
  if (!dir) return ''
  const parts = dir.replace(/\/+$/, '').split('/')
  return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : dir
})

const CALENDAR_TOOL_NAMES = new Set([
  'create_schedule_event',
  'update_schedule_event',
  'update_schedule_event_time',
  'delete_schedule_event'
])

const TASK_TOOL_NAMES = new Set([
  'create_task',
  'update_task',
  'delete_task'
])

const FILE_TOOL_NAMES = new Set([
  'write_file',
  'edit_file',
  'move_file',
  'copy_file',
  'delete_file',
  'create_dir'
])

const EMAIL_TOOL_NAMES = new Set([
  'star_email',
  'unstar_email',
  'get_starred_emails',
  'check_email_status',
  'get_emails',
  'send_email',
  'analyze_emails',
  'sync_emails',
  'delete_email',
  'get_trash_emails',
  'restore_email',
  'permanent_delete_email',
  'empty_trash',
])

// 状态
const messages = ref([])
const inputText = ref('')
const wsRef = ref(null)
const isSending = ref(false)
const isThinking = ref(false)
const currentToolLabel = ref('')
const hasInitialized = ref(false)
const messagesContainer = ref(null)
const chatListCollapsed = ref(false)
const abortControllerRef = ref(null)
const isStopping = ref(false)

// 工具名 → 中文显示映射
const TOOL_LABELS = {
  get_user_profile: '正在读取用户画像...',
  create_schedule_event: '正在创建日程...',
  update_schedule_event: '正在更新日程...',
  update_schedule_event_time: '正在调整日程时间...',
  delete_schedule_event: '正在删除日程...',
  read_file: '正在读取文件...',
  write_file: '正在写入文件...',
  edit_file: '正在编辑文件...',
  list_dir: '正在浏览目录...',
  create_dir: '正在创建目录...',
  search_files: '正在搜索文件...',
  grep: '正在搜索内容...',
  move_file: '正在移动文件...',
  copy_file: '正在复制文件...',
  delete_file: '正在删除文件...',
  exec: '正在执行命令...',
  check_email_status: '正在检查邮箱状态...',
  get_emails: '正在获取邮件...',
  send_email: '正在发送邮件...',
  analyze_emails: '正在分析邮件...',
  sync_emails: '正在同步邮件...',
  list_tasks: '正在加载任务...',
  create_task: '正在创建任务...',
  update_task: '正在更新任务...',
  delete_task: '正在删除任务...',
  get_blackboard_status: '正在检查Blackboard...',
  sync_blackboard: '正在同步Blackboard...',
  get_blackboard_assignments: '正在获取作业...',
  get_tis_status: '正在检查TIS...',
  get_tis_schedule: '正在读取课表...',
  list_courses: '正在加载课程...',
  get_starred_emails: '正在获取星标邮件...',
  star_email: '正在标记星标...',
  unstar_email: '正在取消星标...',
}

function getToolLabel(toolName) {
  return TOOL_LABELS[toolName] || `正在执行 ${toolName}...`
}

// 工具名 → 对话记录标签（非进行时，用于已完成的工具调用展示）
const TOOL_CHAT_LABELS = {
  get_user_profile: '读取用户画像',
  list_dir: '浏览目录',
  read_file: '读取文件',
  write_file: '写入文件',
  grep: '搜索内容',
  search_files: '搜索文件',
  create_schedule_event: '创建日程',
  update_schedule_event: '更新日程',
  delete_schedule_event: '删除日程',
  list_tasks: '加载任务',
  create_task: '创建任务',
  update_task: '更新任务',
  delete_task: '删除任务',
  get_emails: '获取邮件',
  send_email: '发送邮件',
  sync_emails: '同步邮件',
  exec: '执行命令',
}

function getToolChatLabel(toolName) {
  return TOOL_CHAT_LABELS[toolName] || toolName
}

// 模型选择
const activeModels = ref([])
const currentProvider = ref('')
const currentModel = ref('')
const showModelDropdown = ref(false)
const modelSelectorRef = ref(null)
const noKeyModalVisible = ref(false)

const router = useRouter()
const route = useRoute()

const handleClickOutside = (e) => {
  if (modelSelectorRef.value && !modelSelectorRef.value.contains(e.target)) {
    showModelDropdown.value = false
  }
}

const toggleModelDropdown = async () => {
  if (!showModelDropdown.value) {
    await loadActiveModels()
  }
  showModelDropdown.value = !showModelDropdown.value
}

const currentModelLabel = computed(() => {
  if (activeModels.value.length === 0) return '未配置模型'
  if (currentProvider.value && currentModel.value) {
    return `${currentProvider.value} / ${currentModel.value}`
  }
  return '选择模型'
})

const loadActiveModels = async () => {
  try {
    const result = await agentAPI.backend.getActiveModels()
    activeModels.value = result.models || []
  } catch (e) {
    console.error('Failed to load active models:', e)
    activeModels.value = []
  }
}

const loadCurrentModel = async () => {
  try {
    const status = await agentAPI.backend.getStatus()
    currentProvider.value = status.provider || ''
    currentModel.value = status.model || ''
  } catch (e) {
    console.error('Failed to load current model:', e)
  }
}

const switchModel = async (m) => {
  showModelDropdown.value = false
  try {
    await agentAPI.backend.updateConfig({
      provider: m.provider,
      model: m.model,
      api_key: m.api_key,
      api_base: m.api_base,
    })
    currentProvider.value = m.provider
    currentModel.value = m.model
  } catch (e) {
    console.error('Failed to switch model:', e)
  }
}

// 跟踪当前正在接收回复的对话 ID，防止切换对话后回复被放到错误的对话中
const sentChatId = ref('')

// 已忽略的主题建议，key = "chatId:msgIdx"，持久化到 localStorage
const DISMISSED_STORAGE_KEY = 'proagent_theme_dismissed'
const dismissedThemes = ref(new Set())

const loadDismissedThemes = () => {
  try {
    const raw = localStorage.getItem(DISMISSED_STORAGE_KEY)
    if (raw) dismissedThemes.value = new Set(JSON.parse(raw))
  } catch { dismissedThemes.value = new Set() }
}
const saveDismissedThemes = () => {
  try {
    localStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify([...dismissedThemes.value]))
  } catch { /* ignore */ }
}

const isThemeDismissed = (chatId, msgIdx) => dismissedThemes.value.has(`${chatId}:${msgIdx}`)
const markThemeDismissed = (chatId, msgIdx) => {
  dismissedThemes.value.add(`${chatId}:${msgIdx}`)
  saveDismissedThemes()
}

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

// 将消息添加到指定对话（不论当前是否在查看该对话）
const appendMessageToChat = (chatId, message) => {
  if (chatId === currentChatId.value) {
    // 当前正在查看该对话，直接 push 到响应式数组
    messages.value.push(message)
  } else {
    // 不在当前对话，写入 localStorage
    try {
      const storageKey = getChatStorageKey(chatId)
      const stored = localStorage.getItem(storageKey)
      const chatMessages = stored ? JSON.parse(stored) : []
      chatMessages.push(message)
      localStorage.setItem(storageKey, JSON.stringify(chatMessages))

      const chat = chatList.value.find(c => c.id === chatId)
      if (chat) {
        chat.updatedAt = Date.now()
        saveChatList()
      }
    } catch (e) {
      console.error('Failed to append message to chat:', e)
    }
  }
}

// 追加流式文本到指定对话的最后一条 assistant 消息
const appendStreamToChat = (chatId, content) => {
  if (chatId === currentChatId.value) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
      lastMsg.text += content
    } else {
      messages.value.push({ role: 'assistant', text: content, done: false })
    }
  } else {
    // 保存到 localStorage，找到最后一条 assistant 消息追加
    try {
      const storageKey = getChatStorageKey(chatId)
      const stored = localStorage.getItem(storageKey)
      const chatMessages = stored ? JSON.parse(stored) : []
      const lastMsg = chatMessages[chatMessages.length - 1]
      if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
        lastMsg.text += content
      } else {
        chatMessages.push({ role: 'assistant', text: content, done: false })
      }
      localStorage.setItem(storageKey, JSON.stringify(chatMessages))

      const chat = chatList.value.find(c => c.id === chatId)
      if (chat) {
        chat.updatedAt = Date.now()
        saveChatList()
      }
    } catch (e) {
      console.error('Failed to append stream to chat:', e)
    }
  }
}

// 标记指定对话的最后一条 assistant 消息为完成
const markLastAssistantDone = (chatId) => {
  if (chatId === currentChatId.value) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg) lastMsg.done = true
  } else {
    try {
      const storageKey = getChatStorageKey(chatId)
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        const chatMessages = JSON.parse(stored)
        const lastMsg = chatMessages[chatMessages.length - 1]
        if (lastMsg) lastMsg.done = true
        localStorage.setItem(storageKey, JSON.stringify(chatMessages))
      }
    } catch (e) {
      console.error('Failed to mark message done:', e)
    }
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

const refreshPanelsIfNeeded = async (toolNames = []) => {
  if (!authStore.isAuthenticated) return

  const names = Array.isArray(toolNames) ? toolNames : []
  const hasCalendarMutation = names.some((name) => CALENDAR_TOOL_NAMES.has(name))
  const hasTaskMutation = names.some((name) => TASK_TOOL_NAMES.has(name))
  const hasFileMutation = names.some((name) => FILE_TOOL_NAMES.has(name))
  const hasEmailMutation = names.some((name) => EMAIL_TOOL_NAMES.has(name))

  const promises = []

  if (hasCalendarMutation || hasTaskMutation) {
    promises.push(
      calendarStore.loadSchedules(),
      dashboardStore.loadTodosFromBackend()
    )
  }

  if (hasFileMutation && fmStore.isDirectorySet) {
    promises.push(fmStore.listFiles())
  }

  if (hasEmailMutation) {
    promises.push(emailStore.fetchStarred())
    promises.push(emailStore.fetchMessages())
    promises.push(emailStore.fetchTrash())
  }

  // Always refresh todo and calendar when agent finishes ANY tool work
  if (!hasCalendarMutation && !hasTaskMutation && names.length > 0) {
    promises.push(dashboardStore.loadTodosFromBackend())
  }

  if (promises.length === 0) return

  try {
    await Promise.all(promises)
  } catch (err) {
    console.error('Failed to refresh panels after agent action:', err)
  }
}

// 连接 WebSocket
const connectWebSocket = () => {
  if (!authStore.isAuthenticated) return

  disconnectWebSocket()

  wsRef.value = agentAPI.connectWebSocket(
    'default',
    (data) => {
      // 使用 sentChatId 路由回复到正确的对话
      const targetChatId = sentChatId.value || currentChatId.value

      if (data.isStream) {
        isThinking.value = false
        currentToolLabel.value = ''
        appendStreamToChat(targetChatId, data.content)
        if (targetChatId === currentChatId.value) scrollToBottom()
      } else if (data.role === 'assistant') {
        isThinking.value = false
        currentToolLabel.value = ''
        appendStreamToChat(targetChatId, data.content)
        if (targetChatId === currentChatId.value) scrollToBottom()
      }
    },
    (toolInfo) => {
      const targetChatId = sentChatId.value || currentChatId.value
      if (targetChatId === currentChatId.value) {
        isThinking.value = true
        currentToolLabel.value = getToolLabel(toolInfo.tool)
        // 在对话中插入工具调用记录块
        appendMessageToChat(targetChatId, {
          role: 'tool',
          text: `🔧 ${getToolChatLabel(toolInfo.tool)}`,
          done: true
        })
      }
    },
    (error) => {
      const targetChatId = sentChatId.value || currentChatId.value
      isThinking.value = false
      currentToolLabel.value = ''

      if (isStopping.value) {
        isStopping.value = false
        return
      }

      appendMessageToChat(targetChatId, {
        role: 'agent',
        text: `· 错误: ${error.content || error.message || 'WebSocket 连接异常，请刷新页面重试'}`,
        done: true
      })
      if (targetChatId === currentChatId.value) scrollToBottom()
    },
    (data) => {
      const targetChatId = sentChatId.value || currentChatId.value
      isThinking.value = false
      currentToolLabel.value = ''
      isSending.value = false

      markLastAssistantDone(targetChatId)

      // 通知画像页面有新交互
      window.dispatchEvent(new CustomEvent('interaction-logged'))

      // 只有当前对话才需要保存和更新 UI
      if (targetChatId === currentChatId.value) {
        saveCurrentChat()
        autoGenerateTitle()
      } else {
        // 对非当前对话，直接更新 localStorage 中的标题
        const chat = chatList.value.find(c => c.id === targetChatId)
        if (chat) {
          try {
            const stored = localStorage.getItem(getChatStorageKey(targetChatId))
            if (stored) {
              const msgs = JSON.parse(stored)
              const firstUserMsg = msgs.find(m => m.role === 'user')
              if (firstUserMsg) {
                let title = firstUserMsg.text.substring(0, 20)
                if (firstUserMsg.text.length > 20) title += '...'
                chat.title = title
                saveChatList()
              }
            }
          } catch (e) { /* ignore */ }
        }
      }

      // 通知画像页面有新交互
      window.dispatchEvent(new CustomEvent('interaction-logged'))

      const toolsUsed = Array.isArray(data?.tools_used) ? data.tools_used : []
      const pendingDeletions = Array.isArray(data?.pending_deletions) ? data.pending_deletions : []

      if (pendingDeletions.length > 0) {
        const storageKey = getChatStorageKey(targetChatId)
        try {
          const stored = localStorage.getItem(storageKey)
          if (stored && targetChatId !== currentChatId.value) {
            const chatMessages = JSON.parse(stored)
            const lastMsg = chatMessages[chatMessages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              const files = pendingDeletions.map(d => d.path || d.resolved || '').filter(Boolean)
              if (files.length > 0) {
                lastMsg.text += '\n\n```delete-confirm\n' + JSON.stringify(files) + '\n```'
                localStorage.setItem(storageKey, JSON.stringify(chatMessages))
              }
            }
          } else if (targetChatId === currentChatId.value) {
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg && lastMsg.role === 'assistant') {
              const files = pendingDeletions.map(d => d.path || d.resolved || '').filter(Boolean)
              if (files.length > 0) {
                lastMsg.text += '\n\n```delete-confirm\n' + JSON.stringify(files) + '\n```'
              }
            }
          }
        } catch (e) { /* ignore */ }
      }

      void refreshPanelsIfNeeded(toolsUsed)
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

// IME 回车误触保护（中/日/韩输入法）
const isInputComposing = ref(false)

const onCompositionStart = () => {
  isInputComposing.value = true
}

const onCompositionEnd = () => {
  isInputComposing.value = false
}

const isImeEnter = (e) => {
  return e.isComposing || isInputComposing.value || e.keyCode === 229
}

const onEnterKeyDown = (e) => {
  if (isImeEnter(e)) {
    return
  }
  e.preventDefault()
  sendMessage()
}

// 发送消息
const sendMessage = async () => {
  if (!inputText.value.trim() || isSending.value) return

  await loadActiveModels()

  if (activeModels.value.length === 0) {
    noKeyModalVisible.value = true
    return
  }

  isSending.value = true
  isThinking.value = true
  const message = inputText.value.trim()

  // 记住发送时所在的对话 ID，用于回复路由
  sentChatId.value = currentChatId.value

  messages.value.push({ role: 'user', text: message, done: true })
  inputText.value = ''
  
  scrollToBottom()
  saveCurrentChat()
  autoGenerateTitle()

  const useFileContext = fmStore.isDirectorySet

  if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
    const wsPayload = { type: 'chat', message }
    if (useFileContext) {
      wsPayload.working_directory = fmStore.workingDirectory
    }
    wsRef.value.send(JSON.stringify(wsPayload))
  } else {
    sendViaREST(message, sentChatId.value).finally(() => {
      isSending.value = false
      isThinking.value = false
      if (sentChatId.value === currentChatId.value) {
        saveCurrentChat()
        autoGenerateTitle()
      }
    })
  }
}

// REST 发送
const sendViaREST = async (message, chatId) => {
  isThinking.value = true
  const controller = new AbortController()
  abortControllerRef.value = controller
  try {
    const sessionId = fmStore.isDirectorySet
      ? `file-manager:${fmStore.workingDirectory.replace(/[\/\\]/g, '_')}`
      : 'default'

    const result = fmStore.isDirectorySet
      ? await agentAPI.chatWithWorkingDirectory(message, fmStore.workingDirectory, sessionId, { signal: controller.signal })
      : await agentAPI.chatLocal(message, sessionId, { signal: controller.signal })

    if (controller.signal.aborted) return

    const pendingDeletions = result?.pending_deletions || []
    const toolCalls = result?.tool_calls || []

    // 在对话中插入工具调用链
    if (toolCalls.length > 0) {
      const toolNames = toolCalls.map(t => `🔧 ${getToolLabel(t)}`).join('\n')
      appendMessageToChat(chatId, {
        role: 'tool',
        text: toolNames,
        done: true
      })
    }

    let responseText = result.response || '没有响应'

    if (pendingDeletions.length > 0) {
      const files = pendingDeletions.map(d => d.path || d.resolved || '').filter(Boolean)
      if (files.length > 0) {
        responseText += '\n\n```delete-confirm\n' + JSON.stringify(files) + '\n```'
      }
    }

    appendMessageToChat(chatId, {
      role: 'agent',
      text: responseText,
      done: true
    })
    if (chatId === currentChatId.value) scrollToBottom()
    // 通知画像页面有新交互
    window.dispatchEvent(new CustomEvent('interaction-logged'))
    console.log('[AgentSidebar] refreshPanelsIfNeeded with tools:', result?.tool_calls)
    await refreshPanelsIfNeeded(result?.tool_calls || [])
  } catch (err) {
    if (controller.signal.aborted) return
    appendMessageToChat(chatId, {
      role: 'agent',
      text: `❌ 发送失败: ${err.message}`,
      done: true
    })
    if (chatId === currentChatId.value) scrollToBottom()
  } finally {
    abortControllerRef.value = null
    isThinking.value = false
  }
}

// Apply theme suggestion from agent
const applyThemeSuggestion = (tokens) => {
  themeStore.applySuggestion(tokens)
}

const onDeleteConfirmed = (msgIdx, files) => {
  const msg = messages.value[msgIdx]
  if (!msg) return
  const fileList = files.map(f => `- ${f}`).join('\n')
  msg.text = msg.text.replace(/```delete-confirm\s*\n[\s\S]*?\n```/g, '').trim()
  msg.text += `\n\n✓ 已删除：\n${fileList}`
  saveCurrentChat()
}

const onDeleteDismissed = (msgIdx) => {
  const msg = messages.value[msgIdx]
  if (!msg) return
  msg.text = msg.text.replace(/```delete-confirm\s*\n[\s\S]*?\n```/g, '').trim()
  msg.text += '\n\n✗ 已取消删除'
  saveCurrentChat()
}

const stopGenerating = () => {
  isStopping.value = true

  if (abortControllerRef.value) {
    abortControllerRef.value.abort()
    abortControllerRef.value = null
  }

  if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
    wsRef.value.close()
    wsRef.value = null
  }

  isSending.value = false
  isThinking.value = false

  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
    lastMsg.done = true
    lastMsg.text += '\n\n· 已中断'
  }

  saveCurrentChat()
}



const loadFromBackendSession = async () => {
  if (!authStore.isAuthenticated) return

  try {
    const result = await agentAPI.getLocalSession('default')
    if (result && result.success && result.messages && result.messages.length > 0) {
      const backendMessages = result.messages.map(m => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        text: m.content || '',
        done: true
      }))

      const chatId = generateId()
      const chat = {
        id: chatId,
        title: '历史对话',
        createdAt: Date.now(),
        updatedAt: Date.now()
      }

      chatList.value.unshift(chat)
      localStorage.setItem(getChatStorageKey(chatId), JSON.stringify(backendMessages))
      saveChatList()

      currentChatId.value = chatId
      messages.value = backendMessages

      nextTick(() => scrollToBottom())
    }
  } catch (e) {
    console.error('Failed to load backend session:', e)
  }
}

  onMounted(async () => {
  loadChatList()
  loadDismissedThemes()
  loadActiveModels()
  loadCurrentModel()
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('agent-api-keys-changed', loadActiveModels)

  if (chatList.value.length === 0) {
    await loadFromBackendSession()
    if (chatList.value.length === 0) {
      createNewChat()
    }
  } else {
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
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('agent-api-keys-changed', loadActiveModels)
})

watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && !hasInitialized.value) {
    hasInitialized.value = true
    connectWebSocket()
  } else if (!isAuth) {
    disconnectWebSocket()
  }
})

watch(() => route.path, () => {
  loadActiveModels()
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

.agent-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
}

.fm-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.55);
  background: rgba(0, 122, 255, 0.08);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
  cursor: default;
}

.fm-badge svg {
  flex-shrink: 0;
  color: #007aff;
}

.input-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: space-between;
}

/* 模型选择器 */
.model-selector {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  background: #ffffff;
  cursor: pointer;
  font-size: 11px;
  font-weight: 500;
  color: #333;
  user-select: none;
  transition: all 0.15s;
  flex-shrink: 0;
}

.model-selector:hover {
  border-color: #007aff;
  background: #f0f7ff;
}

.model-selector-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-selector-arrow {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
  transition: transform 0.2s;
}

.model-selector-arrow.open {
  transform: rotate(180deg);
}

.model-dropdown {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 0;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.12);
  min-width: 180px;
  max-height: 240px;
  overflow-y: auto;
  z-index: 100;
  padding: 4px;
}

.model-dropdown-empty {
  padding: 12px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

.model-dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  color: #333;
  transition: background 0.1s;
}

.model-dropdown-item:hover {
  background: #f0f7ff;
}

.model-dropdown-item.active {
  background: rgba(0, 122, 255, 0.08);
  font-weight: 600;
}

.model-dropdown-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-dropdown-check {
  color: #007aff;
  font-weight: 700;
  flex-shrink: 0;
  margin-left: 6px;
}

.close-agent-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid #000000;
  cursor: pointer;
  color: #000000;
  transition: all 0.2s ease;
}

.close-agent-btn:hover {
  background: #f5f5f5;
  color: #000000;
}

/* 聊天记录列表 */
.chat-list-section {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  max-height: 180px;
  display: flex;
  flex-direction: column;
  transition: max-height 0.25s ease;
  overflow: hidden;
}

.chat-list-section.is-collapsed {
  max-height: 36px;
}

.chat-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.chat-list-header-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-list-toggle-icon {
  transition: transform 0.2s ease;
  color: rgba(0, 0, 0, 0.35);
  flex-shrink: 0;
}

.chat-list-toggle-icon.is-rotated {
  transform: rotate(-90deg);
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
  background: #ffffff;
  border: 1px solid #000000;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #000000;
  cursor: pointer;
  transition: all 0.2s ease;
}

.new-chat-btn:hover {
  background: #f5f5f5;
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
  background: #ffffff;
  border: 1px solid #000000;
  color: #000000;
  opacity: 0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chat-item:hover .delete-chat-btn {
  opacity: 1;
}

.delete-chat-btn:hover {
  background: #f5f5f5;
  color: #000000;
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

.message.agent,
.message.assistant {
  background: white;
  color: #1d1d1f;
  align-self: flex-start;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message.tool {
  background: transparent;
  color: #6b7280;
  align-self: flex-start;
  font-size: 11px;
  padding: 2px 14px;
  border-radius: 4px;
  opacity: 0.7;
  border: none;
  box-shadow: none;
  max-width: 100%;
}

.message-content {
  word-break: break-word;
  overflow-wrap: anywhere;
}

.message-content :deep(pre) {
  white-space: pre-wrap;
  word-break: break-all;
  overflow-x: auto;
  max-width: 100%;
  background: #f5f5f7;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 11px;
  line-height: 1.4;
  margin: 6px 0;
}

.message-content :deep(code) {
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 11px;
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

.stop-btn {
  padding: 7px 14px;
  background: rgba(255, 59, 48, 0.1);
  border: 1px solid rgba(255, 59, 48, 0.3);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  color: #ff3b30;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s;
  white-space: nowrap;
}

.stop-btn:hover {
  background: rgba(255, 59, 48, 0.18);
  border-color: rgba(255, 59, 48, 0.5);
}

.send-btn {
  padding: 6px 14px;
  background: #ffffff;
  color: #000000;
  border: 1px solid #000000;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  align-self: flex-end;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.send-btn:hover {
  background: #f5f5f5;
}

.send-btn:disabled {
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #9ca3af;
  cursor: not-allowed;
}



/* Thinking indicator */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  align-self: flex-start;
}

.thinking-dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.thinking-dots .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #007aff;
  animation: thinking-pulse 1.4s ease-in-out infinite;
}

.thinking-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-pulse {
  0%, 80%, 100% {
    opacity: 0.25;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.thinking-text {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.5);
  font-style: italic;
}

.no-key-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.no-key-modal {
  width: min(380px, calc(100vw - 32px));
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fff;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
  padding: 20px;
}

.no-key-modal-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.no-key-modal-body {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
}

.no-key-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.no-key-modal-btn {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
}

.no-key-modal-btn.primary {
  background: #007aff;
  color: #fff;
  border-color: #007aff;
}

.no-key-modal-btn.ghost {
  background: transparent;
  color: #374151;
  border-color: rgba(0, 0, 0, 0.2);
}

.no-key-modal-btn.primary:hover {
  background: #0066d6;
}

.no-key-modal-btn.ghost:hover {
  background: rgba(0, 0, 0, 0.04);
}
</style>
