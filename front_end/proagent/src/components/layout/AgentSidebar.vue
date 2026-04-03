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
            <div class="message-content">{{ msg.text }}</div>
          </div>
          <div v-if="messages.length === 0" class="placeholder-text">
            在这里与 Agent 对话...
          </div>
        </div>

        <div class="input-area">
          <textarea
            v-model="inputText"
            class="message-input"
            placeholder="输入你的问题..."
            @keydown.enter.meta="sendMessage"
            rows="3"
          ></textarea>
          <button class="send-btn" @click="sendMessage" type="button">发送</button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  isOpen: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggleFromSelf'])

// Thought Trace 数据
const traceExpanded = ref(true)
const phaseLabel = {
  planning: '📋 规划',
  tool_call: '🔧 工具调用',
  observation: '👁️ 观察',
  result: '✅ 结果'
}

// Mock trace 事件（后期从 Pinia 或 WebSocket 接收真实数据）
const traceEvents = ref([
  { phase: 'planning', summary: '分析用户问题，制定执行计划', durationMs: 120 },
  { phase: 'tool_call', summary: '调用 search_workspace 工具', durationMs: 250 },
  { phase: 'observation', summary: '获取查询结果 3 条', durationMs: 80 }
])

// 对话消息
const messages = ref([
  { role: 'agent', text: 'Hello! 我是 ProAgent 助手，可以帮你分析代码和回答问题。' }
])

const inputText = ref('')

const sendMessage = () => {
  if (!inputText.value.trim()) return
  
  // 用户消息
  messages.value.push({
    role: 'user',
    text: inputText.value
  })
  
  // 模拟 Agent 响应
  setTimeout(() => {
    messages.value.push({
      role: 'agent',
      text: `已收到: "${inputText.value}" (这是演示回复)`
    })
  }, 500)
  
  inputText.value = ''
}
</script>

<style scoped>
/* 右侧侧边栏核心容器样式 */
.right-sidebar {
  width: 300px;
  flex-shrink: 0;
  background: var(--clr-bg-agent, rgba(235, 235, 235, 0.65));
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
</style>