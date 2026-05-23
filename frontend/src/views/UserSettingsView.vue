<template>
  <section class="settings-shell">
    <header class="settings-header">
      <h1 class="settings-title">用户设置</h1>
      <p class="settings-subtitle">管理个人资料、邮箱绑定、API Key 与外部账号</p>
    </header>

    <div class="settings-grid">
      <article class="panel">
        <h2 class="panel-title">个人资料</h2>
        <div class="field-row">
          <label class="field-label" for="displayName">姓名</label>
          <div class="field-inline">
            <input
              id="displayName"
              v-model.trim="profile.name"
              class="text-input"
              type="text"
              placeholder="请输入姓名"
            />
            <button class="action-btn" type="button" @click="saveName">保存姓名</button>
            <!-- 修改密码功能暂未实现后端接口，暂时隐藏 -->
            <!-- <button class="action-btn ghost" type="button" @click="openPasswordModal">修改密码</button> -->
          </div>
          <p v-if="nameNotice" class="status-text" :class="`status-${nameNoticeType}`">{{ nameNotice }}</p>
        </div>
      </article>

      <article class="panel">
        <h2 class="panel-title">邮箱绑定</h2>
        <p class="binding-meta binding-hint" style="margin-bottom: 8px;">仅支持腾讯企业邮箱（如 @mail.sustech.edu.cn）</p>

        <template v-if="email.status === 'loading'">
          <p class="binding-meta">加载中…</p>
        </template>
        <template v-else-if="email.status === 'bound'">
          <ul class="binding-list">
            <li class="binding-item">
              <div class="binding-main">
                <p class="binding-title">{{ email.emailAddress }}</p>
                <p class="binding-meta" v-if="email.bindTime">绑定时间：{{ email.bindTime }}</p>
                <p class="binding-meta" v-if="email.lastSyncTime">上次同步：{{ email.lastSyncTime }}</p>
              </div>
              <div class="action-group">
                <button class="action-btn ghost" type="button" @click="syncEmail">同步</button>
                <button class="text-btn" type="button" @click="unbindEmail">解绑</button>
              </div>
            </li>
          </ul>
        </template>
        <template v-else>
          <div class="email-bind-form">
            <input v-model="emailForm.email" class="text-input" type="email" placeholder="企业邮箱地址（如 xxx@mail.sustech.edu.cn）" />
            <input v-model="emailForm.password" class="text-input" type="password" placeholder="客户端专用密码（非登录密码）" />
            <p class="binding-meta binding-hint">获取方式：登录邮箱网页版 → 设置 → 客户端专用密码 → 生成</p>
            <button class="action-btn" type="button" @click="bindEmail">绑定邮箱</button>
          </div>
        </template>
      </article>

      <article class="panel">
        <h2 class="panel-title">AI 服务 API Key</h2>
        
        <!-- 添加按钮 -->
        <div style="margin-bottom:12px;">
          <button class="action-btn ghost" type="button" @click="showAddKeyModal = true">+ 添加 API Key</button>
        </div>

        <!-- 空态 -->
        <p v-if="apiKeys.length === 0 && !loadingKeys" class="binding-meta">暂无已配置的 API Key</p>
        <p v-if="loadingKeys" class="binding-meta">加载中...</p>

        <!-- 已绑定列表 -->
        <ul class="binding-list">
          <li v-for="item in apiKeys" :key="item.provider" class="binding-item">
            <div class="binding-main">
              <p class="binding-title">{{ item.provider }}</p>
              <p v-if="item.model" class="binding-meta" style="font-size:11px;color:#6b7280;">模型: {{ item.model }}</p>
              <p class="binding-meta" :class="item.last_test_success === true ? 'binding-success' : item.last_test_success === false ? 'status-error' : ''">
                {{ item.last_test_success === true ? '● 已连接' : item.last_test_success === false ? '✕ 连接失败' : '○ 未测试' }}
              </p>
              <p class="binding-meta">{{ item.api_key_masked }}</p>
              <p class="binding-meta" style="font-size:11px;color:#9ca3af;">{{ item.api_base }}</p>
            </div>
            <div class="action-group">
              <label class="toggle-label" :title="item.is_active ? '点击停用' : '点击激活'" style="display:flex;align-items:center;gap:4px;cursor:pointer;">
                <span style="font-size:11px;color:#6b7280;">{{ item.is_active ? '已激活' : '未激活' }}</span>
                <div class="toggle-switch" :class="{ active: item.is_active }" @click="toggleApiKey(item.provider)">
                  <div class="toggle-knob"></div>
                </div>
              </label>
              <button class="text-btn" type="button" @click="startEditKey(item)">编辑</button>
              <button class="text-btn" type="button" @click="unbindApiKey(item.provider)">解绑</button>
            </div>
          </li>
        </ul>

        <!-- 添加 API Key 弹窗 -->
        <Teleport to="body">
          <div v-if="showAddKeyModal" class="password-modal-mask" @click.self="closeAddKeyModal">
            <div class="password-modal" role="dialog" aria-modal="true" aria-label="添加 API Key">
              <h3 class="password-modal-title">添加 API Key</h3>
              <div class="password-form">
                <label class="field-label">服务商</label>
                <select v-model="addForm.provider" class="text-input">
                  <option value="">选择服务商</option>
                  <option value="deepseek">DeepSeek</option>
                </select>

                <label class="field-label">模型名称</label>
                <select v-if="providerModels[addForm.provider]" v-model="addForm.model" class="text-input">
                  <option value="">选择模型</option>
                  <option v-for="m in providerModels[addForm.provider]" :key="m" :value="m">{{ m }}</option>
                </select>
                <input v-else v-model.trim="addForm.model" class="text-input" type="text" placeholder="例如: deepseek-chat" />

                <label class="field-label">API Key</label>
                <input v-model.trim="addForm.api_key" class="text-input" type="password" placeholder="sk-..." />

                <label class="field-label">API Base URL</label>
                <input v-model.trim="addForm.api_base" class="text-input" type="text" placeholder="https://api.deepseek.com/v1" />

                <p v-if="addNotice" class="password-notice" :class="'status-' + addNoticeType">{{ addNotice }}</p>

                <div class="password-actions">
                  <button class="action-btn" type="button" :disabled="saving || !addTestPassed" @click="submitAddKey">{{ saving ? '保存中...' : '保存' }}</button>
                  <button class="action-btn ghost" type="button" :disabled="saving" @click="testAddKey">测试连接</button>
                  <button class="action-btn ghost" type="button" @click="closeAddKeyModal">取消</button>
                </div>
              </div>
            </div>
          </div>
        </Teleport>

        <!-- 编辑弹窗 -->
        <Teleport to="body">
          <div v-if="editingKey" class="password-modal-mask" @click.self="cancelEditKey">
            <div class="password-modal" role="dialog" aria-modal="true" aria-label="编辑 API Key">
              <h3 class="password-modal-title">编辑 {{ editingKey.provider }}</h3>
              <div class="password-form">
                <label class="field-label">模型名称</label>
                <select v-if="providerModels[editingKey.provider]" v-model="editForm.model" class="text-input">
                  <option value="">选择模型</option>
                  <option v-for="m in providerModels[editingKey.provider]" :key="m" :value="m">{{ m }}</option>
                </select>
                <input v-else v-model.trim="editForm.model" class="text-input" type="text" placeholder="例如: deepseek-chat" />
                <label class="field-label">API Key</label>
                <input v-model.trim="editForm.api_key" class="text-input" type="password" placeholder="sk-..." />
                <label class="field-label">API Base URL</label>
                <input v-model.trim="editForm.api_base" class="text-input" type="text" placeholder="https://..." />
                <p v-if="editNotice" class="password-notice" :class="'status-' + editNoticeType">{{ editNotice }}</p>
                <div class="password-actions">
                  <button class="action-btn" type="button" :disabled="saving || !editTestPassed" @click="saveEditKey">{{ saving ? '保存中...' : '保存' }}</button>
                  <button class="action-btn ghost" type="button" @click="testEditKey">测试连接</button>
                  <button class="action-btn ghost" type="button" @click="cancelEditKey">取消</button>
                </div>
              </div>
            </div>
          </div>
        </Teleport>
      </article>

      <article class="panel">
        <h2 class="panel-title">教务平台绑定</h2>
        <ul class="provider-list">
          <li class="provider-item">
            <div>
              <p class="binding-title">TIS 教务系统</p>
              <p class="binding-meta" v-if="tis.status === 'loading'">绑定中…</p>
              <p class="binding-meta" v-else-if="tis.status === 'binding'">请在弹窗中完成登录，然后点击「完成登录」</p>
              <template v-else-if="tis.status === 'bound'">
                <p class="binding-meta binding-success">已绑定 · {{ tis.studentName }}（{{ tis.studentId }}）</p>
                <p class="binding-meta">{{ tis.courseCount }} 门课程 · 绑定时间：{{ tis.bindTime }}</p>
              </template>
              <p class="binding-meta" v-else>未绑定</p>
            </div>
            <div class="action-group">
              <template v-if="tis.status === 'binding'">
                <button class="action-btn" type="button" @click="completeBinding('tis')">完成登录，开始绑定</button>
              </template>
              <template v-else-if="tis.status === 'unbound'">
                <button v-if="isTauriApp" class="action-btn" type="button" @click="bindTis">绑定 TIS</button>
                <button v-else class="action-btn ghost" type="button" @click="bindTis">绑定 TIS</button>
              </template>
              <button v-else-if="tis.status === 'bound'" class="action-btn ghost" type="button" @click="unbindTis">解绑</button>
            </div>
          </li>
          <li class="provider-item">
            <div>
              <p class="binding-title">Blackboard</p>
              <p class="binding-meta" v-if="bb.status === 'loading'">绑定中…</p>
              <p class="binding-meta" v-else-if="bb.status === 'binding'">请在弹窗中完成登录，然后点击「完成登录」</p>
              <template v-else-if="bb.status === 'bound'">
                <p class="binding-meta binding-success">已绑定 · {{ bb.assignmentsCount || bb.coursesCount }} 个事件</p>
                <p class="binding-meta">绑定时间：{{ bb.bindTime }}</p>
              </template>
              <p class="binding-meta" v-else>未绑定</p>
              <input v-if="bb.status !== 'bound'" v-model.trim="bbIcsUrl" class="text-input" type="text" placeholder="ICS 日历 URL（从 BB 日历 → 获取外部链接复制）" style="font-size:11px;margin-top:6px;" />
            </div>
            <div class="action-group">
              <template v-if="bb.status === 'binding'">
                <button class="action-btn" type="button" @click="completeBinding('blackboard')">完成登录，开始绑定</button>
              </template>
              <button v-else-if="bb.status !== 'bound'" class="action-btn" type="button" @click="bindBbWithIcs">绑定 Blackboard</button>
              <button v-else class="action-btn ghost" type="button" @click="unbindBb">解绑</button>
            </div>
          </li>

        </ul>
        <p class="binding-meta" v-if="isTauriApp" style="margin-top: 10px;">💡 点击「绑定」打开登录窗口，完成登录后<strong>保持窗口打开</strong>，然后点击「完成登录，开始绑定」。提取 Cookie 后会询问是否关闭窗口。</p>
        <p v-if="bindingError" class="status-text status-error" style="margin-top: 8px;">{{ bindingError }}</p>
        <div v-if="bindingProgress.active" class="binding-progress">
          <div class="progress-bar-track"><div class="progress-bar-fill"></div></div>
          <p class="progress-step">{{ bindingProgress.step }}</p>
        </div>
      </article>
    </div>

    <div v-if="isPasswordModalOpen" class="password-modal-mask" @click.self="closePasswordModal">
      <div class="password-modal" role="dialog" aria-modal="true" aria-label="修改密码">
        <h3 class="password-modal-title">修改密码</h3>

        <div class="password-form">
          <label class="field-label" for="oldPassword">旧密码</label>
          <input
            id="oldPassword"
            v-model="passwordForm.oldPassword"
            class="text-input"
            type="password"
            placeholder="请输入旧密码"
          />

          <label class="field-label" for="newPassword">新密码</label>
          <input
            id="newPassword"
            v-model="passwordForm.newPassword"
            class="text-input"
            type="password"
            placeholder="请输入新密码"
          />
          <p class="password-strength" :class="strengthClass">
            密码强度：{{ passwordStrengthLabel }}
          </p>

          <label class="field-label" for="confirmPassword">确认新密码</label>
          <input
            id="confirmPassword"
            v-model="passwordForm.confirmPassword"
            class="text-input"
            type="password"
            placeholder="请再次输入新密码"
          />

          <label class="field-label" for="verifyCode">验证码</label>
          <div class="verify-row">
            <input
              id="verifyCode"
              v-model.trim="passwordForm.verifyCode"
              class="text-input"
              type="text"
              placeholder="请输入验证码"
            />
            <button
              class="action-btn ghost"
              type="button"
              :disabled="verifyCountdown > 0"
              @click="requestVerifyCode"
            >
              {{ verifyCountdown > 0 ? `${verifyCountdown}s 后重试` : '获取验证码' }}
            </button>
          </div>

          <p v-if="passwordNotice" class="password-notice" :class="`status-${passwordNoticeType}`">{{ passwordNotice }}</p>

          <div class="password-actions">
            <button class="action-btn" type="button" @click="submitPasswordChange">确定修改</button>
            <button class="action-btn ghost" type="button" @click="closePasswordModal">取消</button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { tisAPI, blackboardAPI, emailAPI, settingsAPI } from '../services/api.js'
import { useCalendarStore } from '../stores/calendar.js'
import { useAuthStore } from '../stores/auth.js'
import { useEmailStore } from '../stores/email.js'
import { getTokenSync } from '../services/auth-storage.js'

const isTauriApp = !!window.__TAURI_INTERNALS__
let invoke = null

if (isTauriApp) {
  import('@tauri-apps/api/core').then(mod => {
    invoke = mod.invoke
    console.log('[UserSettings] Tauri IPC ready')
  }).catch(e => {
    console.error('[UserSettings] Tauri IPC import failed:', e)
  })
}

const authStore = useAuthStore()

const profile = reactive({
  name: authStore.user?.full_name || ''
})

const settingsData = ref({})

const isPasswordModalOpen = ref(false)
const passwordNotice = ref('')
const passwordNoticeType = ref('info')
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
  verifyCode: ''
})
const verifyCountdown = ref(0)
const verifyTimerId = ref(null)

const nameNotice = ref('')
const nameNoticeType = ref('info')

const mockPasswordBackend = reactive({
  currentPassword: 'OldPass#2026',
  latestVerifyCode: ''
})

// API Key management
const apiKeys = ref([])
const loadingKeys = ref(false)
const saving = ref(false)

const showAddKeyModal = ref(false)
const addForm = reactive({
  provider: '',
  model: '',
  api_key: '',
  api_base: ''
})
const addNotice = ref('')
const addNoticeType = ref('info')
const addTestPassed = ref(false)

const editingKey = ref(null)
const editForm = reactive({
  model: '',
  api_key: '',
  api_base: ''
})
const editNotice = ref('')
const editNoticeType = ref('info')
const editTestPassed = ref(false)

const defaultBases = {
  deepseek: 'https://api.deepseek.com/v1',
}

const providerModels = {
  deepseek: ['deepseek-chat', 'deepseek-reasoner', 'deepseek-v4-flash', 'deepseek-v4-pro'],
}

const defaultBaseFor = (provider) => {
  return defaultBases[provider] || 'https://api.openai.com/v1'
}

const loadApiKeys = async () => {
  loadingKeys.value = true
  try {
    const data = await settingsAPI.getApiKeys()
    apiKeys.value = data.providers || []
  } catch (e) {
    console.error('[UserSettings] Failed to load API keys:', e)
  } finally {
    loadingKeys.value = false
  }
}

// 选提供商时自动填 URL 和重置模型
watch(() => addForm.provider, (p) => {
  if (p && defaultBases[p]) {
    addForm.api_base = defaultBases[p]
  }
  addForm.model = ''
})

// 任何表单字段变化 → 必须重新测试
watch([() => addForm.provider, () => addForm.model, () => addForm.api_key, () => addForm.api_base],
  () => { addTestPassed.value = false }
)
watch([() => editForm.model, () => editForm.api_key, () => editForm.api_base],
  () => { editTestPassed.value = false }
)

const closeAddKeyModal = () => {
  showAddKeyModal.value = false
  addForm.provider = ''
  addForm.model = ''
  addForm.api_key = ''
  addForm.api_base = ''
  addNotice.value = ''
  addNoticeType.value = 'info'
  addTestPassed.value = false
}

const submitAddKey = async () => {
  const provider = addForm.provider
  if (!provider || !addForm.api_key) return
  saving.value = true
  addNotice.value = ''
  try {
    const apiBase = addForm.api_base || defaultBaseFor(addForm.provider)
    await settingsAPI.saveApiKey(provider, addForm.api_key, apiBase, addForm.model)
    closeAddKeyModal()
    await loadApiKeys()
  } catch (e) {
    addNotice.value = '保存失败: ' + e.message
    addNoticeType.value = 'error'
  } finally {
    saving.value = false
  }
}

const testAddKey = async () => {
  if (!addForm.provider || !addForm.api_key) {
    addNotice.value = '请先选择服务商并填写 API Key'
    addNoticeType.value = 'warn'
    return
  }
  addNotice.value = '正在测试连接...'
  addNoticeType.value = 'info'
  try {
    const apiBase = addForm.api_base || defaultBaseFor(addForm.provider)
    const result = await settingsAPI.testApiKey(addForm.provider, addForm.api_key, apiBase, addForm.model)
    addTestPassed.value = result.success
    if (result.success) {
      addNotice.value = '连接成功！'
      addNoticeType.value = 'success'
    } else {
      addNotice.value = '连接失败: ' + (result.message || '未知错误')
      addNoticeType.value = 'error'
    }
  } catch (e) {
    addTestPassed.value = false
    addNotice.value = '测试失败: ' + e.message
    addNoticeType.value = 'error'
  }
}

const startEditKey = (item) => {
  editingKey.value = item
  editForm.model = item.model || ''
  editForm.api_key = ''
  editForm.api_base = item.api_base || defaultBases[item.provider] || ''
  editNotice.value = ''
  editNoticeType.value = 'info'
  editTestPassed.value = false
}

const cancelEditKey = () => {
  editingKey.value = null
  editNotice.value = ''
  editNoticeType.value = 'info'
  editTestPassed.value = false
}

const saveEditKey = async () => {
  if (!editingKey.value) return
  saving.value = true
  editNotice.value = ''
  try {
    const apiBase = editForm.api_base || editingKey.value.api_base
    const model = editForm.model || editingKey.value.model || ''
    await settingsAPI.saveApiKey(editingKey.value.provider, editForm.api_key, apiBase, model)
    editNotice.value = '保存成功'
    editNoticeType.value = 'success'
    await loadApiKeys()
    setTimeout(() => cancelEditKey(), 800)
  } catch (e) {
    editNotice.value = '保存失败: ' + e.message
    editNoticeType.value = 'error'
  } finally {
    saving.value = false
  }
}

const testEditKey = async () => {
  if (!editingKey.value) return
  editNotice.value = '正在测试连接...'
  editNoticeType.value = 'info'
  try {
    const apiBase = editForm.api_base || editingKey.value.api_base
    const apiKey = editForm.api_key || ''
    const model = editForm.model || editingKey.value.model || ''
    const result = await settingsAPI.testApiKey(editingKey.value.provider, apiKey, apiBase, model)
    editTestPassed.value = result.success
    if (result.success) {
      editNotice.value = '连接成功！'
      editNoticeType.value = 'success'
    } else {
      editNotice.value = '连接失败: ' + (result.message || '未知错误')
      editNoticeType.value = 'error'
    }
  } catch (e) {
    editTestPassed.value = false
    editNotice.value = '测试失败: ' + e.message
    editNoticeType.value = 'error'
  }
}

const toggleApiKey = async (provider) => {
  try {
    const result = await settingsAPI.toggleApiKey(provider)
    if (result.success) {
      apiKeys.value = apiKeys.value.map(k => ({
        ...k,
        is_active: k.provider === provider ? result.is_active : k.is_active
      }))
    }
  } catch (e) {
    console.error('[UserSettings] Failed to toggle API key:', e)
  }
}

const unbindApiKey = async (provider) => {
  try {
    await settingsAPI.deleteApiKey(provider)
    await loadApiKeys()
  } catch (e) {
    console.error('[UserSettings] Failed to delete API key:', e)
  }
}

const saveName = async () => {
  if (!profile.name) {
    profile.name = '未命名用户'
    nameNotice.value = '姓名不能为空，已回退为默认值。'
    nameNoticeType.value = 'warn'
    return
  }
  try {
    await settingsAPI.update({ full_name: profile.name })
    if (authStore.user) authStore.user.full_name = profile.name
    nameNotice.value = '保存成功'
    nameNoticeType.value = 'success'
  } catch (e) {
    nameNotice.value = '保存失败: ' + e.message
    nameNoticeType.value = 'error'
  }
}

const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordForm.verifyCode = ''
  passwordNotice.value = ''
  passwordNoticeType.value = 'info'
}

const openPasswordModal = () => {
  isPasswordModalOpen.value = true
  passwordNotice.value = ''
}

const closePasswordModal = () => {
  isPasswordModalOpen.value = false
  resetPasswordForm()
}

const requestVerifyCode = () => {
  if (verifyCountdown.value > 0) {
    return
  }

  mockPasswordBackend.latestVerifyCode = String(100000 + Math.floor(Math.random() * 900000))
  verifyCountdown.value = 60
  passwordNotice.value = `验证码已发送到主邮箱（模拟码：${mockPasswordBackend.latestVerifyCode}）。`
  passwordNoticeType.value = 'info'

  verifyTimerId.value = setInterval(() => {
    if (verifyCountdown.value <= 1) {
      clearInterval(verifyTimerId.value)
      verifyTimerId.value = null
      verifyCountdown.value = 0
      return
    }
    verifyCountdown.value -= 1
  }, 1000)
}

const submitPasswordChange = () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword || !passwordForm.confirmPassword || !passwordForm.verifyCode) {
    passwordNotice.value = '请完整填写所有字段。'
    passwordNoticeType.value = 'warn'
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordNotice.value = '两次输入的新密码不一致。'
    passwordNoticeType.value = 'error'
    return
  }

  if (passwordForm.oldPassword !== mockPasswordBackend.currentPassword) {
    passwordNotice.value = '后端返回：旧密码错误。'
    passwordNoticeType.value = 'error'
    return
  }

  if (passwordForm.verifyCode !== mockPasswordBackend.latestVerifyCode) {
    passwordNotice.value = '后端返回：验证码错误或已失效。'
    passwordNoticeType.value = 'error'
    return
  }

  mockPasswordBackend.currentPassword = passwordForm.newPassword

  passwordNotice.value = '密码修改成功。'
  passwordNoticeType.value = 'success'
  setTimeout(() => {
    closePasswordModal()
  }, 500)
}

const passwordStrengthLabel = computed(() => {
  const pwd = passwordForm.newPassword
  if (!pwd) {
    return '未输入'
  }

  let score = 0
  if (pwd.length >= 8) score += 1
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1
  if (/\d/.test(pwd)) score += 1
  if (/[^A-Za-z0-9]/.test(pwd)) score += 1

  if (score <= 1) return '弱'
  if (score <= 3) return '中'
  return '强'
})

const strengthClass = computed(() => {
  if (passwordStrengthLabel.value === '强') return 'strength-strong'
  if (passwordStrengthLabel.value === '中') return 'strength-medium'
  if (passwordStrengthLabel.value === '弱') return 'strength-weak'
  return 'strength-empty'
})

const formatDate = (timestamp) => {
  if (!timestamp) {
    return '暂无'
  }

  const date = new Date(timestamp)
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  const s = String(date.getSeconds()).padStart(2, '0')
  return `${y}-${m}-${d} ${h}:${min}:${s}`
}

const tis = reactive({
  status: 'loading',
  studentName: '',
  studentId: '',
  courseCount: 0,
  bindTime: '',
})

const bb = reactive({
  status: 'loading',
  coursesCount: 0,
  assignmentsCount: 0,
  bindTime: '',
})

const email = reactive({
  status: 'loading',
  emailAddress: '',
  bindTime: '',
  lastSyncTime: '',
})

const emailForm = reactive({
  email: '',
  password: '',
})

const loadBindingStatus = async () => {
  try {
    const tisRes = await tisAPI.getStatus()
    if (tisRes.is_bound) {
      tis.status = 'bound'
      tis.studentName = tisRes.user_info?.name || tisRes.student_name || ''
      tis.studentId = tisRes.user_info?.student_id || tisRes.student_id || ''
      tis.courseCount = tisRes.total_courses || 0
      tis.bindTime = tisRes.bind_time || ''
    } else {
      tis.status = 'unbound'
    }
  } catch (err) {
    console.error('[UserSettings] TIS status error:', err)
    tis.status = 'unbound'
  }
  try {
    const bbRes = await blackboardAPI.getStatus()
    if (bbRes.is_bound) {
      bb.status = 'bound'
      bb.coursesCount = bbRes.courses_count || 0
      bb.assignmentsCount = bbRes.assignments_count || 0
      bb.bindTime = bbRes.bind_time || ''
    } else {
      bb.status = 'unbound'
    }
  } catch (err) {
    console.error('[UserSettings] BB status error:', err)
    bb.status = 'unbound'
  }
}

const loadEmailStatus = async () => {
  try {
    const res = await emailAPI.getStatus()
    if (res.is_bound) {
      email.status = 'bound'
      email.emailAddress = res.email_address || ''
      email.bindTime = res.bind_time || ''
      email.lastSyncTime = res.last_sync_time || ''
    } else {
      email.status = 'unbound'
    }
  } catch (err) {
    console.error('[UserSettings] email status error:', err)
    email.status = 'unbound'
  }
}

const bindEmail = async () => {
  if (!emailForm.email || !emailForm.password) {
    bindingError.value = '请填写邮箱地址和客户端专用密码'
    return
  }
  email.status = 'loading'
  bindingError.value = ''
  try {
    const result = await emailAPI.bind(emailForm.email, emailForm.password)
    if (result.success) {
      emailForm.email = ''
      emailForm.password = ''
      await loadEmailStatus()
      const emailStore = useEmailStore()
      await emailStore.fetchStatus()
    } else {
      bindingError.value = result.message || '绑定失败'
      email.status = 'unbound'
    }
  } catch (err) {
    bindingError.value = err?.message || '绑定失败'
    email.status = 'unbound'
  }
}

const syncEmail = async () => {
  try {
    await emailAPI.sync()
    await loadEmailStatus()
  } catch (err) {
    bindingError.value = err?.message || '同步失败'
  }
}

const unbindEmail = async () => {
  try {
    await emailAPI.unbind()
    await loadEmailStatus()
    const emailStore = useEmailStore()
    await emailStore.fetchStatus()
  } catch (err) {
    bindingError.value = err?.message || '解绑失败'
  }
}

const bindTis = async () => {
  if (!isTauriApp || !invoke) {
    window.open('https://cas.sustech.edu.cn/cas/login?service=https://tis.sustech.edu.cn', '_blank')
    return
  }
  try {
    bindingError.value = ''
    bindingProgress.active = true
    bindingProgress.step = '正在打开 CAS 登录窗口…'
    await invoke('open_cas_login', { platform: 'tis' })
    tis.status = 'binding'
    bindingProgress.active = false
  } catch (err) {
    bindingError.value = err?.message || String(err) || '打开登录窗口失败'
    tis.status = 'unbound'
    bindingProgress.active = false
  }
}

const bindBb = async () => {
  if (!isTauriApp || !invoke) {
    window.open('https://cas.sustech.edu.cn/cas/login?service=https://bb.sustech.edu.cn', '_blank')
    return
  }
  try {
    bindingError.value = ''
    bindingProgress.active = true
    bindingProgress.step = '正在打开 CAS 登录窗口…'
    await invoke('open_cas_login', { platform: 'blackboard' })
    bb.status = 'binding'
    bindingProgress.active = false
  } catch (err) {
    bindingError.value = err?.message || String(err) || '打开登录窗口失败'
    bb.status = 'unbound'
    bindingProgress.active = false
  }
}

const bindingError = ref('')
const bindingProgress = reactive({ active: false, step: '' })
const bbIcsUrl = ref('')

const completeBinding = async (platform) => {
  const state = platform === 'tis' ? tis : bb
  state.status = 'loading'
  bindingError.value = ''
  bindingProgress.active = true
  bindingProgress.step = '正在提取 Cookie…'
  try {
    if (!invoke) { state.status = 'unbound'; bindingProgress.active = false; return }

    let cookies
    try {
      cookies = await invoke('extract_cookies', { platform })
    } catch (extractErr) {
      const msg = typeof extractErr === 'string' ? extractErr : extractErr?.message || ''
      if (msg.includes('not found')) {
        bindingError.value = '请保持 CAS 登录窗口打开状态，不要提前关闭窗口，然后重新点击「完成登录，开始绑定」'
      } else {
        bindingError.value = msg || '提取 Cookie 失败，请重试'
      }
      state.status = 'unbound'
      bindingProgress.active = false
      return
    }

    if (!cookies || (Array.isArray(cookies) && cookies.length === 0)) {
      bindingError.value = '未检测到登录信息，请确认已在弹出窗口中完成登录'
      state.status = 'unbound'
      bindingProgress.active = false
      return
    }

    // Ask user whether to close the CAS window before proceeding
    const shouldClose = confirm('Cookie 已提取完毕，是否关闭登录窗口？')
    if (shouldClose) {
      await invoke('close_cas_window', { platform }).catch(() => {})
    }

    bindingProgress.step = '正在绑定到教务系统，请稍候…'
    const token = getTokenSync() || ''
    const bindFn = platform === 'tis' ? 'bind_tis' : 'bind_blackboard'
    const invokeArgs = { cookies, backendUrl: 'http://127.0.0.1:8002', token }
    if (platform === 'blackboard' && bbIcsUrl.value) {
      invokeArgs.icsUrl = bbIcsUrl.value
    }
    const result = await invoke(bindFn, invokeArgs)
    if (result && result.success) {
      bindingError.value = ''
      bindingProgress.step = '正在导入数据…'
      await loadBindingStatus()
      const calendarStore = useCalendarStore()
      if (platform === 'tis') {
        await calendarStore.importTISSchedule()
      } else {
        await calendarStore.importBlackboardAssignments()
      }
      bindingProgress.active = false
    } else {
      bindingError.value = result?.message || '绑定失败，请重试'
      state.status = 'unbound'
      bindingProgress.active = false
    }
  } catch (err) {
    bindingError.value = err?.message || String(err) || '绑定异常，请重试'
    state.status = 'unbound'
    bindingProgress.active = false
  }
}

const bindBbWithIcs = async () => {
  if (!bbIcsUrl.value) {
    bindingError.value = '请先输入 ICS 日历 URL'
    return
  }
  bb.status = 'loading'
  bindingError.value = ''
  try {
    const result = await blackboardAPI.bindIcs(bbIcsUrl.value)
    if (result.success) {
      bindingError.value = ''
      await loadBindingStatus()
      const calendarStore = useCalendarStore()
      await calendarStore.importBlackboardAssignments()
    } else {
      bindingError.value = result.message || 'ICS 绑定失败'
      bb.status = 'unbound'
    }
  } catch (err) {
    bindingError.value = err?.message || 'ICS 绑定失败'
    bb.status = 'unbound'
  }
}

const unbindTis = async () => {
  try { await tisAPI.unbind(); await loadBindingStatus() } catch {}
}

const unbindBb = async () => {
  try {
    await blackboardAPI.unbind()
    await loadBindingStatus()
    const calendarStore = useCalendarStore()
    calendarStore.clearBlackboardEvents()
  } catch {}
}

const loadSettings = async () => {
  try {
    const data = await settingsAPI.get()
    settingsData.value = data
  } catch {}
}

onMounted(() => {
  loadBindingStatus()
  loadEmailStatus()
  loadSettings()
  loadApiKeys()
})

onBeforeUnmount(() => {
  if (verifyTimerId.value) {
    clearInterval(verifyTimerId.value)
  }
})


</script>

<style scoped>
.settings-shell {
  width: 100%;
  min-height: 100%;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: var(--clr-bg-card, #ffffff);
  padding: 20px;
  box-sizing: border-box;
}

.settings-header {
  margin-bottom: 16px;
}

.settings-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1d1d1f;
}

.settings-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.panel {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 14px;
  background: var(--clr-bg-card, #ffffff);
}

.panel-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 12px;
  color: #4b5563;
}

.field-inline {
  display: flex;
  gap: 8px;
}

.add-form {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.text-input {
  min-width: 0;
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  color: #111827;
  background: var(--clr-bg-card, #ffffff);
}

.text-input:focus {
  outline: none;
  border-color: #007aff;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.action-btn {
  border: 1px solid #007aff;
  background: #007aff;
  color: #ffffff;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.action-btn:disabled {
  border-color: #d1d5db;
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.action-btn.ghost {
  border-color: rgba(0, 0, 0, 0.2);
  background: var(--clr-bg-card, #ffffff);
  color: #111827;
}

.binding-list,
.provider-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-group {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.binding-item,
.provider-item {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--clr-bg-card, #ffffff);
}

.binding-main {
  min-width: 0;
}

.binding-title {
  margin: 0;
  font-size: 13px;
  color: #111827;
  font-weight: 600;
  word-break: break-all;
}

.binding-meta {
  margin: 4px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.binding-success {
  color: #16a34a;
  font-weight: 600;
}

.binding-hint {
  color: #9ca3af;
  font-style: italic;
}

.text-btn {
  border: none;
  background: transparent;
  color: #ef4444;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.password-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.28);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  z-index: 50;
}

.password-modal {
  width: min(460px, calc(100vw - 32px));
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: var(--clr-bg-card, #ffffff);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
  padding: 16px;
}

.password-modal-title {
  margin: 0 0 12px;
  font-size: 17px;
  font-weight: 700;
  color: #111827;
}

.password-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.verify-row {
  display: flex;
  gap: 8px;
}

.password-notice {
  margin: 6px 0 0;
  font-size: 12px;
}

.password-strength {
  margin: 0;
  font-size: 12px;
}

.status-text {
  margin: 0;
  font-size: 12px;
}

.status-info {
  color: #2563eb;
}

.status-success {
  color: #16a34a;
}

.status-warn {
  color: #b45309;
}

.status-error {
  color: #dc2626;
}

.binding-progress {
  margin-top: 12px;
  padding: 12px;
  background: #f0f7ff;
  border-radius: 8px;
  border: 1px solid #bdd3f0;
}

.progress-bar-track {
  width: 100%;
  height: 6px;
  background: #d0ddf0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  width: 30%;
  background: linear-gradient(90deg, #007aff, #4a9eff);
  border-radius: 3px;
  animation: progress-indeterminate 1.5s ease-in-out infinite;
}

@keyframes progress-indeterminate {
  0% { transform: translateX(-100%); width: 30%; }
  50% { width: 60%; }
  100% { transform: translateX(400%); width: 30%; }
}

.progress-step {
  margin: 6px 0 0;
  font-size: 12px;
  color: #2563eb;
  text-align: center;
}

.strength-empty {
  color: #6b7280;
}

.strength-weak {
  color: #dc2626;
}

.strength-medium {
  color: #b45309;
}

.strength-strong {
  color: #16a34a;
}

.password-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 980px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

.email-bind-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 220px;
}

.email-bind-form .text-input {
  min-width: 0;
  flex: 1;
}

.email-bind-form .action-btn {
  align-self: flex-end;
}

/* Toggle Switch */
.toggle-switch {
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: #d1d5db;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-switch.active {
  background: #16a34a;
}

.toggle-knob {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle-switch.active .toggle-knob {
  transform: translateX(16px);
}
</style>
