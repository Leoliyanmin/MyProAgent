// API Service Layer for connecting to Backend
// Uses Vite proxy in development, direct URL in production
// Note: Local Backend (8000) or Server Backend (8001)

const API_BASE_URL = import.meta.env.DEV ? '' : 'http://localhost:8001'

// Helper to get token from localStorage
const getToken = () => localStorage.getItem('token')

// Helper to make authenticated requests
const fetchWithAuth = async (url, options = {}) => {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`)
  }
  
  return response.json()
}

// ==================== Authentication API ====================

export const authAPI = {
  // Login
  login: async (email, password) => {
    return fetchWithAuth('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
  },
  
  // Register with verification code
  register: async (email, password, full_name, verification_code) => {
    return fetchWithAuth('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ 
        email, 
        password, 
        full_name, 
        verification_code 
      })
    })
  },
  
  // Send verification code
  sendVerificationCode: async (email, purpose = 'register') => {
    return fetchWithAuth('/auth/verification/send', {
      method: 'POST',
      body: JSON.stringify({ email, purpose })
    })
  },
  
  // Get current user info
  getCurrentUser: async () => {
    return fetchWithAuth('/auth/me')
  }
}

// ==================== Tasks API ====================

export const tasksAPI = {
  // Get all tasks
  getTasks: async () => {
    return fetchWithAuth('/tasks/')
  },
  
  // Create new task
  createTask: async (taskData) => {
    return fetchWithAuth('/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData)
    })
  },
  
  // Update task
  updateTask: async (taskId, taskData) => {
    return fetchWithAuth(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(taskData)
    })
  },
  
  // Delete task
  deleteTask: async (taskId) => {
    return fetchWithAuth(`/tasks/${taskId}`, {
      method: 'DELETE'
    })
  },
  
  // Get AI study plan
  getStudyPlan: async () => {
    return fetchWithAuth('/tasks/study-plan')
  }
}

// ==================== Schedules API ====================

export const schedulesAPI = {
  // Get all schedules
  getSchedules: async () => {
    return fetchWithAuth('/schedules/')
  },
  
  // Create new schedule
  createSchedule: async (scheduleData) => {
    return fetchWithAuth('/schedules/', {
      method: 'POST',
      body: JSON.stringify(scheduleData)
    })
  },
  
  // Update schedule
  updateSchedule: async (scheduleId, scheduleData) => {
    return fetchWithAuth(`/schedules/${scheduleId}`, {
      method: 'PUT',
      body: JSON.stringify(scheduleData)
    })
  },
  
  // Delete schedule
  deleteSchedule: async (scheduleId) => {
    return fetchWithAuth(`/schedules/${scheduleId}`, {
      method: 'DELETE'
    })
  }
}

// ==================== AI Agent API ====================

export const agentAPI = {
  // Chat with AI agent
  chat: async (message, session_id = null) => {
    return fetchWithAuth('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id })
    })
  },
  
  // Get chat history
  getHistory: async () => {
    return fetchWithAuth('/agent/history')
  }
}

// ==================== Sync API (Local ↔ Server) ====================

export const syncAPI = {
  // Push local data to server
  pushToServer: async () => {
    return fetchWithAuth('/sync/push', {
      method: 'POST'
    })
  },
  
  // Pull data from server
  pullFromServer: async () => {
    return fetchWithAuth('/sync/pull', {
      method: 'POST'
    })
  }
}

export default {
  auth: authAPI,
  tasks: tasksAPI,
  schedules: schedulesAPI,
  agent: agentAPI,
  sync: syncAPI
}
