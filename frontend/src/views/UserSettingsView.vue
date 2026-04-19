<template>
  <section class="settings-shell">
    <header class="settings-header">
      <h1 class="settings-title">用户设置</h1>
      <p class="settings-subtitle">管理个人资料、邮箱绑定、RSS 与外部账号</p>
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
          <p class="binding-meta">
            最近姓名修改时间：{{ formatDate(mockProfileBackend.lastNameUpdatedAt) }}
          </p>
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
        <h2 class="panel-title">个人 RSS</h2>
        <form class="add-form" @submit.prevent="addRssSource">
          <input
            v-model.trim="newRss"
            class="text-input"
            type="url"
            placeholder="https://example.com/feed.xml"
            required
          />
          <button class="action-btn" type="submit">添加 RSS</button>
        </form>

        <ul class="binding-list">
          <li v-for="source in rssSources" :key="source.id" class="binding-item">
            <div class="binding-main">
              <p class="binding-title">{{ source.url }}</p>
            </div>
            <button class="text-btn" type="button" @click="removeRssSource(source.id)">移除</button>
          </li>
        </ul>
      </article>

      <article class="panel">
        <h2 class="panel-title">第三方平台绑定</h2>
        <ul class="provider-list">
          <li v-for="provider in providers" :key="provider.key" class="provider-item">
            <div>
              <p class="binding-title">{{ provider.label }}</p>
              <p class="binding-meta">
                {{ provider.connected ? `已绑定账号：${provider.account}` : '未绑定' }}
              </p>
            </div>
            <button class="action-btn ghost" type="button" @click="toggleProvider(provider.key)">
              {{ provider.connected ? '解除绑定' : '立即绑定' }}
            </button>
          </li>
        </ul>
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
import { computed, onBeforeUnmount, reactive, ref } from 'vue'

const profile = reactive({
  name: 'Yanmin'
})

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
const mockProfileBackend = reactive({
  lastNameUpdatedAt: Date.now() - 2 * 60 * 60 * 1000,
  minIntervalMs: 60 * 1000
})

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

const newRss = ref('')
const rssSources = ref([
  { id: 1, url: 'https://github.blog/feed/' },
  { id: 2, url: 'https://stackoverflow.blog/feed/' }
])

const providers = ref([
  { key: 'github', label: 'GitHub', connected: true, account: 'yanmin-dev' },
  { key: 'stackoverflow', label: 'Stack Overflow', connected: false, account: '' },
])

const saveName = () => {
  if (!profile.name) {
    profile.name = '未命名用户'
    nameNotice.value = '姓名不能为空，已回退为默认值。'
    nameNoticeType.value = 'warn'
    return
  }

  const now = Date.now()
  const elapsed = now - mockProfileBackend.lastNameUpdatedAt
  if (elapsed < mockProfileBackend.minIntervalMs) {
    const waitSeconds = Math.ceil((mockProfileBackend.minIntervalMs - elapsed) / 1000)
    nameNotice.value = `后端限制：请在 ${waitSeconds}s 后再次修改姓名。`
    nameNoticeType.value = 'error'
    return
  }

  mockProfileBackend.lastNameUpdatedAt = now
  nameNotice.value = `后端保存成功，修改时间键已更新为 ${formatDate(now)}。`
  nameNoticeType.value = 'success'
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

const addRssSource = () => {
  const nextId = Date.now()
  rssSources.value.unshift({ id: nextId, url: newRss.value })
  newRss.value = ''
}

const removeRssSource = (id) => {
  rssSources.value = rssSources.value.filter(item => item.id !== id)
}

const toggleProvider = (key) => {
  providers.value = providers.value.map(item => {
    if (item.key !== key) {
      return item
    }

    if (item.connected) {
      return { ...item, connected: false, account: '' }
    }

    return {
      ...item,
      connected: true,
      account: `${item.key}_user`
    }
  })
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
</style>
