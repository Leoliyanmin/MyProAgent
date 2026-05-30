<template>
  <div class="widget-panel">
    <div class="widget-header">
      <span class="widget-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/></svg>
        Agent
      </span>
      <div class="header-right">
        <button class="header-btn" type="button" title="收回到侧边栏" @click="retractToSidebar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <button class="header-btn" type="button" title="新对话" @click="chat.createNewChat(isTempMode)">+</button>
        <button class="header-btn close-btn" type="button" title="关闭" @click="close">×</button>
      </div>
    </div>

    <div class="chat-list-bar" @click="showChats = !showChats">
      <span class="chat-title">{{ currentChatTitle }}</span>
      <svg class="arrow" :class="{ open: showChats }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
    </div>
    <div v-if="showChats" class="chat-list-drop">
      <div
        v-for="c in chat.chatList"
        :key="c.id"
        class="chat-item"
        :class="{ active: c.id === chat.currentChatId }"
        @click="switchToChat(c.id)"
      >
        <span class="chat-name">{{ c.title }}</span>
        <span v-if="c.isTemporary" class="temp-tag">临时</span>
        <button class="del-btn" type="button" @click.stop="chat.deleteChat(c.id)">×</button>
      </div>
    </div>

    <div class="chat-body" ref="msgContainer">
      <div v-if="chat.safeMessages.length === 0 && !chat.isThinking" class="placeholder">输入消息开始对话...</div>
      <div v-for="(msg, idx) in chat.safeMessages" :key="idx" class="msg" :class="msg.role">
        <div v-for="(segment, si) in chat.parseMessage(msg.text)" :key="si">
          <div v-if="segment.type === 'text'" class="msg-text markdown-body" v-html="chat.renderMarkdown(segment.content)"></div>
          <ThemeSuggestionWidget
            v-else-if="segment.type === 'theme-suggestion'"
            :tokens="segment.tokens"
            :initially-dismissed="chat.isThemeDismissed(chat.currentChatId, idx)"
            @accept="chat.applyThemeSuggestion(segment.tokens); chat.markThemeDismissed(chat.currentChatId, idx)"
            @dismiss="chat.markThemeDismissed(chat.currentChatId, idx)"
          />
          <DeleteConfirmWidget
            v-else-if="segment.type === 'delete-confirm'"
            :files="segment.files"
            :working-directory="chat.fmStore.workingDirectory"
            @confirm="chat.onDeleteConfirmed(idx, segment.files)"
            @dismiss="chat.onDeleteDismissed(idx)"
          />
        </div>
      </div>
      <div v-if="chat.isThinking" class="thinking-indicator">
        <span class="thinking-dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
        <span class="thinking-text">{{ chat.currentToolLabel || 'Agent 正在思考' }}</span>
      </div>
    </div>

    <div class="chat-input-row">
      <div class="model-pick" ref="modelRef" @click.stop="toggleModels">
        <span class="model-label" :title="chat.currentModelLabel">{{ compactModelLabel }}</span>
        <div v-if="showModels" class="model-drop">
          <div v-if="chat.activeModels.length === 0" class="model-empty">暂无可用模型</div>
          <div
            v-for="m in chat.activeModels"
            :key="`${m.provider}:${m.model}`"
            class="model-item"
            :class="{ active: chat.currentProvider === m.provider && chat.currentModel === m.model }"
            @click.stop="switchModel(m)"
          >{{ m.provider }}/{{ m.model }}</div>
        </div>
      </div>
      <div class="input-wrapper">
        <textarea
          v-model="chat.inputText"
          class="chat-input"
          rows="2"
          :disabled="chat.isSending"
          @keydown.enter.exact="onEnterKey"
          @compositionstart="chat.onCompositionStart"
          @compositionend="chat.onCompositionEnd"
        ></textarea>
      </div>
      <div class="send-area">
        <label class="temp-toggle" title="临时对话（7 天后自动清理）">
          <input v-model="isTempMode" type="checkbox" />
          <span class="temp-label">临时</span>
        </label>
        <button v-if="!chat.isSending && !chat.isThinking" class="send-btn" type="button" :disabled="!chat.inputText.trim()" @click="chat.sendMessage">↑</button>
        <button v-else class="stop-btn" type="button" @click="chat.stopGenerating">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useAgentChat } from '../../composables/useAgentChat.js'
import { useDashboardStore } from '../../stores/dashboard.js'
import ThemeSuggestionWidget from '../agent/ThemeSuggestionWidget.vue'
import DeleteConfirmWidget from '../agent/DeleteConfirmWidget.vue'

const dashboardStore = useDashboardStore()
const chat = useAgentChat('dashboard-agent')

const showChats = ref(false)
const showModels = ref(false)
const modelRef = ref(null)
const msgContainer = ref(null)
const isTempMode = ref(false)

const currentChatTitle = computed(() => {
  const c = chat.chatList.find(item => item.id === chat.currentChatId)
  return c?.title || '对话'
})

const compactModelLabel = computed(() => {
  if (!chat.currentModel || chat.activeModels.length === 0) return chat.currentModelLabel
  const model = String(chat.currentModel)
  const suffix = model.split('/').pop() || model
  const parts = suffix.split('-').filter(Boolean)
  if (parts.length >= 2) return parts.slice(-2).join('-')
  return suffix.length > 12 ? `...${suffix.slice(-12)}` : suffix
})

const close = () => dashboardStore.toggleMiniWidget('agent')

const retractToSidebar = () => {
  window.dispatchEvent(new CustomEvent('agent-retract-to-sidebar'))
}

const switchToChat = (id) => {
  chat.switchChat(id)
  showChats.value = false
}

const scrollDown = () => {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
}

const toggleModels = async () => {
  if (!showModels.value) await chat.loadActiveModels()
  showModels.value = !showModels.value
}

const switchModel = async (modelConfig) => {
  showModels.value = false
  await chat.switchModel(modelConfig)
}

const onEnterKey = (event) => {
  if (chat.isImeEnter(event)) return
  event.preventDefault()
  chat.sendMessage()
}

const handleClickOutside = (event) => {
  if (modelRef.value && !modelRef.value.contains(event.target)) showModels.value = false
}

const handlePopToDashboard = () => {
  chat.connectWebSocket()
}

chat.setScrollContainer(scrollDown)
chat.init()

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('agent-pop-to-dashboard', handlePopToDashboard)
  scrollDown()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('agent-pop-to-dashboard', handlePopToDashboard)
  chat.cleanup()
})
</script>

<style scoped>
.widget-panel { display: flex; flex-direction: column; height: 100%; width: 100%; overflow: hidden; }
.widget-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid rgba(0,0,0,.06); flex-shrink: 0; }
.widget-title { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #1d1d1f; }
.header-right { display: flex; align-items: center; gap: 2px; }
.header-btn { width: 24px; height: 24px; border: none; border-radius: 6px; background: transparent; color: rgba(0,0,0,.42); cursor: pointer; display: flex; align-items: center; justify-content: center; }
.header-btn:hover { background: rgba(0,0,0,.06); color: #1d1d1f; }
.close-btn:hover { color: #ff3b30; }
.chat-list-bar { display: flex; align-items: center; justify-content: space-between; padding: 5px 12px; font-size: 11px; color: rgba(0,0,0,.45); border-bottom: 1px solid rgba(0,0,0,.04); cursor: pointer; flex-shrink: 0; }
.chat-title { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arrow { transition: transform .2s; flex-shrink: 0; }
.arrow.open { transform: rotate(180deg); }
.chat-list-drop { max-height: 120px; overflow-y: auto; border-bottom: 1px solid rgba(0,0,0,.04); flex-shrink: 0; }
.chat-item { display: flex; align-items: center; gap: 5px; padding: 5px 12px; font-size: 11px; cursor: pointer; }
.chat-item:hover { background: rgba(0,0,0,.04); }
.chat-item.active { background: rgba(0,122,255,.08); font-weight: 600; }
.chat-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.temp-tag { font-size: 9px; color: #6b7280; background: rgba(0,0,0,.06); border-radius: 4px; padding: 1px 4px; }
.del-btn { border: none; background: none; color: rgba(0,0,0,.25); cursor: pointer; }
.del-btn:hover { color: #ff3b30; }
.chat-body { flex: 1; min-height: 0; overflow-y: auto; padding: 8px 12px; display: flex; flex-direction: column; gap: 7px; }
.placeholder { color: rgba(0,0,0,.32); font-size: 12px; text-align: center; padding: 20px 0; }
.msg { max-width: 90%; padding: 6px 8px; border-radius: 8px; font-size: 11px; line-height: 1.45; word-break: break-word; }
.msg.user { align-self: flex-end; background: #007aff; color: #fff; }
.msg.assistant, .msg.agent { align-self: flex-start; background: rgba(0,0,0,.045); color: #1d1d1f; }
.msg.tool { align-self: flex-start; background: transparent; color: #6b7280; padding: 2px 8px; font-size: 10px; }
.markdown-body :deep(p) { margin: 0 0 4px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul) { margin: 4px 0 8px; padding-left: 0; list-style: none; }
.markdown-body :deep(li) { position: relative; margin: 3px 0; padding-left: 14px; }
.markdown-body :deep(li::before) { content: ''; position: absolute; left: 2px; top: 0.78em; width: 4px; height: 4px; border-radius: 50%; background: rgba(0,0,0,.32); transform: translateY(-50%); }
.markdown-body :deep(li > p) { display: inline; margin: 0; }
.markdown-body :deep(pre) { white-space: pre-wrap; background: #f5f5f7; border-radius: 6px; padding: 6px; overflow-x: auto; }
.thinking-indicator { display: flex; align-items: center; gap: 6px; padding: 4px 8px; color: rgba(0,0,0,.45); }
.thinking-dots { display: inline-flex; gap: 3px; }
.dot { width: 5px; height: 5px; border-radius: 50%; background: rgba(0,122,255,.65); animation: pulse 1.4s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
@keyframes pulse { 0%,80%,100% { opacity: .2; } 40% { opacity: 1; } }
.chat-input-row { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 7px; padding: 6px 10px; border-top: 1px solid rgba(0,0,0,.06); flex-shrink: 0; align-items: stretch; }
.model-pick { position: relative; flex-shrink: 0; }
.model-label { display: flex; align-items: center; width: 100%; height: 100%; min-height: 38px; box-sizing: border-box; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 0 7px; font-size: 11px; color: rgba(0,0,0,.48); background: rgba(0,0,0,.04); border-radius: 8px; cursor: pointer; }
.model-drop { position: absolute; bottom: calc(100% + 5px); left: 0; min-width: 150px; max-height: 160px; overflow-y: auto; border: 1px solid rgba(0,0,0,.1); border-radius: 7px; background: #fff; box-shadow: 0 8px 22px rgba(0,0,0,.14); z-index: 40; padding: 4px; }
.model-empty, .model-item { padding: 5px 8px; border-radius: 5px; font-size: 10px; white-space: nowrap; }
.model-empty { color: #9ca3af; text-align: center; }
.model-item { cursor: pointer; }
.model-item:hover { background: rgba(0,0,0,.04); }
.model-item.active { background: rgba(0,122,255,.08); font-weight: 600; }
.input-wrapper { flex: 1; min-width: 0; }
.chat-input { width: 100%; min-height: 38px; height: 38px; box-sizing: border-box; padding: 7px 9px; border: 1px solid rgba(0,0,0,.12); border-radius: 10px; font-size: 12px; line-height: 16px; outline: none; font-family: inherit; resize: none; overflow-y: auto; background: rgba(255,255,255,.85); color: #1d1d1f; }
.chat-input:focus { border-color: #007aff; box-shadow: 0 0 0 2px rgba(0,122,255,.15); background: #fff; }
.send-area { display: flex; align-items: stretch; gap: 6px; flex-shrink: 0; }
.temp-toggle { display: inline-flex; align-items: center; cursor: pointer; }
.temp-toggle input { display: none; }
.temp-label { display: flex; align-items: center; justify-content: center; height: 100%; min-height: 38px; box-sizing: border-box; font-size: 11px; color: rgba(0,0,0,.42); border-radius: 8px; padding: 0 8px; background: rgba(0,0,0,.04); }
.temp-toggle input:checked + .temp-label { color: #007aff; background: rgba(0,122,255,.1); font-weight: 600; }
.send-btn { width: 40px; min-height: 38px; border-radius: 10px; border: none; background: #007aff; color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; }
.send-btn:hover { background: #0062cc; }
.send-btn:disabled { background: #a0c4ff; cursor: not-allowed; }
.stop-btn { width: 40px; min-height: 38px; border-radius: 10px; border: 1px solid rgba(255,59,48,.3); background: rgba(255,59,48,.1); color: #ff3b30; display: flex; align-items: center; justify-content: center; cursor: pointer; }
</style>
