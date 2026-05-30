<template>
  <div class="widget-panel">
    <div class="widget-header">
      <span class="widget-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M15 3v18"/></svg>
        Agent
      </span>
      <div class="header-right">
        <button class="new-chat-btn" @click="chatStore.createNewChat" title="新对话">+</button>
        <button class="widget-close" @click="close" title="关闭">✕</button>
      </div>
    </div>

    <!-- Chat list -->
    <div class="chat-list-bar" @click="showChats = !showChats">
      <span class="chat-title">{{ currentChatTitle }}</span>
      <svg class="arrow" :class="{ open: showChats }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
    </div>
    <div v-if="showChats" class="chat-list-drop">
      <div
        v-for="chat in chatStore.chatList"
        :key="chat.id"
        class="chat-item"
        :class="{ active: chat.id === chatStore.currentChatId }"
        @click="switchToChat(chat.id)"
      >
        <span class="chat-name">{{ chat.title }}</span>
        <button class="del-btn" @click.stop="chatStore.deleteChat(chat.id)">×</button>
      </div>
    </div>

    <!-- Messages -->
    <div class="chat-body" ref="msgContainer">
      <div v-if="chatStore.messages.length === 0 && !sending" class="placeholder">
        输入消息开始对话...
      </div>
      <div v-for="(msg, idx) in chatStore.messages" :key="idx" class="msg" :class="msg.role">
        <div class="msg-text" v-html="renderMd(msg.text)"></div>
      </div>
      <div v-if="sending" class="msg assistant">
        <div class="thinking"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
      </div>
    </div>

    <!-- Input + model selector -->
    <div class="chat-input-row">
      <div class="model-pick" @click.stop="toggleModels">
        <span class="model-label">{{ modelLabel }}</span>
        <div v-if="showModels" class="model-drop">
          <div
            v-for="m in models"
            :key="m.provider"
            class="model-item"
            :class="{ active: currentProvider === m.provider }"
            @click.stop="switchModel(m)"
          >{{ m.provider }}/{{ m.model }}</div>
        </div>
      </div>
      <textarea
        v-model="input"
        class="chat-input"
        placeholder="输入..."
        rows="1"
        @keydown.enter.exact="handleSend"
        :disabled="sending"
      ></textarea>
      <button class="send-btn" @click="handleSend" :disabled="sending || !input.trim()">
        {{ sending ? '...' : '↑' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useAgentChatStore } from '../../stores/agentChat.js'
import { useDashboardStore } from '../../stores/dashboard.js'
import { agentAPI } from '../../services/api.js'
import { marked } from 'marked'

const chatStore = useAgentChatStore()
const dashboardStore = useDashboardStore()
const close = () => dashboardStore.toggleMiniWidget('agent')

const renderMd = (text) => {
  if (!text) return ''
  try { return marked.parse(text) } catch { return text }
}

const input = ref('')
const sending = ref(false)
const msgContainer = ref(null)
const showChats = ref(false)
const models = ref([])
const currentProvider = ref('')
const currentModel = ref('')
const showModels = ref(false)

const currentChatTitle = computed(() => {
  const c = chatStore.chatList.find(c => c.id === chatStore.currentChatId)
  return c?.title || '对话'
})

const modelLabel = computed(() => {
  if (currentProvider.value) return currentProvider.value.split('/').pop()
  return '模型'
})

const switchToChat = (id) => {
  chatStore.switchChat(id)
  showChats.value = false
}

const scrollDown = () => {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
}

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''
  chatStore.addMessage({ role: 'user', text, done: true })
  scrollDown()
  sending.value = true
  try {
    const result = await agentAPI.chatLocal(text, 'default')
    const reply = result?.response || '没有响应'
    chatStore.addMessage({ role: 'assistant', text: reply, done: true })
  } catch (e) {
    chatStore.addMessage({ role: 'assistant', text: '发送失败: ' + (e?.message || '未知错误'), done: true })
  } finally {
    sending.value = false
    scrollDown()
  }
}

const toggleModels = async () => {
  if (!showModels.value) {
    try {
      const res = await agentAPI.backend.getActiveModels()
      models.value = res.models || []
      const status = await agentAPI.backend.getStatus()
      currentProvider.value = status.provider || ''
      currentModel.value = status.model || ''
    } catch { models.value = [] }
  }
  showModels.value = !showModels.value
}

const switchModel = async (m) => {
  showModels.value = false
  try {
    await agentAPI.backend.updateConfig({ provider: m.provider, model: m.model, api_key: m.api_key, api_base: m.api_base })
    currentProvider.value = m.provider
    currentModel.value = m.model
  } catch {}
}

onMounted(() => { scrollDown() })
</script>

<style scoped>
.widget-panel { display: flex; flex-direction: column; height: 100%; width: 100%; overflow: hidden; }
.widget-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; }
.widget-title { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #1d1d1f; }
.header-right { display: flex; align-items: center; gap: 4px; }
.new-chat-btn { width: 22px; height: 22px; border: none; border-radius: 5px; background: transparent; cursor: pointer; font-size: 16px; color: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; line-height: 1; }
.new-chat-btn:hover { background: rgba(0,0,0,0.06); color: #1d1d1f; }
.widget-close { width: 22px; height: 22px; border: none; border-radius: 5px; background: transparent; cursor: pointer; font-size: 13px; color: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; }
.widget-close:hover { background: rgba(0,0,0,0.06); color: #ff3b30; }

/* chat list */
.chat-list-bar { display: flex; align-items: center; justify-content: space-between; padding: 6px 12px; font-size: 11px; color: rgba(0,0,0,0.4); cursor: pointer; border-bottom: 1px solid rgba(0,0,0,0.04); flex-shrink: 0; }
.chat-list-bar:hover { background: rgba(0,0,0,0.02); }
.chat-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arrow { flex-shrink: 0; transition: transform 0.2s; }
.arrow.open { transform: rotate(180deg); }

.chat-list-drop { max-height: 120px; overflow-y: auto; border-bottom: 1px solid rgba(0,0,0,0.04); flex-shrink: 0; }
.chat-item { display: flex; align-items: center; padding: 5px 12px; font-size: 11px; cursor: pointer; }
.chat-item:hover { background: rgba(0,0,0,0.03); }
.chat-item.active { background: rgba(0,122,255,0.06); font-weight: 600; }
.chat-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn { background: none; border: none; color: rgba(0,0,0,0.2); cursor: pointer; font-size: 14px; padding: 0 4px; }
.del-btn:hover { color: #ff3b30; }

/* messages */
.chat-body { flex: 1; overflow-y: auto; padding: 8px 12px; display: flex; flex-direction: column; gap: 6px; }
.placeholder { color: rgba(0,0,0,0.3); font-size: 12px; text-align: center; padding: 20px 0; }
.msg { padding: 6px 8px; border-radius: 7px; font-size: 11px; line-height: 1.4; max-width: 85%; word-break: break-word; }
.msg.user { background: #007aff; color: #fff; align-self: flex-end; }
.msg.assistant { background: rgba(0,0,0,0.04); color: #1d1d1f; align-self: flex-start; }
.thinking { display: flex; gap: 3px; padding: 2px 0; }
.dot { width: 5px; height: 5px; border-radius: 50%; background: rgba(0,0,0,0.2); animation: pulse 1.4s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes pulse { 0%,80%,100% { opacity: 0.2; } 40% { opacity: 1; } }

/* input */
.chat-input-row { display: flex; gap: 4px; padding: 6px 10px; border-top: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; align-items: flex-end; }

.model-pick { position: relative; flex-shrink: 0; }
.model-label { display: block; padding: 4px 6px; font-size: 10px; color: rgba(0,0,0,0.4); background: rgba(0,0,0,0.04); border-radius: 4px; cursor: pointer; white-space: nowrap; }
.model-label:hover { background: rgba(0,0,0,0.08); }
.model-drop { position: absolute; bottom: 100%; left: 0; margin-bottom: 4px; background: #fff; border: 1px solid rgba(0,0,0,0.1); border-radius: 6px; box-shadow: 0 4px 16px rgba(0,0,0,0.1); z-index: 50; min-width: 120px; max-height: 160px; overflow-y: auto; }
.model-item { padding: 4px 10px; font-size: 10px; cursor: pointer; white-space: nowrap; }
.model-item:hover { background: rgba(0,0,0,0.04); }
.model-item.active { background: rgba(0,122,255,0.06); font-weight: 600; }

.chat-input { flex: 1; padding: 5px 7px; border: 1px solid rgba(0,0,0,0.1); border-radius: 6px; font-size: 11px; outline: none; font-family: inherit; resize: none; background: rgba(255,255,255,0.8); color: #1d1d1f; }
.chat-input:focus { border-color: #007aff; background: #fff; }
.send-btn { width: 28px; height: 28px; background: #007aff; color: #fff; border: none; border-radius: 6px; font-size: 14px; font-weight: 700; cursor: pointer; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
.send-btn:hover { background: #0062cc; }
.send-btn:disabled { background: #a0c4ff; cursor: not-allowed; }
</style>
