<template>
  <aside class="macos-sidebar right-sidebar agent-panel" :class="{ 'is-collapsed': !isOpen }">
    <div class="agent-header">
      <div class="agent-header-left">
        <span class="font-semibold">Agent 助手</span>
        <span v-if="chat.fmStore.isDirectorySet" class="fm-badge" :title="'工作目录: ' + chat.fmStore.workingDirectory">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          {{ shortDir }}
        </span>
      </div>
      <div class="agent-header-right">
        <button class="icon-btn" type="button" title="弹出到仪表板" @click="popToDashboard">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/><path d="M21 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h6"/></svg>
        </button>
        <button class="icon-btn" type="button" title="收起 Agent 助手" @click="emit('toggleFromSelf')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>
    </div>

    <div class="chat-list-section" :class="{ 'is-collapsed': chatListCollapsed }">
      <div class="chat-list-header" @click="chatListCollapsed = !chatListCollapsed">
        <div class="chat-list-header-left">
          <svg class="chat-list-toggle-icon" :class="{ 'is-rotated': chatListCollapsed }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          <span class="chat-list-title">聊天记录</span>
        </div>
        <button class="new-chat-btn" type="button" title="新建对话" @click.stop="chat.createNewChat(false)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新对话
        </button>
      </div>
      <div class="chat-list">
        <div
          v-for="c in chat.chatList"
          :key="c.id"
          class="chat-item"
          :class="{ active: chat.currentChatId === c.id }"
          @click="chat.switchChat(c.id)"
        >
          <svg class="chat-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <div class="chat-info">
            <div class="chat-title">{{ c.title }}</div>
            <div class="chat-time">{{ chat.formatTime(c.updatedAt) }}</div>
          </div>
          <span v-if="c.isTemporary" class="chat-temp-badge">临时</span>
          <button class="delete-chat-btn" type="button" title="删除" @click.stop="chat.deleteChat(c.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <div v-if="chat.chatList.length === 0" class="chat-empty">暂无聊天记录，点击"新对话"开始</div>
      </div>
    </div>

    <div class="dialog-section">
      <div class="messages-list" ref="messagesContainer">
        <div v-for="(msg, idx) in chat.safeMessages" :key="idx" class="message" :class="[msg.role]">
          <div v-for="(segment, si) in chat.parseMessage(msg.text)" :key="si">
            <div v-if="segment.type === 'text'" class="message-content markdown-body" v-html="chat.renderMarkdown(segment.content)"></div>
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
        <div v-if="chat.safeMessages.length === 0 && !chat.isThinking" class="placeholder-text">在这里与 Agent 对话...</div>
        <div v-if="chat.isThinking" class="thinking-indicator">
          <span class="thinking-dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
          <span class="thinking-text">{{ chat.currentToolLabel || 'Agent 正在思考' }}</span>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="chat.inputText"
          class="message-input"
          placeholder="输入你的问题... (Shift+Enter 换行)"
          rows="3"
          @keydown.enter.exact="onEnterKeyDown"
          @compositionstart="chat.onCompositionStart"
          @compositionend="chat.onCompositionEnd"
        ></textarea>
        <div class="input-actions">
          <div class="model-selector" ref="modelSelectorRef" @click.stop="toggleModelDropdown">
            <span class="model-selector-label">{{ chat.currentModelLabel }}</span>
            <svg class="model-selector-arrow" :class="{ open: showModelDropdown }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
            <div v-if="showModelDropdown" class="model-dropdown">
              <div v-if="chat.activeModels.length === 0" class="model-dropdown-empty">暂无可用模型</div>
              <div
                v-for="m in chat.activeModels"
                :key="`${m.provider}:${m.model}`"
                class="model-dropdown-item"
                :class="{ active: chat.currentProvider === m.provider && chat.currentModel === m.model }"
                @click.stop="switchModel(m)"
              >
                <span class="model-dropdown-name">{{ m.provider }} / {{ m.model }}</span>
                <span v-if="chat.currentProvider === m.provider && chat.currentModel === m.model" class="model-dropdown-check">✓</span>
              </div>
            </div>
          </div>
          <button v-if="!chat.isSending && !chat.isThinking" class="send-btn" type="button" @click.prevent="chat.sendMessage">发送</button>
          <button v-else class="stop-btn" type="button" @click.prevent="chat.stopGenerating">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
            停止
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="chat.noKeyModalVisible" class="no-key-modal-mask" @click.self="chat.chatStore.dismissNoKeyModal">
        <div class="no-key-modal" role="dialog" aria-modal="true" aria-label="未配置 API Key">
          <h3 class="no-key-modal-title">未配置 API Key</h3>
          <p class="no-key-modal-body">当前没有可用的 AI 服务密钥，请前往用户设置绑定 API Key。</p>
          <div class="no-key-modal-actions">
            <button class="no-key-modal-btn primary" type="button" @click.stop.prevent="goToSettings">去设置</button>
            <button class="no-key-modal-btn ghost" type="button" @click.stop.prevent="chat.chatStore.dismissNoKeyModal">取消</button>
          </div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useAgentChat } from '../../composables/useAgentChat.js'
import ThemeSuggestionWidget from '../agent/ThemeSuggestionWidget.vue'
import DeleteConfirmWidget from '../agent/DeleteConfirmWidget.vue'

defineProps({
  isOpen: { type: Boolean, default: true }
})
const emit = defineEmits(['toggleFromSelf'])

const chat = useAgentChat('sidebar')
const messagesContainer = ref(null)
const modelSelectorRef = ref(null)
const showModelDropdown = ref(false)
const chatListCollapsed = ref(false)

const shortDir = computed(() => {
  const dir = chat.fmStore.workingDirectory
  if (!dir) return ''
  const parts = dir.replace(/\/+$/, '').split('/')
  return parts.length > 2 ? '.../' + parts.slice(-2).join('/') : dir
})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
}

const onEnterKeyDown = (event) => {
  if (chat.isImeEnter(event)) return
  event.preventDefault()
  chat.sendMessage()
}

const toggleModelDropdown = async () => {
  if (!showModelDropdown.value) await chat.loadActiveModels()
  showModelDropdown.value = !showModelDropdown.value
}

const switchModel = async (modelConfig) => {
  showModelDropdown.value = false
  await chat.switchModel(modelConfig)
}

const handleClickOutside = (event) => {
  if (modelSelectorRef.value && !modelSelectorRef.value.contains(event.target)) {
    showModelDropdown.value = false
  }
}

const popToDashboard = () => {
  window.dispatchEvent(new CustomEvent('agent-pop-to-dashboard'))
}

const goToSettings = async () => {
  chat.chatStore.dismissNoKeyModal()
  await chat.router.push('/user-settings')
}

chat.setScrollContainer(scrollToBottom)
chat.init()

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('agent-api-keys-changed', chat.loadActiveModels)
  scrollToBottom()
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('agent-api-keys-changed', chat.loadActiveModels)
  chat.cleanup()
})
</script>

<style scoped>
.right-sidebar { width: 320px; flex-shrink: 0; background-color: var(--clr-bg-agent, rgba(235,235,235,.65)); border-left: 1px solid rgba(0,0,0,.08); display: flex; flex-direction: column; overflow: hidden; transition: width .2s ease; }
.right-sidebar.is-collapsed { width: 0; border-left: none; }
.agent-header { height: 52px; border-bottom: 1px solid rgba(0,0,0,.08); display: flex; align-items: center; justify-content: space-between; padding: 0 16px; font-size: 14px; font-weight: 600; flex-shrink: 0; }
.agent-header-left, .agent-header-right { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fm-badge { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 500; color: rgba(0,0,0,.55); background: rgba(0,122,255,.08); padding: 2px 7px; border-radius: 4px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.icon-btn { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 6px; background: #fff; border: 1px solid rgba(0,0,0,.12); cursor: pointer; color: #111827; }
.icon-btn:hover { background: rgba(0,122,255,.08); color: #007aff; }
.chat-list-section { border-bottom: 1px solid rgba(0,0,0,.08); flex-shrink: 0; max-height: 220px; display: flex; flex-direction: column; transition: max-height .2s ease; }
.chat-list-section.is-collapsed { max-height: 36px; }
.chat-list-header { height: 36px; padding: 0 12px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; flex-shrink: 0; }
.chat-list-header-left { display: flex; align-items: center; gap: 6px; color: #6b7280; font-size: 12px; font-weight: 600; }
.chat-list-toggle-icon { transition: transform .2s ease; }
.chat-list-toggle-icon.is-rotated { transform: rotate(-90deg); }
.new-chat-btn { display: inline-flex; align-items: center; gap: 4px; border: 1px solid rgba(0,0,0,.12); border-radius: 6px; background: #fff; padding: 4px 8px; font-size: 12px; cursor: pointer; }
.chat-list { overflow-y: auto; padding: 4px 8px 8px; }
.chat-item { display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 8px; cursor: pointer; }
.chat-item:hover { background: rgba(0,0,0,.04); }
.chat-item.active { background: rgba(0,122,255,.09); }
.chat-icon, .delete-chat-btn { flex-shrink: 0; }
.chat-info { min-width: 0; flex: 1; }
.chat-title { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-time { font-size: 11px; color: #86868b; }
.chat-temp-badge { font-size: 10px; color: #6b7280; background: rgba(0,0,0,.06); border-radius: 4px; padding: 2px 4px; }
.delete-chat-btn { border: none; background: transparent; color: #9ca3af; cursor: pointer; }
.delete-chat-btn:hover { color: #ff3b30; }
.chat-empty { text-align: center; color: #9ca3af; font-size: 12px; padding: 16px 0; }
.dialog-section { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.messages-list { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.message { max-width: 90%; padding: 9px 11px; border-radius: 10px; font-size: 13px; line-height: 1.5; word-break: break-word; }
.message.user { align-self: flex-end; background: #007aff; color: #fff; }
.message.assistant, .message.agent { align-self: flex-start; background: rgba(255,255,255,.72); color: #1d1d1f; border: 1px solid rgba(0,0,0,.06); }
.message.tool { align-self: flex-start; padding: 4px 10px; color: #6b7280; background: transparent; font-size: 12px; }
.markdown-body :deep(p) { margin: 0 0 6px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul) { margin: 4px 0 8px; padding-left: 0; list-style: none; }
.markdown-body :deep(li) { position: relative; margin: 3px 0; padding-left: 14px; }
.markdown-body :deep(li::before) { content: ''; position: absolute; left: 2px; top: 0.78em; width: 4px; height: 4px; border-radius: 50%; background: rgba(0,0,0,.32); transform: translateY(-50%); }
.markdown-body :deep(li > p) { display: inline; margin: 0; }
.markdown-body :deep(pre) { white-space: pre-wrap; background: #f5f5f7; border-radius: 8px; padding: 8px; overflow-x: auto; }
.placeholder-text { margin: auto; color: #9ca3af; font-size: 13px; }
.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 4px; color: #6b7280; font-size: 13px; }
.thinking-dots { display: inline-flex; gap: 4px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #007aff; animation: pulse 1.4s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }
@keyframes pulse { 0%,80%,100% { opacity: .25; transform: scale(.8); } 40% { opacity: 1; transform: scale(1.1); } }
.input-area { border-top: 1px solid rgba(0,0,0,.08); padding: 12px; flex-shrink: 0; }
.message-input { width: 100%; box-sizing: border-box; resize: none; border: 1px solid rgba(0,0,0,.12); border-radius: 10px; padding: 9px 11px; font-size: 13px; font-family: inherit; outline: none; background: rgba(255,255,255,.8); }
.message-input:focus { border-color: #007aff; background: #fff; box-shadow: 0 0 0 2px rgba(0,122,255,.16); }
.input-actions { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 8px; }
.model-selector { position: relative; display: inline-flex; align-items: center; gap: 5px; min-width: 0; max-width: 190px; padding: 5px 9px; border: 1px solid rgba(0,0,0,.12); border-radius: 7px; background: #fff; font-size: 11px; cursor: pointer; }
.model-selector-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.model-selector-arrow { transition: transform .2s; flex-shrink: 0; }
.model-selector-arrow.open { transform: rotate(180deg); }
.model-dropdown { position: absolute; bottom: calc(100% + 6px); left: 0; min-width: 220px; max-height: 220px; overflow-y: auto; border: 1px solid rgba(0,0,0,.1); border-radius: 8px; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,.14); z-index: 20; padding: 4px; }
.model-dropdown-empty, .model-dropdown-item { padding: 8px 10px; border-radius: 6px; font-size: 12px; }
.model-dropdown-empty { color: #9ca3af; text-align: center; }
.model-dropdown-item { display: flex; justify-content: space-between; gap: 8px; cursor: pointer; }
.model-dropdown-item:hover { background: rgba(0,0,0,.04); }
.model-dropdown-item.active { background: rgba(0,122,255,.09); font-weight: 600; }
.model-dropdown-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.send-btn, .stop-btn { display: inline-flex; align-items: center; gap: 5px; border-radius: 8px; padding: 7px 14px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid rgba(0,0,0,.12); background: #fff; color: #1d1d1f; }
.send-btn:hover { background: #f5f5f7; }
.stop-btn { color: #ff3b30; border-color: rgba(255,59,48,.3); background: rgba(255,59,48,.08); }
.no-key-modal-mask { position: fixed; inset: 0; background: rgba(17,24,39,.32); display: flex; align-items: center; justify-content: center; z-index: 200; }
.no-key-modal { width: min(380px, calc(100vw - 32px)); border-radius: 14px; border: 1px solid rgba(0,0,0,.12); background: #fff; box-shadow: 0 18px 48px rgba(0,0,0,.2); padding: 22px; }
.no-key-modal-title { margin: 0 0 10px; font-size: 17px; font-weight: 700; }
.no-key-modal-body { margin: 0 0 18px; font-size: 13px; color: #6b7280; line-height: 1.5; }
.no-key-modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
.no-key-modal-btn { padding: 8px 14px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid rgba(0,0,0,.16); background: #fff; }
.no-key-modal-btn.primary { background: #007aff; border-color: #007aff; color: #fff; }
</style>
