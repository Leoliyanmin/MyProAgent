import { computed, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { agentAPI } from '../services/api.js'
import { useAgentChatStore } from '../stores/agentChat.js'
import { useAuthStore } from '../stores/auth.js'
import { useCalendarStore } from '../stores/calendar.js'
import { useDashboardStore } from '../stores/dashboard.js'
import { useEmailStore } from '../stores/email.js'
import { useFileManagerStore } from '../stores/fileManager.js'
import { useThemeStore } from '../stores/theme.js'
import { useDailyQuoteStore } from '../stores/dailyQuote.js'
import { useMessageParser } from './useMessageParser.js'

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

const DAILY_QUOTE_TOOL_NAMES = new Set([
  'get_daily_quote',
  'set_daily_quote',
  'refresh_daily_quote',
  'get_daily_quote_history',
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
  'empty_trash'
])

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
  search_files: '正在搜索内容...',
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
  get_blackboard_status: '正在检查 Blackboard...',
  sync_blackboard: '正在同步 Blackboard...',
  get_blackboard_assignments: '正在获取作业...',
  get_tis_status: '正在检查 TIS...',
  get_tis_schedule: '正在读取课表...',
  list_courses: '正在加载课程...',
  get_starred_emails: '正在获取星标邮件...',
  star_email: '正在标记星标...',
  unstar_email: '正在取消星标...',
  get_daily_quote: '正在读取每日一句...',
  set_daily_quote: '正在更新每日一句...',
  refresh_daily_quote: '正在刷新每日一句...',
  get_daily_quote_history: '正在查看历史记录...'
}

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
  exec: '执行命令'
}

const DISMISSED_STORAGE_KEY = 'proagent_theme_dismissed'

function stringifyError(value, fallback = 'WebSocket 连接异常，请刷新页面重试') {
  const raw = value?.content ?? value?.message ?? value ?? fallback
  if (typeof raw === 'string') return raw
  try { return JSON.stringify(raw) } catch { return fallback }
}

export function useAgentChat(sessionId = 'default', { isTemporary = false } = {}) {
  const authStore = useAuthStore()
  const themeStore = useThemeStore()
  const calendarStore = useCalendarStore()
  const dashboardStore = useDashboardStore()
  const fmStore = useFileManagerStore()
  const emailStore = useEmailStore()
  const dailyQuoteStore = useDailyQuoteStore()
  const chatStore = useAgentChatStore()
  const router = useRouter()
  const { parse: parseMessage } = useMessageParser()
  const {
    messages: storeMessages,
    chatList,
    currentChatId,
    activeModels,
    currentProvider,
    currentModel,
    noKeyModalVisible
  } = storeToRefs(chatStore)

  const localMessages = ref([])
  const messages = isTemporary ? localMessages : storeMessages
  const inputText = ref('')
  const wsRef = ref(null)
  const isSending = ref(false)
  const isThinking = ref(false)
  const currentToolLabel = ref('')
  const sentChatId = ref('')
  const abortControllerRef = ref(null)
  const isStopping = ref(false)
  const isInputComposing = ref(false)
  const dismissedThemes = ref(new Set())
  const toolMessagesInFlight = new Set()
  let scrollFn = null

  const safeMessages = computed(() => {
    if (!Array.isArray(messages.value)) return []
    return messages.value
      .filter(message => message && typeof message === 'object')
      .map(message => ({
        ...message,
        role: typeof message.role === 'string' ? message.role : 'assistant',
        text: typeof message.text === 'string' ? message.text : stringifyError(message.text, '')
      }))
  })

  const currentModelLabel = computed(() => {
    if (activeModels.value.length === 0) return '未配置模型'
    if (currentProvider.value && currentModel.value) {
      return `${currentProvider.value} / ${currentModel.value}`
    }
    return '选择模型'
  })

  function getToolLabel(toolName) {
    return TOOL_LABELS[toolName] || `正在执行 ${toolName}...`
  }

  function getToolChatLabel(toolName) {
    return TOOL_CHAT_LABELS[toolName] || toolName
  }

  function renderMarkdown(text) {
    if (!text) return ''
    try {
      marked.setOptions({ breaks: true, gfm: true, headerIds: false, mangle: false })
      return marked.parse(text)
    } catch {
      return text
    }
  }

  function setScrollContainer(fn) {
    scrollFn = fn
  }

  function triggerScroll() {
    if (scrollFn) scrollFn()
  }

  function saveMessagesToStore() {
    if (isTemporary) return
    chatStore.saveChatMessages(currentChatId.value, messages.value)
  }

  function appendMessageToChat(chatId, message) {
    if (chatId === currentChatId.value) {
      messages.value.push(message)
      return
    }
    const storedMessages = chatStore.loadChatMessagesFromStorage(chatId)
    storedMessages.push(message)
    chatStore.saveChatMessages(chatId, storedMessages)
  }

  function appendStreamToChat(chatId, content) {
    const text = typeof content === 'string' ? content : String(content ?? '')
    if (chatId === currentChatId.value) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
        lastMsg.text += text
      } else {
        messages.value.push({ role: 'assistant', text, done: false })
      }
      return
    }

    const storedMessages = chatStore.loadChatMessagesFromStorage(chatId)
    const lastMsg = storedMessages[storedMessages.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
      lastMsg.text += text
    } else {
      storedMessages.push({ role: 'assistant', text, done: false })
    }
    chatStore.saveChatMessages(chatId, storedMessages)
  }

  function markLastAssistantDone(chatId) {
    if (chatId === currentChatId.value) {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg) lastMsg.done = true
      return
    }
    const storedMessages = chatStore.loadChatMessagesFromStorage(chatId)
    const lastMsg = storedMessages[storedMessages.length - 1]
    if (lastMsg) {
      lastMsg.done = true
      chatStore.saveChatMessages(chatId, storedMessages)
    }
  }

  function updateChatTitle(chatId) {
    const chat = chatList.value.find(c => c.id === chatId)
    if (!chat || !chat.title.startsWith('新对话')) return
    const sourceMessages = chatId === currentChatId.value
      ? messages.value
      : chatStore.loadChatMessagesFromStorage(chatId)
    const firstUserMsg = sourceMessages.find(m => m.role === 'user')
    if (!firstUserMsg) return
    chat.title = firstUserMsg.text.length > 20 ? `${firstUserMsg.text.slice(0, 20)}...` : firstUserMsg.text
    chatStore.saveChatList()
  }

  async function refreshPanelsIfNeeded(toolNames = []) {
    if (!authStore.isAuthenticated) return
    const names = Array.isArray(toolNames) ? toolNames : []
    const hasCalendarMutation = names.some(name => CALENDAR_TOOL_NAMES.has(name))
    const hasTaskMutation = names.some(name => TASK_TOOL_NAMES.has(name))
    const hasFileMutation = names.some(name => FILE_TOOL_NAMES.has(name))
    const hasDailyQuoteMutation = names.some(name => DAILY_QUOTE_TOOL_NAMES.has(name))
    const hasEmailMutation = names.some(name => EMAIL_TOOL_NAMES.has(name))
    const promises = []

    if (hasCalendarMutation || hasTaskMutation) {
      promises.push(calendarStore.loadSchedules(), dashboardStore.loadTodosFromBackend())
    }
    if (hasFileMutation && fmStore.isDirectorySet) promises.push(fmStore.listFiles())
    if (hasEmailMutation) {
      promises.push(emailStore.fetchStarred(), emailStore.fetchMessages(), emailStore.fetchTrash())
    }
    if (!hasCalendarMutation && !hasTaskMutation && names.length > 0) {
      promises.push(dashboardStore.loadTodosFromBackend())
    }
    if (hasDailyQuoteMutation) {
      promises.push(dailyQuoteStore.load())
    }

    try { await Promise.all(promises) } catch (err) {
      console.error('Failed to refresh panels after agent action:', err)
    }
  }

  async function loadActiveModels() {
    try {
      const result = await agentAPI.backend.getActiveModels()
      chatStore.setActiveModels(result?.models)
      if (activeModels.value.length > 0) chatStore.dismissNoKeyModal()
    } catch (err) {
      console.error('Failed to load active models:', err)
      chatStore.setActiveModels([])
    }
  }

  async function loadCurrentModel() {
    try {
      const status = await agentAPI.backend.getStatus()
      chatStore.setCurrentModel(status.provider, status.model)
    } catch (err) {
      console.error('Failed to load current model:', err)
    }
  }

  async function switchModel(modelConfig) {
    try {
      await agentAPI.backend.updateConfig({
        provider: modelConfig.provider,
        model: modelConfig.model,
        api_key: modelConfig.api_key,
        api_base: modelConfig.api_base
      })
      chatStore.setCurrentModel(modelConfig.provider, modelConfig.model)
    } catch (err) {
      console.error('Failed to switch model:', err)
    }
  }

  function connectWebSocket() {
    if (!authStore.isAuthenticated) return
    disconnectWebSocket()
    wsRef.value = agentAPI.connectWebSocket(
      sessionId,
      (data) => {
        const targetChatId = sentChatId.value || currentChatId.value
        if (data.isStream || data.role === 'assistant') {
          isThinking.value = false
          currentToolLabel.value = ''
          appendStreamToChat(targetChatId, data.content)
          if (targetChatId === currentChatId.value) triggerScroll()
        }
      },
      (toolInfo) => {
        const targetChatId = sentChatId.value || currentChatId.value
        if (targetChatId !== currentChatId.value) return
        isThinking.value = true
        currentToolLabel.value = getToolLabel(toolInfo.tool)
        if (!toolMessagesInFlight.has(toolInfo.tool)) {
          toolMessagesInFlight.add(toolInfo.tool)
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
        isSending.value = false
        currentToolLabel.value = ''
        if (isStopping.value) {
          isStopping.value = false
          return
        }
        appendMessageToChat(targetChatId, {
          role: 'agent',
          text: `· 错误: ${stringifyError(error)}`,
          done: true
        })
        if (targetChatId === currentChatId.value) triggerScroll()
      },
      (data) => {
        const targetChatId = sentChatId.value || currentChatId.value
        isThinking.value = false
        isSending.value = false
        currentToolLabel.value = ''
        markLastAssistantDone(targetChatId)

        const pendingDeletions = Array.isArray(data?.pending_deletions) ? data.pending_deletions : []
        if (pendingDeletions.length > 0) appendPendingDeletions(targetChatId, pendingDeletions)

        updateChatTitle(targetChatId)
        if (targetChatId === currentChatId.value) saveMessagesToStore()
        window.dispatchEvent(new CustomEvent('interaction-logged'))
        void refreshPanelsIfNeeded(Array.isArray(data?.tools_used) ? data.tools_used : [])
      }
    )
  }

  function disconnectWebSocket() {
    if (!wsRef.value) return
    wsRef.value.close(1000, 'normal disconnect')
    wsRef.value = null
  }

  function appendPendingDeletions(chatId, pendingDeletions) {
    const files = pendingDeletions.map(d => d.path || d.resolved || '').filter(Boolean)
    if (files.length === 0) return
    const suffix = '\n\n```delete-confirm\n' + JSON.stringify(files) + '\n```'
    const targetMessages = chatId === currentChatId.value
      ? messages.value
      : chatStore.loadChatMessagesFromStorage(chatId)
    const lastMsg = targetMessages[targetMessages.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') lastMsg.text += suffix
    if (chatId !== currentChatId.value) chatStore.saveChatMessages(chatId, targetMessages)
  }

  async function sendViaREST(message, chatId) {
    isThinking.value = true
    const controller = new AbortController()
    abortControllerRef.value = controller
    try {
      const restSessionId = fmStore.isDirectorySet
        ? `file-manager:${fmStore.workingDirectory.replace(/[\/\\]/g, '_')}`
        : sessionId
      const result = fmStore.isDirectorySet
        ? await agentAPI.chatWithWorkingDirectory(message, fmStore.workingDirectory, restSessionId, { signal: controller.signal })
        : await agentAPI.chatLocal(message, restSessionId, { signal: controller.signal })

      if (controller.signal.aborted) return
      const toolCalls = Array.isArray(result?.tool_calls) ? result.tool_calls : []
      if (toolCalls.length > 0) {
        appendMessageToChat(chatId, {
          role: 'tool',
          text: toolCalls.map(t => `🔧 ${getToolLabel(t)}`).join('\n'),
          done: true
        })
      }

      let responseText = result?.response || '没有响应'
      const pendingDeletions = Array.isArray(result?.pending_deletions) ? result.pending_deletions : []
      if (pendingDeletions.length > 0) {
        const files = pendingDeletions.map(d => d.path || d.resolved || '').filter(Boolean)
        if (files.length > 0) responseText += '\n\n```delete-confirm\n' + JSON.stringify(files) + '\n```'
      }
      appendMessageToChat(chatId, { role: 'agent', text: responseText, done: true })
      if (chatId === currentChatId.value) triggerScroll()
      window.dispatchEvent(new CustomEvent('interaction-logged'))
      await refreshPanelsIfNeeded(toolCalls)
    } catch (err) {
      if (controller.signal.aborted) return
      appendMessageToChat(chatId, {
        role: 'agent',
        text: `❌ 发送失败: ${stringifyError(err, '发送失败')}`,
        done: true
      })
      if (chatId === currentChatId.value) triggerScroll()
    } finally {
      abortControllerRef.value = null
      isThinking.value = false
    }
  }

  async function sendMessage() {
    const message = inputText.value.trim()
    if (!message || isSending.value) return
    await loadActiveModels()
    if (activeModels.value.length === 0) {
      chatStore.showNoKeyModal()
      return
    }

    isSending.value = true
    isThinking.value = true
    toolMessagesInFlight.clear()
    sentChatId.value = currentChatId.value
    messages.value.push({ role: 'user', text: message, done: true })
    inputText.value = ''
    triggerScroll()
    saveMessagesToStore()
    updateChatTitle(currentChatId.value)

    const wsPayload = { type: 'chat', message }
    if (fmStore.isDirectorySet) wsPayload.working_directory = fmStore.workingDirectory
    if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
      wsRef.value.send(JSON.stringify(wsPayload))
    } else {
      sendViaREST(message, sentChatId.value).finally(() => {
        isSending.value = false
        isThinking.value = false
        saveMessagesToStore()
        updateChatTitle(sentChatId.value)
      })
    }
  }

  function stopGenerating() {
    isStopping.value = true
    if (abortControllerRef.value) {
      abortControllerRef.value.abort()
      abortControllerRef.value = null
    }
    if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
      wsRef.value.close(1000, 'user stopped')
      wsRef.value = null
    }
    isSending.value = false
    isThinking.value = false
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
      lastMsg.done = true
      lastMsg.text += '\n\n· 已中断'
    }
    saveMessagesToStore()
  }

  function createNewChat(temporary = false) {
    const chat = chatStore.createNewChat(temporary)
    chatStore.loadChatMessages(chat.id)
    return chat
  }

  function switchChat(chatId) {
    chatStore.switchChat(chatId)
    triggerScroll()
  }

  function onCompositionStart() { isInputComposing.value = true }
  function onCompositionEnd() { isInputComposing.value = false }
  function isImeEnter(e) { return e.isComposing || isInputComposing.value || e.keyCode === 229 }

  function applyThemeSuggestion(tokens) {
    themeStore.applySuggestion(tokens)
  }

  function loadDismissedThemes() {
    try {
      const raw = localStorage.getItem(DISMISSED_STORAGE_KEY)
      if (raw) dismissedThemes.value = new Set(JSON.parse(raw))
    } catch {
      dismissedThemes.value = new Set()
    }
  }

  function saveDismissedThemes() {
    try { localStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify([...dismissedThemes.value])) } catch {}
  }

  function isThemeDismissed(chatId, msgIdx) {
    return dismissedThemes.value.has(`${chatId}:${msgIdx}`)
  }

  function markThemeDismissed(chatId, msgIdx) {
    dismissedThemes.value.add(`${chatId}:${msgIdx}`)
    saveDismissedThemes()
  }

  function onDeleteConfirmed(msgIdx, files) {
    const msg = messages.value[msgIdx]
    if (!msg) return
    msg.text = msg.text.replace(/```delete-confirm\s*\n[\s\S]*?\n```/g, '').trim()
    msg.text += `\n\n✓ 已删除：\n${files.map(f => `- ${f}`).join('\n')}`
    saveMessagesToStore()
  }

  function onDeleteDismissed(msgIdx) {
    const msg = messages.value[msgIdx]
    if (!msg) return
    msg.text = msg.text.replace(/```delete-confirm\s*\n[\s\S]*?\n```/g, '').trim()
    msg.text += '\n\n✗ 已取消删除'
    saveMessagesToStore()
  }

  function init() {
    chatStore.init()
    loadDismissedThemes()
    loadActiveModels()
    loadCurrentModel()
    if (authStore.isAuthenticated) connectWebSocket()
  }

  function cleanup() {
    saveMessagesToStore()
    disconnectWebSocket()
  }

  return reactive({
    messages,
    safeMessages,
    inputText,
    isSending,
    isThinking,
    currentToolLabel,
    activeModels,
    currentModelLabel,
    currentProvider,
    currentModel,
    noKeyModalVisible,
    isInputComposing,
    chatList,
    currentChatId,
    switchChat,
    deleteChat: chatStore.deleteChat,
    createNewChat,
    loadChatMessages: chatStore.loadChatMessages,
    formatTime: chatStore.formatTime,
    sendMessage,
    stopGenerating,
    switchModel,
    loadActiveModels,
    loadCurrentModel,
    connectWebSocket,
    disconnectWebSocket,
    init,
    cleanup,
    saveMessagesToStore,
    onCompositionStart,
    onCompositionEnd,
    isImeEnter,
    renderMarkdown,
    parseMessage,
    applyThemeSuggestion,
    onDeleteConfirmed,
    onDeleteDismissed,
    isThemeDismissed,
    markThemeDismissed,
    getToolLabel,
    getToolChatLabel,
    setScrollContainer,
    fmStore,
    chatStore,
    router
  })
}
