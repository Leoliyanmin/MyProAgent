<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="mac-title">Login to AgentWorkspace</h1>
        <p class="mac-subtitle">Sign in to your account</p>
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="email" class="mac-label">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="mac-input"
            placeholder="Enter your email"
            required
            :class="{ 'is-invalid': errors.email }"
          />
          <span class="error-text" v-if="errors.email">{{ errors.email }}</span>
        </div>

        <div class="form-group">
          <label for="password" class="mac-label">Password</label>
          <div class="password-input-wrapper">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="mac-input"
              placeholder="Enter your password"
              required
              :class="{ 'is-invalid': errors.password }"
            />
            <button type="button" class="eye-btn" @click="showPassword = !showPassword">
               {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <span class="error-text" v-if="errors.password">{{ errors.password }}</span>
          <!-- 修改密码功能暂未实现后端接口，暂时隐藏 -->
          <!-- <router-link to="/forgot-password" class="forgot-password-link">Forgot password?</router-link> -->
        </div>
        
        <div v-if="auth.error" class="api-error">
          {{ auth.error }}
        </div>

        <button type="submit" class="mac-btn w-full" :disabled="auth.loading || !isValid">
          <span v-if="auth.loading" class="spinner"></span>
          <span v-else>Login</span>
        </button>
      </form>

      <div class="auth-footer">
        <p class="mac-text">
          Don't have an account? 
          <router-link to="/register" class="mac-link">Sign up</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({
  email: '',
  password: ''
})

const errors = reactive({
  email: '',
  password: ''
})

const showPassword = ref(false)

const validateEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

watch(() => form.email, (newVal) => {
  if (newVal && !validateEmail(newVal)) {
    errors.email = 'Invalid email format'
  } else {
    errors.email = ''
  }
})

watch(() => form.password, (newVal) => {
  if (newVal && newVal.length < 6) {
    errors.password = 'Password must be at least 6 characters'
  } else {
    errors.password = ''
  }
})

const isValid = computed(() => {
  return validateEmail(form.email) && form.password.length >= 6
})

const handleLogin = async () => {
  if (!isValid.value) return
  
  const result = await auth.login(form.email, form.password)
  
  if (result.success) {
    const redirectPath = route.query.redirect || '/dashboard'
    router.push(redirectPath)
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
  max-width: 400px;
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
  margin-bottom: 20px;
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

.forgot-password-link {
  display: inline-block;
  font-size: 12px;
  color: var(--clr-primary, #007aff);
  text-decoration: none;
  margin-top: 6px;
}

.forgot-password-link:hover {
  text-decoration: underline;
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

.mac-btn:hover:not(:disabled) {
  background-color: var(--clr-primary-dark, #0062cc);
}

.mac-btn:disabled {
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
