<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="mac-title">Reset Password</h1>
        <p class="mac-subtitle">Set a new password for your account</p>
      </div>

      <form @submit.prevent="handleResetPassword" class="auth-form">
        <div class="form-group">
          <label for="email" class="mac-label">Email</label>
          <div class="email-input-wrapper">
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="mac-input"
              placeholder="Enter your email"
              required
              :class="{ 'is-invalid': errors.email }"
            />
            <button 
              type="button" 
              class="mac-btn-sm send-code-btn" 
              @click="sendCode"
              :disabled="countdown > 0 || !isEmailValid || sendingCode"
            >
              {{ countdown > 0 ? `${countdown}s` : (sendingCode ? 'Sending' : 'Send Code') }}
            </button>
          </div>
          <span class="error-text" v-if="errors.email">{{ errors.email }}</span>
        </div>

        <div class="form-group">
          <label for="verificationCode" class="mac-label">Verification Code</label>
          <input
            id="verificationCode"
            v-model="form.verificationCode"
            type="text"
            class="mac-input"
            placeholder="Enter 6-digit code"
            required
            maxlength="6"
            :class="{ 'is-invalid': errors.verificationCode }"
          />
          <span class="error-text" v-if="errors.verificationCode">{{ errors.verificationCode }}</span>
        </div>

        <div class="form-group">
          <label for="oldPassword" class="mac-label">Old Password</label>
          <div class="password-input-wrapper">
            <input
              id="oldPassword"
              v-model="form.oldPassword"
              :type="showOldPassword ? 'text' : 'password'"
              class="mac-input"
              placeholder="Enter your old password"
              required
              :class="{ 'is-invalid': errors.oldPassword }"
            />
            <button type="button" class="eye-btn" @click="showOldPassword = !showOldPassword">
              {{ showOldPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <span class="error-text" v-if="errors.oldPassword">{{ errors.oldPassword }}</span>
        </div>

        <div class="form-group">
          <label for="newPassword" class="mac-label">New Password <span class="label-hint">(min. 8 characters)</span></label>
          <div class="password-input-wrapper">
            <input
              id="newPassword"
              v-model="form.newPassword"
              :type="showNewPassword ? 'text' : 'password'"
              class="mac-input"
              placeholder="Enter your new password"
              required
              :class="{ 'is-invalid': errors.newPassword }"
            />
            <button type="button" class="eye-btn" @click="showNewPassword = !showNewPassword">
              {{ showNewPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <span class="error-text" v-if="errors.newPassword">{{ errors.newPassword }}</span>
          <p class="password-strength" :class="strengthClass" v-if="form.newPassword">
            Password strength: {{ passwordStrengthLabel }}
          </p>
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="mac-label">Confirm New Password</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            class="mac-input"
            placeholder="Confirm your new password"
            required
            :class="{ 'is-invalid': errors.confirmPassword }"
          />
          <span class="error-text" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
        </div>
        
        <div v-if="errorMsg" class="api-error">
          {{ errorMsg }}
        </div>
        <div v-if="successMsg" class="api-success">
          {{ successMsg }}
        </div>

        <button type="submit" class="mac-btn w-full" :disabled="loading || !isValid">
          <span v-if="loading" class="spinner"></span>
          <span v-else>Reset Password</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="mac-text">
          Remember your password? 
          <router-link to="/login" class="mac-link">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  email: '',
  verificationCode: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errors = reactive({
  email: '',
  verificationCode: '',
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const showOldPassword = ref(false)
const showNewPassword = ref(false)
const countdown = ref(0)
const sendingCode = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')

const validateEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

const isEmailValid = computed(() => validateEmail(form.email))

watch(() => form.email, (newVal) => {
  if (newVal && !validateEmail(newVal)) {
    errors.email = 'Invalid email format'
  } else {
    errors.email = ''
  }
})

watch(() => form.newPassword, (newVal) => {
  if (newVal && newVal.length < 8) {
    errors.newPassword = 'Password must be at least 8 characters'
  } else {
    errors.newPassword = ''
  }
  
  if (form.confirmPassword && newVal !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  } else {
    errors.confirmPassword = ''
  }
})

watch(() => form.confirmPassword, (newVal) => {
  if (newVal && newVal !== form.newPassword) {
    errors.confirmPassword = 'Passwords do not match'
  } else {
    errors.confirmPassword = ''
  }
})

watch(() => form.verificationCode, (newVal) => {
  if (newVal && !/^\d{6}$/.test(newVal)) {
    errors.verificationCode = 'Code must be 6 digits'
  } else {
    errors.verificationCode = ''
  }
})

const passwordStrengthLabel = computed(() => {
  const pwd = form.newPassword
  if (!pwd) return ''
  
  let score = 0
  if (pwd.length >= 8) score += 1
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1
  if (/\d/.test(pwd)) score += 1
  if (/[^A-Za-z0-9]/.test(pwd)) score += 1
  
  if (score <= 1) return 'Weak'
  if (score <= 3) return 'Medium'
  return 'Strong'
})

const strengthClass = computed(() => {
  if (passwordStrengthLabel.value === 'Strong') return 'strength-strong'
  if (passwordStrengthLabel.value === 'Medium') return 'strength-medium'
  if (passwordStrengthLabel.value === 'Weak') return 'strength-weak'
  return ''
})

const isValid = computed(() => {
  return validateEmail(form.email) && 
         form.newPassword.length >= 8 && 
         form.newPassword === form.confirmPassword &&
         /^\d{6}$/.test(form.verificationCode) &&
         form.oldPassword.length > 0 &&
         form.verificationCode.length === 6
})

const sendCode = async () => {
  if (!isEmailValid.value || countdown.value > 0 || sendingCode.value) return

  sendingCode.value = true
  errorMsg.value = ''
  successMsg.value = ''

  try {
    // TODO: Replace with actual API call to send verification code
    // const result = await auth.sendVerificationCode(form.email, 'reset_password')
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Start countdown
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)

    // Show test code for development
    const testCode = String(100000 + Math.floor(Math.random() * 900000))
    successMsg.value = `Verification code sent. Test code: ${testCode}`
  } catch (error) {
    errorMsg.value = error.message || 'Failed to send code'
  } finally {
    sendingCode.value = false
  }
}

const handleResetPassword = async () => {
  if (!isValid.value) return
  
  loading.value = true
  errorMsg.value = ''
  successMsg.value = ''
  
  try {
    // TODO: Replace with actual API call
    // const result = await auth.resetPassword({
    //   email: form.email,
    //   oldPassword: form.oldPassword,
    //   newPassword: form.newPassword,
    //   verificationCode: form.verificationCode
    // })
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    successMsg.value = 'Password reset successfully! Redirecting to login...'
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error) {
    errorMsg.value = error.message || 'Failed to reset password'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: var(--clr-bg-app, #f5f5f7);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  width: 100vw;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  background: var(--clr-bg-content, #ffffff);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05);
  padding: 32px;
  box-sizing: border-box;
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.mac-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--clr-text-primary, #1d1d1f);
  margin: 0 0 8px 0;
}

.mac-subtitle {
  font-size: 14px;
  color: var(--clr-text-secondary, #86868b);
  margin: 0;
}

.form-group {
  margin-bottom: 16px;
}

.mac-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--clr-text-secondary, #86868b);
  margin-bottom: 8px;
}

.mac-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid var(--clr-border, #d2d2d7);
  background-color: var(--clr-bg-app, #f5f5f7);
  font-size: 14px;
  color: var(--clr-text-primary, #1d1d1f);
  outline: none;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.mac-input:focus {
  border-color: var(--clr-primary, #007aff);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  background-color: #ffffff;
}

.mac-input.is-invalid {
  border-color: #ff3b30;
}

.email-input-wrapper {
  display: flex;
  gap: 8px;
}

.send-code-btn {
  flex-shrink: 0;
  width: 110px;
}

.password-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.eye-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: var(--clr-text-secondary, #86868b);
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.eye-btn:hover {
  color: var(--clr-primary, #007aff);
}

.error-text {
  display: block;
  font-size: 12px;
  color: #ff3b30;
  margin-top: 4px;
}

.label-hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--clr-text-secondary, #86868b);
}

.password-strength {
  font-size: 12px;
  margin: 6px 0 0;
}

.strength-weak {
  color: #ff3b30;
}

.strength-medium {
  color: #ff9500;
}

.strength-strong {
  color: #34c759;
}

.api-error {
  font-size: 13px;
  color: #ff3b30;
  background-color: rgba(255, 59, 48, 0.1);
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 20px;
  text-align: center;
}

.api-success {
  font-size: 13px;
  color: #34c759;
  background-color: rgba(52, 199, 89, 0.1);
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 20px;
  text-align: center;
}

.mac-btn {
  background-color: var(--clr-primary, #007aff);
  color: white;
  border: none;
  border-radius: 8px;
  height: 40px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mac-btn-sm {
  background-color: var(--clr-bg-content, #e5e5ea);
  color: var(--clr-text-primary, #1d1d1f);
  border: 1px solid var(--clr-border, #d2d2d7);
  border-radius: 8px;
  height: 40px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mac-btn-sm:hover:not(:disabled) {
  background-color: #d1d1d6;
}

.mac-btn:hover:not(:disabled) {
  background-color: var(--clr-primary-dark, #0062cc);
}

.mac-btn:disabled, .mac-btn-sm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.w-full {
  width: 100%;
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
}

.mac-text {
  font-size: 13px;
  color: var(--clr-text-secondary, #86868b);
}

.mac-link {
  color: var(--clr-primary, #007aff);
  text-decoration: none;
  font-weight: 500;
}

.mac-link:hover {
  text-decoration: underline;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
