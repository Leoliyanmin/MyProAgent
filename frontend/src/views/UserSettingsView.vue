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
        <form class="add-form" @submit.prevent="addEmailBinding">
          <input
            v-model.trim="newEmail.email"
            class="text-input"
            type="email"
            placeholder="新增绑定邮箱"
            required
          />
          <input
            v-model="newEmail.password"
            class="text-input"
            type="password"
            placeholder="邮箱密码"
            required
          />
          <button class="action-btn" type="submit">添加绑定</button>
        </form>

        <ul class="binding-list">
          <li v-for="item in emailBindings" :key="item.id" class="binding-item">
            <div class="binding-main">
              <p class="binding-title">{{ item.email }}</p>
              <p class="binding-meta">绑定代码：{{ item.code }}</p>
            </div>
            <button class="text-btn" type="button" @click="removeEmailBinding(item.id)">移除</button>
          </li>
        </ul>
      </article>

      <article class="panel">
        <h2 class="panel-title">AI 服务 API Key</h2>
        
        <!-- 添加按钮 / 展开表单 -->
        <div v-if="!showAddKeyForm" style="margin-bottom:12px;">
          <button class="action-btn ghost" type="button" @click="showAddKeyForm = true">+ 添加 API Key</button>
        </div>
        <div v-else class="add-form">
          <select v-model="newKey.provider" class="text-input" style="flex:0 0 auto;width:140px;">
            <option value="">选择服务商</option>
            <option value="deepseek">DeepSeek</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="zhipu">Zhipu (智谱)</option>
            <option value="openrouter">OpenRouter</option>
            <option value="groq">Groq</option>
            <option value="moonshot">Moonshot</option>
            <option value="gemini">Gemini</option>
            <option value="custom">自定义</option>
          </select>
          <input
            v-if="newKey.provider === 'custom'"
            v-model.trim="newKey.customProvider"
            class="text-input"
            type="text"
            placeholder="自定义服务商名称"
            style="flex:0 0 auto;width:160px;"
          />
          <input
            v-model.trim="newKey.api_key"
            class="text-input"
            type="password"
            placeholder="API Key (sk-...)"
          />
          <input
            v-model.trim="newKey.api_base"
            class="text-input"
            type="text"
            :placeholder="defaultBaseFor(newKey.provider)"
          />
          <button class="action-btn" type="button" :disabled="saving" @click="addApiKey">{{ saving ? '保存中...' : '保存并测试' }}</button>
          <button class="action-btn ghost" type="button" @click="cancelAddKey">取消</button>
        </div>

        <!-- 空态 -->
        <p v-if="apiKeys.length === 0 && !showAddKeyForm && !loadingKeys" class="binding-meta">暂无已配置的 API Key</p>
        <p v-if="loadingKeys" class="binding-meta">加载中...</p>

        <!-- 已绑定列表 -->
        <ul class="binding-list">
          <li v-for="item in apiKeys" :key="item.provider" class="binding-item">
            <div class="binding-main">
              <p class="binding-title">{{ item.provider }}</p>
              <p class="binding-meta" :class="item.last_test_success === true ? 'binding-success' : item.last_test_success === false ? 'status-error' : ''">
                {{ item.last_test_success === true ? '● 已连接' : item.last_test_success === false ? '✕ 连接失败' : '○ 未测试' }}
              </p>
              <p class="binding-meta">{{ item.api_key_masked }}</p>
              <p class="binding-meta" style="font-size:11px;color:#9ca3af;">{{ item.api_base }}</p>
            </div>
            <div class="action-group">
              <button class="text-btn" type="button" @click="startEditKey(item)">编辑</button>
              <button class="text-btn" type="button" @click="unbindApiKey(item.provider)">解绑</button>
            </div>
          </li>
        </ul>

        <!-- 编辑弹窗 -->
        <Teleport to="body">
          <div v-if="editingKey" class="password-modal-mask" @click.self="cancelEditKey">
            <div class="password-modal" role="dialog" aria-modal="true" aria-label="编辑 API Key">
              <h3 class="password-modal-title">编辑 {{ editingKey.provider }}</h3>
              <div class="password-form">
                <label class="field-label">API Key</label>
                <input v-model.trim="editForm.api_key" class="text-input" type="password" placeholder="sk-..." />
                <label class="field-label">API Base URL</label>
                <input v-model.trim="editForm.api_base" class="text-input" type="text" placeholder="https://..." />
                <p v-if="editNotice" class="password-notice" :class="'status-' + editNoticeType">{{ editNotice }}</p>
                <div class="password-actions">
                  <button class="action-btn" type="button" :disabled="saving" @click="saveEditKey">{{ saving ? '保存中...' : '保存' }}</button>
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
                <p class="binding-meta binding-success">已绑定 · {{ bb.coursesCount }} 门课程</p>
                <p class="binding-meta">绑定时间：{{ bb.bindTime }}</p>
              </template>
              <p class="binding-meta" v-else>未绑定</p>
            </div>
            <div class="action-group">
              <template v-if="bb.status === 'binding'">
                <button class="action-btn" type="button" @click="completeBinding('blackboard')">完成登录，开始绑定</button>
              </template>
              <template v-else-if="bb.status === 'unbound'">
                <button v-if="isTauriApp" class="action-btn" type="button" @click="bindBb">绑定 Blackboard</button>
                <button v-else class="action-btn ghost" type="button" @click="bindBb">绑定 Blackboard</button>
              </template>
              <button v-else-if="bb.status === 'bound'" class="action-btn ghost" type="button" @click="unbindBb">解绑</button>
            </div>
          </li>
          <li class="provider-item">
            <div>
              <p class="binding-title">邮箱</p>
              <p class="binding-meta" v-if="email.status === 'loading'">加载中…</p>
              <template v-else-if="email.status === 'bound'">
                <p class="binding-meta binding-success">已绑定 · {{ email.emailAddress }}</p>
                <p class="binding-meta">绑定时间：{{ email.bindTime }}</p>
                <p v-if="email.lastSyncTime" class="binding-meta">上次同步：{{ email.lastSyncTime }}</p>
              </template>
              <p class="binding-meta" v-else>未绑定</p>
              <p class="binding-meta binding-hint" style="margin-top: 4px;">仅支持腾讯企业邮箱（如 @mail.sustech.edu.cn）</p>
            </div>
            <div class="action-group">
              <template v-if="email.status === 'unbound'">
                <div class="email-bind-form">
                  <input v-model="emailForm.email" class="text-input" type="email" placeholder="企业邮箱地址（如 xxx@mail.sustech.edu.cn）" />
                  <input v-model="emailForm.password" class="text-input" type="password" placeholder="客户端专用密码（非登录密码）" />
                  <p class="binding-meta binding-hint">获取方式：登录邮箱网页版 → 设置 → 客户端专用密码 → 生成</p>
                  <button class="action-btn" type="button" @click="bindEmail">绑定邮箱</button>
                </div>
              </template>
              <template v-else-if="email.status === 'bound'">
                <button class="action-btn ghost" type="button" @click="syncEmail">同步</button>
                <button class="action-btn ghost" type="button" @click="unbindEmail">解绑</button>
              </template>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
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

const newEmail = reactive({
  email: '',
  password: ''
})

const emailBindings = ref([
  { id: 1, email: 'yanmin.work@example.com', code: 'MAIL-9KD2' },
  { id: 2, email: 'yanmin.alert@example.com', code: 'MAIL-3PT7' }
])

const newEmail = reactive({
  email: '',
  password: ''
})

const emailBindings = ref([
  { id: 1, email: 'yanmin.work@example.com', code: 'MAIL-9KD2' },
  { id: 2, email: 'yanmin.alert@example.com', code: 'MAIL-3PT7' }
])

// API Key management
const apiKeys = ref([])
const loadingKeys = ref(false)
const saving = ref(false)
const showAddKeyForm = ref(false)
const newKey = reactive({
  provider: '',
  customProvider: '',
  api_key: '',
  api_base: ''
})
const editingKey = ref(null)
const editForm = reactive({
  api_key: '',
  api_base: ''
})
const editNotice = ref('')
const editNoticeType = ref('info')

const defaultBases = {
  deepseek: 'https://api.deepseek.com/v1',
  openai: 'https://api.openai.com/v1',
  anthropic: 'https://api.anthropic.com',
  zhipu: 'https://open.bigmodel.cn/api/paas/v4',
  openrouter: 'https://openrouter.ai/api/v1',
  groq: 'https://api.groq.com/openai/v1',
  moonshot: 'https://api.moonshot.cn/v1',
  gemini: 'https://generativelanguage.googleapis.com/v1beta',
  custom: 'https://'
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

const cancelAddKey = () => {
  showAddKeyForm.value = false
  newKey.provider = ''
  newKey.customProvider = ''
  newKey.api_key = ''
  newKey.api_base = ''
}

const addApiKey = async () => {
  const provider = newKey.provider === 'custom' ? newKey.customProvider : newKey.provider
  if (!provider || !newKey.api_key) return
  saving.value = true
  try {
    const apiBase = newKey.api_base || defaultBaseFor(newKey.provider)
    await settingsAPI.saveApiKey(provider, newKey.api_key, apiBase)
    cancelAddKey()
    await loadApiKeys()
  } catch (e) {
    console.error('[UserSettings] Failed to save API key:', e)
  } finally {
    saving.value = false
  }
}

const startEditKey = (item) => {
  editingKey.value = item
  editForm.api_key = ''
  editForm.api_base = item.api_base || ''
  editNotice.value = ''
  editNoticeType.value = 'info'
}

const cancelEditKey = () => {
  editingKey.value = null
  editNotice.value = ''
  editNoticeType.value = 'info'
}

const saveEditKey = async () => {
  if (!editingKey.value) return
  saving.value = true
  editNotice.value = ''
  try {
    const apiBase = editForm.api_base || editingKey.value.api_base
    await settingsAPI.saveApiKey(editingKey.value.provider, editForm.api_key, apiBase)
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
    const result = await settingsAPI.testApiKey(editingKey.value.provider, apiKey, apiBase)
    if (result.success) {
      editNotice.value = '连接成功！'
      editNoticeType.value = 'success'
    } else {
      editNotice.value = '连接失败: ' + (result.message || '未知错误')
      editNoticeType.value = 'error'
    }
  } catch (e) {
    editNotice.value = '测试失败: ' + e.message
    editNoticeType.value = 'error'
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
    const result = await invoke(bindFn, { cookies, backendUrl: 'http://127.0.0.1:8002', token })
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

const unbindTis = async () => {
  try { await tisAPI.unbind(); await loadBindingStatus() } catch {}
}

const unbindBb = async () => {
  try { await blackboardAPI.unbind(); await loadBindingStatus() } catch {}
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

const createCode = () => {
  const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let token = 'MAIL-'
  for (let i = 0; i < 4; i += 1) {
    token += alphabet[Math.floor(Math.random() * alphabet.length)]
  }
  return token
}

const addEmailBinding = () => {
  const nextId = Date.now()
  emailBindings.value.unshift({
    id: nextId,
    email: newEmail.email,
    code: createCode()
  })
  newEmail.email = ''
  newEmail.password = ''
}

const removeEmailBinding = (id) => {
  emailBindings.value = emailBindings.value.filter(item => item.id !== id)
}


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
</style>
