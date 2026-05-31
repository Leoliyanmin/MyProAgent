<template>
  <div class="widget-panel">
    <div class="widget-header">
      <span class="widget-title page-link" title="打开邮件管理" @click="openEmailPage">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        写邮件
      </span>
      <button class="widget-close" @click="close" title="关闭">✕</button>
    </div>

    <form class="compose-form" @submit.prevent="handleSend">
      <div class="field">
        <label class="field-label">收件人</label>
        <input v-model="form.to" class="field-input" type="email" placeholder="recipient@example.com" :disabled="sending" required />
      </div>
      <div class="field">
        <label class="field-label">主题</label>
        <input v-model="form.subject" class="field-input" type="text" placeholder="邮件主题" :disabled="sending" required />
      </div>
      <div class="field field-body">
        <label class="field-label">正文</label>
        <textarea v-model="form.body" class="field-input field-textarea" rows="5" placeholder="邮件正文..." :disabled="sending" required></textarea>
      </div>

      <div class="form-footer">
        <p v-if="sendSuccess" class="status-ok">✓ 发送成功</p>
        <p v-if="sendError" class="status-err">{{ sendError }}</p>
        <button type="submit" class="send-btn" :disabled="sending || !emailStore.bindStatus.is_bound">
          {{ sending ? '发送中...' : '发送' }}
        </button>
      </div>

      <div v-if="!emailStore.bindStatus.is_bound" class="unbound-hint">
        请先在用户设置中绑定邮箱
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useEmailStore } from '../../stores/email.js'
import { useDashboardStore } from '../../stores/dashboard.js'

const emailStore = useEmailStore()
const dashboardStore = useDashboardStore()
const router = useRouter()
const form = reactive({ to: '', subject: '', body: '' })
const sending = ref(false)
const sendSuccess = ref(false)
const sendError = ref('')

const close = () => dashboardStore.toggleMiniWidget('compose')

const openEmailPage = () => {
  router.push({ name: 'email' })
}

const handleSend = async () => {
  if (sending.value) return
  sendSuccess.value = false
  sendError.value = ''
  sending.value = true
  try {
    const result = await emailStore.send(form.subject, form.body, form.to)
    if (result.success) {
      sendSuccess.value = true
      form.to = ''
      form.subject = ''
      form.body = ''
    } else {
      sendError.value = result.message || '发送失败'
    }
  } catch (e) {
    sendError.value = e?.message || '发送失败'
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.widget-panel { display: flex; flex-direction: column; height: 100%; width: 100%; overflow: hidden; }
.widget-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; }
.widget-title { display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #1d1d1f; }
.page-link { cursor: pointer; }
.page-link:hover { color: #007aff; }
.widget-close { width: 22px; height: 22px; border: none; border-radius: 5px; background: transparent; cursor: pointer; font-size: 13px; color: rgba(0,0,0,0.35); display: flex; align-items: center; justify-content: center; transition: all 0.15s; flex-shrink: 0; }
.widget-close:hover { background: rgba(0,0,0,0.06); color: #ff3b30; }
.compose-form { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 10px 14px; overflow-y: auto; }
.field { display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; }
.field-body { flex: 1; min-height: 0; }
.field-label { font-size: 10px; font-weight: 600; color: rgba(0,0,0,0.4); text-transform: uppercase; letter-spacing: 0.3px; }
.field-input { padding: 6px 8px; border: 1px solid rgba(0,0,0,0.1); border-radius: 5px; font-size: 12px; outline: none; font-family: inherit; transition: border-color 0.2s; background: rgba(255,255,255,0.8); color: #1d1d1f; }
.field-input:focus { border-color: #007aff; background: #fff; }
.field-textarea { flex: 1; min-height: 80px; resize: vertical; }
.form-footer { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-shrink: 0; }
.status-ok { font-size: 11px; color: #34c759; margin: 0; }
.status-err { font-size: 11px; color: #ff3b30; margin: 0; }
.send-btn { padding: 5px 14px; background: #007aff; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
.send-btn:hover { background: #0062cc; }
.send-btn:disabled { background: #a0c4ff; cursor: not-allowed; }
.unbound-hint { font-size: 11px; color: #ff9500; text-align: center; padding: 6px; background: rgba(255,149,0,0.06); border-radius: 5px; }
</style>
