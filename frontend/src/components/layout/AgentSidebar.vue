<template>
  <aside 
    class="macos-sidebar right-sidebar agent-panel" 
    :class="{ 'is-collapsed': !isOpen }"
  >
    <div class="agent-header">
      <span class="font-semibold">Agent 助手</span>
      
      <button class="icon-btn close-agent-btn" @click="emit('toggleFromSelf')" title="收起 Agent 助手">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
      </button>
    </div>

    <div class="agent-body">
      <!-- Thought Trace 区域：展示推理过程 -->
      <div class="trace-section">
        <div class="trace-header">
          <h4 class="trace-title">思维轨迹</h4>
          <button class="trace-toggle-btn" @click="traceExpanded = !traceExpanded" type="button">
            {{ traceExpanded ? '▼' : '▶' }}
          </button>
        </div>
        
        <div v-if="traceExpanded" class="trace-content">
          <div v-for="(event, idx) in traceEvents" :key="idx" class="trace-event">
            <div class="event-phase" :class="`phase-${event.phase}`">
              {{ phaseLabel[event.phase] }}
            </div>
            <div class="event-summary">{{ event.summary }}</div>
            <div class="event-meta">{{ event.durationMs }}ms</div>
          </div>
          <div v-if="traceEvents.length === 0" class="trace-empty">
            等待 Agent 执行...
          </div>
        </div>
      </div>

      <!-- 对话框区域 -->
      <div class="dialog-section">
        <div class="messages-list">
          <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
            <div class="message-content markdown-body" v-html="renderMarkdown(msg.text)"></div>
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
          <button class="send-btn" @click.prevent="sendMessage" type="button" :disabled="isSending">{{ isSending ? '发送中...' : '发送' }}</button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '../../stores/auth.js'
import { agentAPI } from '../../services/api.js'
import { marked } from 'marked'

defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggleFromSelf'])

// Auth store
const authStore = useAuthStore()

// 状态
const traceExpanded = ref(true)
const messages = ref([])
const inputText = ref('')
const wsRef = ref(null)
const sessionId = ref('default')
const isConnecting = ref(false)
const isConnected = ref(false)
const agentStatus = ref(null)
const isSending = ref(false)
const hasInitialized = ref(false)

// Thought Trace 数据
const phaseLabel = {
  planning: '📋 规划',
  tool_call: '🔧 工具调用',
  observation: '👁️ 观察',
  result: '✅ 结果',
  tool: '🔧 工具调用'
}

const traceEvents = ref([])

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

// 欢迎消息
const welcomeMessage = 'Hello! 我是 ProAgent 智能助手，现在具备文件管理能力。我可以：\n\n' +
  '📁 读取、编辑项目文件\n' +
  '🔍 搜索文件和内容\n' +
  '💡 分析代码、回答问题\n\n' +
  '试试问我："帮我找出所有 Python 文件中的 TODO"'

// 加载历史消息
const loadHistory = async () => {
  try {
    const result = await agentAPI.getLocalSession(sessionId.value)
    if (result.success && result.messages) {
      messages.value = result.messages.map(m => ({
        role: m.role,
        text: m.content
      }))
    }
    if (messages.value.length === 0) {
      messages.value.push({ role: 'agent', text: welcomeMessage })
    }
  } catch (err) {
    console.error('[Agent] Failed to load history:', err)
    messages.value.push({ role: 'agent', text: welcomeMessage })
  }
}

// 获取 Agent 状态
const loadAgentStatus = async () => {
  try {
    const status = await agentAPI.getStatus()
    agentStatus.value = status
    console.log('[Agent] Status:', status)
  } catch (err) {
    console.error('[Agent] Failed to get status:', err)
  }
}

// 连接 WebSocket
const connectWebSocket = () => {
  if (!authStore.isAuthenticated) {
    console.log('[Agent] Not authenticated, skipping WebSocket connection')
    return
  }

  disconnectWebSocket()

  isConnecting.value = true

  wsRef.value = agentAPI.connectWebSocket(
    sessionId.value,
    // onMessage
    (data) => {
      if (data.role === 'assistant') {
        // 如果最后一条消息是 assistant，追加内容
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.done) {
          lastMsg.text += data.content
        } else {
          messages.value.push({ role: 'assistant', text: data.content, done: false })
        }
      }
      // 不再处理 data.role === 'user'：
      // 用户消息已在 sendMessage() 中本地添加，无需重复添加
    },
    // onTool
    (data) => {
      traceEvents.value.push(data)
    },
    // onError
    (error) => {
      console.error('[Agent] WebSocket error:', error)
      isConnected.value = false
      isConnecting.value = false
      messages.value.push({
        role: 'agent',
        text: `❌ 错误: ${error.message || '连接失败'}`,
        done: true
      })
    },
    // onDone
    (data) => {
      console.log('[Agent] Request completed:', data)
      // 标记最后一条消息完成
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg) {
        lastMsg.done = true
      }
    }
  )

  if (wsRef.value) {
    wsRef.value.onopen = () => {
      console.log('[Agent] WebSocket connected')
      isConnected.value = true
      isConnecting.value = false
    }
  }
}

// 断开 WebSocket
const disconnectWebSocket = () => {
  if (wsRef.value) {
    wsRef.value.close()
    wsRef.value = null
  }
  isConnected.value = false
  isConnecting.value = false
}

const sendMessage = () => {
  if (!inputText.value.trim() || isSending.value) return

  isSending.value = true
  const message = inputText.value.trim()

  messages.value.push({ role: 'user', text: message, done: true })
  inputText.value = ''

  if (wsRef.value && wsRef.value.readyState === WebSocket.OPEN) {
    wsRef.value.send(JSON.stringify({
      type: 'chat',
      message
    }))
    isSending.value = false
  } else {
    sendViaREST(message).finally(() => {
      isSending.value = false
    })
  }
}

// 通过 REST API 发送消息（降级方案）
const sendViaREST = async (message) => {
  try {
    const result = await agentAPI.chatLocal(message, sessionId.value)

    // 添加助手消息
    messages.value.push({
      role: 'agent',
      text: result.response || '没有响应',
      done: true
    })

    // 显示工具调用
    if (result.tool_calls && result.tool_calls.length > 0) {
      for (const tool of result.tool_calls) {
        traceEvents.value.push({
          phase: 'tool',
          summary: `调用工具: ${tool}`,
          durationMs: 0
        })
      }
    }
  } catch (err) {
    console.error('[Agent] Failed to send message:', err)
    messages.value.push({
      role: 'agent',
      text: `❌ 发送失败: ${err.message}`,
      done: true
    })
  }
}

// 清空对话
const clearChat = () => {
  messages.value = [{ role: 'agent', text: welcomeMessage }]
  traceEvents.value = []
  agentAPI.clearLocalSession(sessionId.value).catch(console.error)
}

onMounted(() => {
  loadAgentStatus()
  if (authStore.isAuthenticated && !hasInitialized.value) {
    hasInitialized.value = true
    loadHistory()
    connectWebSocket()
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})

watch(() => authStore.isAuthenticated, (isAuth) => {
  if (isAuth && !hasInitialized.value) {
    hasInitialized.value = true
    loadHistory()
    connectWebSocket()
  } else if (!isAuth) {
    disconnectWebSocket()
    messages.value = [{ role: 'agent', text: '请先登录使用 Agent 助手' }]
  }
})
</script>

<style scoped>
/* 右侧侧边栏核心容器样式 */
.right-sidebar {
  width: 300px;
  flex-shrink: 0;
  background-color: var(--clr-bg-agent, rgba(235, 235, 235, 0.65));
  background-image: var(--clr-bg-agent-image, none);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-left: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
  overflow: hidden;
}

.right-sidebar.is-collapsed {
  width: 0;
  border-left: none;
}

/* 内部结构样式 */
.agent-header {
  height: 52px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
  flex-shrink: 0;
  white-space: nowrap; 
}

.close-agent-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.close-agent-btn:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
}

.agent-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Thought Trace 区域 */
.trace-section {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  padding: 10px;
  flex-shrink: 0;
}

.trace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.trace-title {
  font-size: 12px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.trace-toggle-btn {
  background: transparent;
  border: none;
  font-size: 10px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.5);
  padding: 2px 4px;
}

.trace-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.trace-event {
  font-size: 11px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  border-left: 3px solid #0071e3;
}

.event-phase {
  font-weight: 600;
  color: #1d1d1f;
  margin-bottom: 2px;
}

.event-phase.phase-planning {
  color: #007aff;
}

.event-phase.phase-tool_call {
  color: #ff9500;
}

.event-phase.phase-observation {
  color: #34c759;
}

.event-phase.phase-result {
  color: #5ac8fa;
}

.event-summary {
  color: #555;
  margin-bottom: 2px;
}

.event-meta {
  font-size: 10px;
  color: #999;
}

.trace-empty {
  font-size: 11px;
  color: #999;
  text-align: center;
  padding: 20px 0;
}

/* 对话框区域 */
.dialog-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.messages-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
  min-height: 100px;
}

.message {
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.4;
  word-break: break-word;
}

.message.user {
  background: #0071e3;
  color: white;
  align-self: flex-end;
  max-width: 85%;
}

.message.agent {
  background: rgba(0, 0, 0, 0.05);
  color: #1d1d1f;
  align-self: flex-start;
}

.message-content {
  margin: 0;
}

/* Markdown 样式 */
.markdown-body {
  line-height: 1.5;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  margin: 8px 0 4px 0;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-body h1 { font-size: 14px; }
.markdown-body h2 { font-size: 13px; }
.markdown-body h3 { font-size: 12px; }
.markdown-body h4 { font-size: 11px; }

.markdown-body p {
  margin: 4px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 4px 0;
  padding-left: 16px;
}

.markdown-body li {
  margin: 2px 0;
}

.markdown-body code {
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 11px;
}

.markdown-body pre {
  background: rgba(0, 0, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 4px 0;
}

.markdown-body pre code {
  background: none;
  padding: 0;
}

.markdown-body blockquote {
  border-left: 3px solid rgba(0, 0, 0, 0.2);
  margin: 4px 0;
  padding-left: 8px;
  color: #666;
}

.markdown-body strong {
  font-weight: 600;
}

.markdown-body em {
  font-style: italic;
}

.markdown-body a {
  color: #0071e3;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.message.user .markdown-body code {
  background: rgba(255, 255, 255, 0.2);
}

.placeholder-text {
  color: #86868b;
  font-size: 12px;
  text-align: center;
  padding: 40px 10px;
}

/* 输入区域 */
.input-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}

.message-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  font-size: 12px;
  font-family: inherit;
  resize: vertical;
  max-height: 80px;
}

.message-input:focus {
  outline: none;
  border-color: #0071e3;
  box-shadow: 0 0 0 2px rgba(0, 113, 227, 0.1);
}

.send-btn {
  padding: 6px 12px;
  background: #0071e3;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.send-btn:hover {
  background: #0051d5;
}

.send-btn:active {
  background: #003da6;
}

.send-btn:disabled {
  background: #999;
  cursor: not-allowed;
}
</style>