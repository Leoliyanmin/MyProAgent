import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock the API module before importing the store
vi.mock('@/services/api.js', () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn(),
    sendVerificationCode: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}))

import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/services/api'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts unauthenticated', () => {
      const auth = useAuthStore()
      expect(auth.isAuthenticated).toBe(false)
      expect(auth.user).toBeNull()
      expect(auth.token).toBeNull()
      expect(auth.loading).toBe(false)
      expect(auth.error).toBeNull()
    })

    it('restores token from localStorage', () => {
      localStorage.setItem('token', 'stored-token')
      const auth = useAuthStore()
      expect(auth.token).toBe('stored-token')
      expect(auth.isAuthenticated).toBe(true)
    })
  })

  describe('login', () => {
    it('sets token and user on successful login', async () => {
      authAPI.login.mockResolvedValue({
        success: true,
        access_token: 'test-token',
      })
      authAPI.getCurrentUser.mockResolvedValue({
        id: 'user@test.com',
        email: 'user@test.com',
        full_name: 'Test User',
      })

      const auth = useAuthStore()
      const result = await auth.login('user@test.com', 'password')

      expect(result.success).toBe(true)
      expect(auth.token).toBe('test-token')
      expect(auth.isAuthenticated).toBe(true)
      expect(localStorage.getItem('token')).toBe('test-token')
    })

    it('sets error on failed login', async () => {
      authAPI.login.mockResolvedValue({
        success: false,
        message: 'Invalid credentials',
      })

      const auth = useAuthStore()
      const result = await auth.login('user@test.com', 'wrong')

      expect(result.success).toBe(false)
      expect(auth.error).toBe('Invalid credentials')
      expect(auth.isAuthenticated).toBe(false)
    })

    it('handles network errors during login', async () => {
      authAPI.login.mockRejectedValue(new Error('Network error'))

      const auth = useAuthStore()
      const result = await auth.login('user@test.com', 'password')

      expect(result.success).toBe(false)
      expect(auth.error).toBe('Network error')
    })
  })

  describe('register', () => {
    it('returns success on successful registration', async () => {
      authAPI.register.mockResolvedValue({
        success: true,
        message: 'Registration successful',
      })

      const auth = useAuthStore()
      const result = await auth.register('user@test.com', 'Password1', 'Test User', '123456')

      expect(result.success).toBe(true)
    })

    it('sets error on failed registration', async () => {
      authAPI.register.mockResolvedValue({
        success: false,
        message: 'Email already exists',
      })

      const auth = useAuthStore()
      const result = await auth.register('user@test.com', 'Password1', 'Test User', '123456')

      expect(result.success).toBe(false)
      expect(auth.error).toBe('Email already exists')
    })
  })

  describe('logout', () => {
    it('clears user, token, and localStorage', async () => {
      authAPI.login.mockResolvedValue({
        success: true,
        access_token: 'test-token',
      })
      authAPI.getCurrentUser.mockResolvedValue({ id: 'user@test.com' })

      const auth = useAuthStore()
      await auth.login('user@test.com', 'password')

      auth.logout()

      expect(auth.user).toBeNull()
      expect(auth.token).toBeNull()
      expect(auth.isAuthenticated).toBe(false)
      expect(localStorage.getItem('token')).toBeNull()
    })
  })

  describe('updateProfile', () => {
    it('merges profile data into current user', async () => {
      authAPI.login.mockResolvedValue({
        success: true,
        access_token: 'test-token',
      })
      authAPI.getCurrentUser.mockResolvedValue({
        id: 'user@test.com',
        email: 'user@test.com',
        full_name: 'Old Name',
      })

      const auth = useAuthStore()
      await auth.login('user@test.com', 'password')

      auth.updateProfile({ full_name: 'New Name', bio: 'Hello' })

      expect(auth.user.full_name).toBe('New Name')
      expect(auth.user.bio).toBe('Hello')
      expect(auth.user.email).toBe('user@test.com')
    })
  })
})
