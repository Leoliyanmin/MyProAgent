import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../services/api.js'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isLoggedIn = computed(() => !!user.value)

  // Actions
  
  // Initialize auth state from localStorage
  const initAuth = async () => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
      try {
        await fetchUser()
      } catch (err) {
        logout()
      }
    }
  }

  // Login
  const login = async (email, password) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await authAPI.login(email, password)
      
      if (result.success && result.user) {
        user.value = result.user
        
        if (result.token) {
          token.value = result.token
          localStorage.setItem('token', result.token)
        } else {
          const tempToken = btoa(JSON.stringify({
            user_id: result.user.user_id,
            email: result.user.email,
            exp: Date.now() + 3600000
          }))
          token.value = tempToken
          localStorage.setItem('token', tempToken)
        }
        
        return { success: true }
      } else if (result.success && !result.user) {
        error.value = 'Login succeeded but user data is missing'
        return { success: false, message: error.value }
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

  // Register
  const register = async (email, password, full_name, verification_code) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await authAPI.register(email, password, full_name, verification_code)
      
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

  // Send verification code
  const sendVerificationCode = async (email, purpose = 'register') => {
    loading.value = true
    error.value = null
    
    try {
      const result = await authAPI.sendVerificationCode(email, purpose)
      return result
    } catch (err) {
      error.value = err.message
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  // Fetch current user info
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

  // Logout
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  // Update user profile (local only, will sync to backend)
  const updateProfile = (profileData) => {
    if (user.value) {
      user.value = { ...user.value, ...profileData }
    }
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    
    // Getters
    isAuthenticated,
    isLoggedIn,
    
    // Actions
    initAuth,
    login,
    register,
    sendVerificationCode,
    fetchUser,
    logout,
    updateProfile
  }
})
