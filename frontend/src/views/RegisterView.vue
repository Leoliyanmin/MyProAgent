<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="mac-title">Create an Account</h1>
        <p class="mac-subtitle">Sign up for AgentWorkspace</p>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="fullName" class="mac-label">Full Name</label>
          <input
            id="fullName"
            v-model="form.fullName"
            type="text"
            class="mac-input"
            placeholder="Enter your full name"
            required
          />
        </div>

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
          <div class="label-row">
            <label for="password" class="mac-label">Password</label>
            <span class="hint-text-inline">(min. 8 chars)</span>
          </div>
          <div class="password-input-wrapper">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="mac-input"
              placeholder="Enter password"
              required
              :class="{ 'is-invalid': errors.password }"
            />
            <button type="button" class="eye-btn" @click="showPassword = !showPassword">
               {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <span class="error-text" v-if="errors.password">{{ errors.password }}</span>
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="mac-label">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            class="mac-input"
            placeholder="Confirm your password"
            required
            :class="{ 'is-invalid': errors.confirmPassword }"
          />
          <span class="error-text" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
        </div>
        
        <div v-if="auth.error" class="api-error">
          {{ auth.error }}
        </div>
        <div v-if="successMsg" class="api-success">
          {{ successMsg }}
        </div>

        <button type="submit" class="mac-btn w-full" :disabled="auth.loading || !isValid">
          <span v-if="auth.loading" class="spinner"></span>
          <span v-else>Register</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="mac-text">
          Already have an account? 
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
  fullName: '',
  email: '',
  verificationCode: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  email: '',
  verificationCode: '',
  password: '',
  confirmPassword: ''
})

const showPassword = ref(false)
const countdown = ref(0)
const sendingCode = ref(false)
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

watch(() => form.password, (newVal) => {
  if (newVal && newVal.length < 8) {
    errors.password = 'Password must be at least 8 characters'
  } else {
    errors.password = ''
  }
  
  if (form.confirmPassword && newVal !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
  } else {
    errors.confirmPassword = ''
  }
})

watch(() => form.confirmPassword, (newVal) => {
  if (newVal && newVal !== form.password) {
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

const isValid = computed(() => {
  return validateEmail(form.email) && 
         form.password.length >= 8 && 
         form.password === form.confirmPassword &&
         /^\d{6}$/.test(form.verificationCode) &&
         form.fullName.trim() !== ''
})

const sendCode = async () => {
  if (!isEmailValid.value || countdown.value > 0 || sendingCode.value) return

  sendingCode.value = true
  successMsg.value = ''

  try {
    const result = await auth.sendVerificationCode(form.email, 'register')

    if (result.success) {
      // Start countdown
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) clearInterval(timer)
      }, 1000)

      // Show test code if in test mode
      if (result.test_code) {
        successMsg.value = `Test code: ${result.test_code}`
      }
    } else {
       auth.error = result.message || 'Failed to send code'
    }
  } finally {
    sendingCode.value = false
  }
}

const handleRegister = async () => {
  if (!isValid.value) return
  
  successMsg.value = ''
  
  const result = await auth.register(
    form.email, 
    form.password, 
    form.fullName, 
    form.verificationCode
  )
  
  if (result.success) {
    successMsg.value = 'Registration successful! Redirecting to login...'
    setTimeout(() => {
      router.push('/login')
    }, 1500)
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

.label-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.hint-text-inline {
  font-size: 12px;
  color: var(--clr-text-secondary, #86868b);
}

.hint-text {
  display: block;
  font-size: 12px;
  color: var(--clr-text-secondary, #86868b);
  margin-top: 4px;
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
