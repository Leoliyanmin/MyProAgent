<template>
  <div class="agent-settings">
    <header class="as-header">
      <div>
        <h1 class="as-title">Agent 设置</h1>
        <p class="as-subtitle">配置 AI 模型和 API 密钥</p>
      </div>
      <button class="as-btn as-btn--test" @click="testConnection" :disabled="isTesting">
        <svg v-if="!isTesting" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        {{ isTesting ? '测试中...' : '测试连接' }}
      </button>
    </header>

    <div class="as-content">
      <div class="as-section">
        <h2 class="as-section-title">当前配置</h2>
        <div class="as-status-card">
          <div class="as-status-item">
            <span class="as-status-label">Provider</span>
            <span class="as-status-value">{{ status.provider || '未知' }}</span>
          </div>
          <div class="as-status-item">
            <span class="as-status-label">Model</span>
            <span class="as-status-value">{{ status.model || '未知' }}</span>
          </div>
          <div class="as-status-item">
            <span class="as-status-label">API Base</span>
            <span class="as-status-value as-status-value--truncate">{{ status.api_base || '未知' }}</span>
          </div>
          <div class="as-status-item">
            <span class="as-status-label">API Key</span>
            <span class="as-status-value">{{ status.api_key || '未设置' }}</span>
          </div>
        </div>
      </div>

      <div class="as-section">
        <h2 class="as-section-title">更新配置</h2>

        <div class="as-form">
          <div class="as-form-group">
            <label class="as-label">Provider</label>
            <select
              class="as-input as-input--select"
              v-model="form.provider"
              @change="onProviderChange"
            >
              <option value="">-- 选择 Provider --</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="openai">OpenAI</option>
              <option value="openrouter">OpenRouter</option>
              <option value="deepseek">DeepSeek</option>
              <option value="groq">Groq</option>
              <option value="zhipu">智谱 AI (GLM)</option>
              <option value="moonshot">Moonshot</option>
              <option value="gemini">Google Gemini</option>
            </select>
            <p class="as-hint">选择 LLM 服务提供商</p>
          </div>

          <div class="as-form-group">
            <label class="as-label">Model</label>
            <input
              type="text"
              class="as-input"
              v-model="form.model"
              placeholder="例如: gpt-4o, claude-3-5-sonnet, glm-4.7"
            />
            <p class="as-hint">输入模型名称</p>
          </div>

          <div class="as-form-group">
            <label class="as-label">API Key</label>
            <div class="as-input-wrapper">
              <input
                :type="showApiKey ? 'text' : 'password'"
                class="as-input"
                v-model="form.api_key"
                placeholder="输入 API 密钥"
              />
              <button
                class="as-toggle-btn"
                @click="showApiKey = !showApiKey"
                :title="showApiKey ? '隐藏' : '显示'"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <template v-if="showApiKey">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </template>
                  <template v-else>
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </template>
                </svg>
              </button>
            </div>
            <p class="as-hint">API 密钥将保存在本地配置中</p>
          </div>

          <div class="as-form-group">
            <label class="as-label">API Base URL</label>
            <input
              type="text"
              class="as-input"
              v-model="form.api_base"
              placeholder="例如: https://api.openai.com/v1 (留空使用默认)"
            />
            <p class="as-hint">自定义 API 端点，留空使用默认地址</p>
          </div>

          <div class="as-actions">
            <button class="as-btn as-btn--reset" @click="resetForm">重置</button>
            <button class="as-btn as-btn--save" @click="saveConfig" :disabled="isSaving">
              <svg v-if="!isSaving" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/>
                <polyline points="7 3 7 8 15 8"/>
              </svg>
              {{ isSaving ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="message" class="as-message" :class="`as-message--${message.type}`">
      {{ message.text }}
      <button class="as-message-close" @click="message = null">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { agentAPI } from '../services/api.js'

const status = ref({
  provider: '',
  model: '',
  api_base: '',
  api_key: ''
})

const form = ref({
  provider: '',
  model: '',
  api_key: '',
  api_base: ''
})

const isTesting = ref(false)
const isSaving = ref(false)
const showApiKey = ref(false)
const message = ref(null)

const showMessage = (type, text) => {
  message.value = { type, text }
  setTimeout(() => message.value = null, 3000)
}

const loadStatus = async () => {
  try {
    const data = await agentAPI.backend.getStatus()
    status.value = data
    form.value.provider = data.provider || ''
    form.value.model = data.model || ''
    form.value.api_base = data.api_base || ''
  } catch (error) {
    console.error('Failed to load status:', error)
  }
}

const onProviderChange = () => {
  form.value.api_key = ''
  form.value.api_base = ''
}

const testConnection = async () => {
  isTesting.value = true
  try {
    const data = await agentAPI.backend.testConnection()
    if (data.success) {
      showMessage('success', '连接成功！')
    } else {
      showMessage('error', `连接失败: ${data.error}`)
    }
  } catch (error) {
    showMessage('error', `连接失败: ${error.message}`)
  } finally {
    isTesting.value = false
  }
}

const saveConfig = async () => {
  if (!form.value.provider && !form.value.model && !form.value.api_key && !form.value.api_base) {
    showMessage('error', '请至少填写一项配置')
    return
  }

  isSaving.value = true
  try {
    const data = await agentAPI.backend.updateConfig({
      provider: form.value.provider || undefined,
      model: form.value.model || undefined,
      api_key: form.value.api_key || undefined,
      api_base: form.value.api_base || undefined
    })

    if (data.success) {
      showMessage('success', '配置已保存')
      await loadStatus()
    } else {
      showMessage('error', `保存失败: ${data.message}`)
    }
  } catch (error) {
    showMessage('error', `保存失败: ${error.message}`)
  } finally {
    isSaving.value = false
  }
}

const resetForm = () => {
  form.value = {
    provider: status.value.provider || '',
    model: status.value.model || '',
    api_key: '',
    api_base: status.value.api_base || ''
  }
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.agent-settings {
  width: 100%;
  height: 100%;
  background: var(--clr-bg-card, #ffffff);
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.as-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  background: var(--clr-bg-topbar, #fafafa);
}

.as-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.as-subtitle {
  margin: 3px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.as-btn {
  border: 1px solid rgba(0,0,0,0.15);
  background: #fff;
  border-radius: 7px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s;
}

.as-btn:hover:not(:disabled) {
  background: #f5f5f7;
}

.as-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.as-btn--test {
  border-color: #007aff;
  color: #007aff;
}

.as-btn--test:hover:not(:disabled) {
  background: rgba(0,122,255,0.1);
}

.as-btn--save {
  background: #16a34a;
  color: #fff;
  border-color: #16a34a;
}

.as-btn--save:hover:not(:disabled) {
  background: #15803d;
}

.as-btn--reset {
  border-color: #6b7280;
}

.as-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.as-section {
  background: #f9fafb;
  border-radius: 10px;
  padding: 16px;
}

.as-section-title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.as-status-card {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.as-status-item {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.as-status-label {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
}

.as-status-value {
  font-size: 13px;
  color: #111827;
  font-weight: 500;
  word-break: break-all;
}

.as-status-value--truncate {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.as-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.as-form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.as-label {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
}

.as-input {
  border: 1px solid rgba(0,0,0,0.15);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  background: #fff;
  color: #111827;
  outline: none;
  transition: border-color 0.15s;
}

.as-input:focus {
  border-color: #007aff;
  box-shadow: 0 0 0 3px rgba(0,122,255,0.1);
}

.as-input--select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.as-input-wrapper {
  position: relative;
}

.as-toggle-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  color: #6b7280;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.as-toggle-btn:hover {
  color: #111827;
}

.as-hint {
  margin: 0;
  font-size: 11px;
  color: #9ca3af;
}

.as-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.as-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.as-message--success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.as-message--error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.as-message-close {
  background: transparent;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
