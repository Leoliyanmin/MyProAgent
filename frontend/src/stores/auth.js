import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../services/api.js'
import { saveAuth, loadAuth, clearAuth, refreshSessionTTL } from '../services/auth-storage.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const sessionExpired = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isLoggedIn = computed(() => !!user.value)

  const initAuth = async () => {
    const result = await loadAuth()
    if (!result) return
    if (result.expired) {
      sessionExpired.value = true
      return
    }
    token.value = result.token
    try {
      await fetchUser()
    } catch (err) {
      console.warn('Failed to fetch user info, continuing with cached token:', err.message)
      user.value = { email: result.user_email || '', full_name: null }
    }
  }

  const login = async (email, password) => {
    loading.value = true
    error.value = null
    sessionExpired.value = false

    try {
      const result = await authAPI.login(email, password)

      if (result.success && result.access_token) {
        token.value = result.access_token
        await saveAuth({ token: result.access_token, user_email: email })

        try {
          await fetchUser()
        } catch (userErr) {
          console.warn('Failed to fetch user info, but login succeeded:', userErr)
          user.value = { email, full_name: null }
        }

        return { success: true }
      } else {
        error.value = result.message || 'Login failed'
        return { success: false, message: error.value }
      }
    } catch (err) {
      error.value = err.message || 'Network error'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  const register = async (email, password, full_name, verification_code, code_context) => {
    loading.value = true
    error.value = null

    try {
      const result = await authAPI.register(email, password, full_name, verification_code, code_context)
      if (result.success) {
        return { success: true, message: result.message }
      } else {
        error.value = result.message || 'Registration failed'
        return { success: false, message: error.value }
      }
    } catch (err) {
      error.value = err.message || 'Network error'
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  const sendVerificationCode = async (email, purpose = 'register') => {
    loading.value = true
    error.value = null
    try {
      return await authAPI.sendVerificationCode(email, purpose)
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const userData = await authAPI.getCurrentUser()
      user.value = userData
    } catch (err) {
      console.error('Failed to fetch user:', err)
      throw err
    }
  }

  const logout = async () => {
    user.value = null
    token.value = null
    sessionExpired.value = false
    await clearAuth()
  }

  const updateProfile = (profileData) => {
    if (user.value) {
      user.value = { ...user.value, ...profileData }
    }
  }

  const touchSession = async () => {
    await refreshSessionTTL()
  }

  const dismissExpiredNotice = () => {
    sessionExpired.value = false
  }

  return {
    user,
    token,
    loading,
    error,
    sessionExpired,
    isAuthenticated,
    isLoggedIn,
    initAuth,
    login,
    register,
    sendVerificationCode,
    fetchUser,
    logout,
    updateProfile,
    touchSession,
    dismissExpiredNotice,
  }
})
