// API Service Layer for connecting to Backend
// Uses Vite proxy in development, direct URL in production
// Note: Local Backend (8000) or Server Backend (8001)

import { getTokenSync, clearAuth } from './auth-storage.js'

const API_BASE_URL = import.meta.env.DEV ? '' : 'http://localhost:8001'

// Helper to get token from auth-storage (supports both localStorage and Tauri store)
const getToken = () => getTokenSync()

// Helper to make requests without authentication
const fetchWithoutAuth = async (url, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
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
    if (response.status === 401) {
      // Clear stale/invalid token to force a clean re-login flow.
      localStorage.removeItem('token')
      window.dispatchEvent(new CustomEvent('auth:required'))
      throw new Error('登录状态已失效，请重新登录')
    }
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`)
  }

  return response.json()
}

// Helper to tolerate transient backend reloads in development.
const fetchWithAuthRetry = async (url, options = {}, retryCount = 1, retryDelayMs = 350) => {
  let lastError = null

  for (let attempt = 0; attempt <= retryCount; attempt += 1) {
    try {
      return await fetchWithAuth(url, options)
    } catch (error) {
      lastError = error
      const isLastAttempt = attempt === retryCount
      if (isLastAttempt) break

      await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
    }
  }

  throw lastError || new Error('Request failed')
}

// ==================== Authentication API ====================

export const authAPI = {
  // Login
  login: async (email, password) => {
    return fetchWithoutAuth('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
  },

  // Register with verification code
  register: async (email, password, full_name, verification_code) => {
    return fetchWithoutAuth('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        confirm_password: password,
        full_name,
        verification_code
      })
    })
  },

  // Send verification code
  sendVerificationCode: async (email, purpose = 'register') => {
    return fetchWithoutAuth('/auth/verification/send', {
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
    const token = getToken()
    const numericId = Number(taskId)
    const isLocalGeneratedId = Number.isFinite(numericId) && numericId > 1000000000000

    // 本地临时任务（Date.now()）或未登录场景不触发后端删除，避免 401 噪音
    if (!token || isLocalGeneratedId) {
      return {
        success: true,
        message: 'Skip remote delete for local task',
        skipped: true,
      }
    }

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
  // Local Agent API (direct connection to localagent on port 8000)
  local: {
    getBaseUrl: () => 'http://127.0.0.1:8000',

    getStatus: async () => {
      const response = await fetch(`${agentAPI.local.getBaseUrl()}/api/status`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    },

    testConnection: async () => {
      const response = await fetch(`${agentAPI.local.getBaseUrl()}/api/test`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    },

    updateConfig: async (config) => {
      const response = await fetch(`${agentAPI.local.getBaseUrl()}/api/config/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    }
  },

  // Backend Agent API (authenticated, port 8002)
  backend: {
    getStatus: async () => {
      return fetchWithAuth('/agent/status')
    },

    testConnection: async () => {
      return fetchWithAuth('/agent/test')
    },

    updateConfig: async (config) => {
      return fetchWithAuth('/agent/config/update', {
        method: 'POST',
        body: JSON.stringify(config)
      })
    }
  },

  // Server Agent API (authenticated)
  // Chat with AI agent (original)
  chat: async (message, session_id = null) => {
    return fetchWithAuth('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id })
    })
  },

  chatLocal: async (message, session_id = null, options = {}) => {
    return fetchWithAuth('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id }),
      signal: options.signal,
    })
  },

  chatWithWorkingDirectory: async (message, working_directory, session_id = 'file_manager', options = {}) => {
    return fetchWithAuth('/agent/chat/file-manager', {
      method: 'POST',
      body: JSON.stringify({ message, working_directory, session_id }),
      signal: options.signal,
    })
  },

  listWorkingDirectory: async (working_directory, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/list', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path })
    }, 2)
  },

  createFileByName: async (working_directory, filename, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/file/create', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path, filename })
    }, 2)
  },

  renameFileByName: async (working_directory, old_filename, new_filename, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/file/rename', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path, old_filename, new_filename })
    }, 2)
  },

  deleteFileByName: async (working_directory, filename, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/file/delete', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path, filename })
    }, 2)
  },

  deleteFileByPath: async (path, working_directory = null) => {
    return fetchWithAuthRetry('/agent/file-manager/file/delete-path', {
      method: 'POST',
      body: JSON.stringify({ path, working_directory })
    }, 2)
  },

  readFileByName: async (working_directory, filename, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/file/read', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path, filename })
    }, 2)
  },

  updateFileByName: async (working_directory, filename, content, relative_path = '') => {
    return fetchWithAuthRetry('/agent/file-manager/file/update', {
      method: 'POST',
      body: JSON.stringify({ working_directory, relative_path, filename, content })
    }, 2)
  },

  getHistory: async (session_id) => {
    return fetchWithAuth(`/agent/history/${session_id}`)
  },

  getLocalSession: async (sessionId) => {
    return fetchWithAuth(`/agent/session/${sessionId}`)
  },

  clearLocalSession: async (sessionId) => {
    return fetchWithAuth(`/agent/session/${sessionId}/clear`, {
      method: 'POST'
    })
  },

  getMemory: async () => {
    return fetchWithAuth('/agent/memory')
  },

  consolidateMemory: async () => {
    return fetchWithAuth('/agent/memory/consolidate', {
      method: 'POST'
    })
  },

  getStatus: async () => {
    return fetchWithAuth('/agent/status')
  },

  // WebSocket connection for real-time chat
  connectWebSocket: (sessionId, onMessage, onTool, onError, onDone) => {
    const token = getToken()
    if (!token) {
      onError?.({ message: '未登录' })
      return null
    }

    const wsUrl = import.meta.env.DEV
      ? `ws://localhost:8002/agent/ws/${sessionId}?token=${token}`
      : `wss://your-production-server.com/agent/ws/${sessionId}?token=${token}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[Agent] WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'message':
            onMessage?.(data)
            break
          case 'stream':
            onMessage?.({ role: data.role || 'assistant', content: data.content, isStream: true })
            break
          case 'tool':
            onTool?.({ phase: 'tool_call', summary: `调用工具: ${data.tool}`, durationMs: 0, tool: data.tool })
            break
          case 'tool_start':
            onTool?.({ phase: 'tool_call', summary: `正在调用: ${data.tool}`, durationMs: 0, tool: data.tool, args: data.args })
            break
          case 'error':
            onError?.(data)
            break
          case 'done':
            onDone?.(data)
            break
          case 'pong':
            break
          default:
            console.log('[Agent] Unknown message type:', data.type)
        }
      } catch (err) {
        console.error('[Agent] Failed to parse message:', err, event.data)
      }
    }

    ws.onerror = (error) => {
      console.error('[Agent] WebSocket error:', error)
      onError?.({ message: '连接错误，请检查网络' })
    }

    ws.onclose = (event) => {
      console.log('[Agent] WebSocket closed:', event.code, event.reason)
      if (event.code !== 1000) {
        onError?.({ message: '连接断开' })
      }
    }

    return ws
  }
}

// ==================== TIS API ====================

export const tisAPI = {
  getSchedule: async () => {
    return fetchWithAuth('/api/v1/tis/schedule')
  },
  getStatus: async () => {
    return fetchWithAuth('/api/v1/tis/status')
  },
  unbind: async () => {
    return fetchWithAuth('/api/v1/tis/unbind', { method: 'POST' })
  }
}

// ==================== Blackboard API ====================

export const blackboardAPI = {
  getAssignments: async () => {
    return fetchWithAuth('/api/v1/blackboard/assignments')
  },
  getStatus: async () => {
    return fetchWithAuth('/api/v1/blackboard/status')
  },
  unbind: async () => {
    return fetchWithAuth('/api/v1/blackboard/unbind', { method: 'POST' })
  }
}

// ==================== Email API ====================

export const emailAPI = {
  getStatus: async () => {
    return fetchWithAuth('/api/v1/email/status')
  },
  bind: async (emailAddress, appPassword) => {
    return fetchWithAuth('/api/v1/email/bind', {
      method: 'POST',
      body: JSON.stringify({ email_address: emailAddress, app_password: appPassword })
    })
  },
  sync: async (maxMessages = 50) => {
    return fetchWithAuth(`/api/v1/email/sync?max_messages=${maxMessages}`, {
      method: 'POST'
    })
  },
  unbind: async () => {
    return fetchWithAuth('/api/v1/email/unbind', { method: 'POST' })
  },
  getMessages: async () => {
    return fetchWithAuth('/api/v1/email/messages')
  },
  send: async (title, context, receiver) => {
    return fetchWithAuth('/api/v1/email/send', {
      method: 'POST',
      body: JSON.stringify({ title, context, receiver })
    })
  },
  deleteMessage: async (messageId) => {
    return fetchWithAuth(`/api/v1/email/messages/${messageId}`, {
      method: 'DELETE'
    })
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

// ==================== Settings API (用户设置) ====================

export const settingsAPI = {
  get: async () => {
    return fetchWithAuth('/auth/settings')
  },
  update: async (fields) => {
    return fetchWithAuth('/auth/settings', {
      method: 'PUT',
      body: JSON.stringify(fields)
    })
  },

  // API Key management
  getApiKeys: async () => {
    return fetchWithAuth('/auth/settings/api-keys')
  },
  saveApiKey: async (provider, api_key, api_base) => {
    return fetchWithAuth('/auth/settings/api-keys', {
      method: 'PUT',
      body: JSON.stringify({ provider, api_key, api_base })
    })
  },
  deleteApiKey: async (provider) => {
    return fetchWithAuth(`/auth/settings/api-keys/${encodeURIComponent(provider)}`, {
      method: 'DELETE'
    })
  },
  testApiKey: async (provider, api_key, api_base) => {
    return fetchWithAuth('/auth/settings/api-keys/test', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key, api_base })
    })
  }
}

// ==================== Profile API (用户画像) ====================

export const profileAPI = {
  getProfile: async () => {
    return fetchWithAuth('/agent/profile')
  },

  getMBTI: async () => {
    return fetchWithAuth('/agent/profile/mbti')
  },

  getInteractions: async (limit = 20, offset = 0) => {
    return fetchWithAuth(`/agent/profile/interactions?limit=${limit}&offset=${offset}`)
  },

  getInteractionDetail: async (conversationId) => {
    return fetchWithAuth(`/agent/profile/interactions/${conversationId}`)
  },

  reanalyze: async () => {
    return fetchWithAuth('/agent/profile/reanalyze', {
      method: 'POST'
    })
  },

  deleteInteraction: async (conversationId) => {
    return fetchWithAuth(`/agent/profile/interactions/${conversationId}`, {
      method: 'DELETE'
    })
  }
}

export default {
  auth: authAPI,
  tasks: tasksAPI,
  schedules: schedulesAPI,
  agent: agentAPI,
  sync: syncAPI,
  profile: profileAPI,
  tis: tisAPI,
  blackboard: blackboardAPI,
  email: emailAPI,
}
