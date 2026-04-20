// MSW Handlers
// Mock API handlers for all backend endpoints

import { http, HttpResponse } from 'msw'
import {
  mockUser,
  mockTasks,
  mockSchedules,
  mockAgentHistory,
  mockStudyPlan,
  mockToken
} from './data.js'

// Helper to simulate network delay
const delay = (ms = 300) => new Promise(resolve => setTimeout(resolve, ms))

// Helper to check authorization header
const checkAuth = (request) => {
  const authHeader = request.headers.get('Authorization')
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null
  }
  return authHeader.replace('Bearer ', '')
}

// Generate unique ID
let taskIdCounter = 100
let scheduleIdCounter = 100
let messageIdCounter = 100

export const handlers = [
  // ==================== Authentication Handlers ====================

  http.post('/auth/login', async ({ request }) => {
    await delay()
    return HttpResponse.json({
      success: true,
      access_token: mockToken,
      token_type: 'bearer',
      user: mockUser
    })
  }),

  http.post('/auth/register', async ({ request }) => {
    await delay()
    const body = await request.json()
    return HttpResponse.json({
      success: true,
      message: 'User registered successfully',
      user: {
        id: 2,
        email: body.email,
        full_name: body.full_name,
        created_at: new Date().toISOString()
      }
    }, { status: 201 })
  }),

  http.post('/auth/verification/send', async ({ request }) => {
    await delay(500)
    return HttpResponse.json({
      success: true,
      message: 'Verification code sent to your email',
      mock_code: '123456'
    })
  }),

  // GET /auth/me
  http.get('/auth/me', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json(mockUser)
  }),

  // ==================== Tasks Handlers ====================

  // GET /tasks/
  http.get('/tasks/', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json(mockTasks)
  }),

  // POST /tasks/
  http.post('/tasks/', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const newTask = {
      id: ++taskIdCounter,
      ...body,
      created_at: new Date().toISOString()
    }

    mockTasks.push(newTask)

    return HttpResponse.json(newTask, { status: 201 })
  }),

  // PUT /tasks/:id
  http.put('/tasks/:id', async ({ request, params }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const taskId = parseInt(params.id)
    const taskIndex = mockTasks.findIndex(t => t.id === taskId)

    if (taskIndex === -1) {
      return HttpResponse.json(
        { detail: 'Task not found' },
        { status: 404 }
      )
    }

    mockTasks[taskIndex] = {
      ...mockTasks[taskIndex],
      ...body,
      id: taskId
    }

    return HttpResponse.json(mockTasks[taskIndex])
  }),

  // DELETE /tasks/:id
  http.delete('/tasks/:id', async ({ request, params }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const taskId = parseInt(params.id)
    const taskIndex = mockTasks.findIndex(t => t.id === taskId)

    if (taskIndex === -1) {
      return HttpResponse.json(
        { detail: 'Task not found' },
        { status: 404 }
      )
    }

    mockTasks.splice(taskIndex, 1)

    return HttpResponse.json({ message: 'Task deleted successfully' })
  }),

  // GET /tasks/study-plan
  http.get('/tasks/study-plan', async ({ request }) => {
    await delay(800)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json(mockStudyPlan)
  }),

  // ==================== Schedules Handlers ====================

  // GET /schedules/
  http.get('/schedules/', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json(mockSchedules)
  }),

  // POST /schedules/
  http.post('/schedules/', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const newSchedule = {
      id: ++scheduleIdCounter,
      ...body,
      created_at: new Date().toISOString()
    }

    mockSchedules.push(newSchedule)

    return HttpResponse.json(newSchedule, { status: 201 })
  }),

  // PUT /schedules/:id
  http.put('/schedules/:id', async ({ request, params }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const scheduleId = parseInt(params.id)
    const scheduleIndex = mockSchedules.findIndex(s => s.id === scheduleId)

    if (scheduleIndex === -1) {
      return HttpResponse.json(
        { detail: 'Schedule not found' },
        { status: 404 }
      )
    }

    mockSchedules[scheduleIndex] = {
      ...mockSchedules[scheduleIndex],
      ...body,
      id: scheduleId
    }

    return HttpResponse.json(mockSchedules[scheduleIndex])
  }),

  // DELETE /schedules/:id
  http.delete('/schedules/:id', async ({ request, params }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const scheduleId = parseInt(params.id)
    const scheduleIndex = mockSchedules.findIndex(s => s.id === scheduleId)

    if (scheduleIndex === -1) {
      return HttpResponse.json(
        { detail: 'Schedule not found' },
        { status: 404 }
      )
    }

    mockSchedules.splice(scheduleIndex, 1)

    return HttpResponse.json({ message: 'Schedule deleted successfully' })
  }),

  // ==================== AI Agent Handlers ====================

  // POST /agent/chat
  http.post('/agent/chat', async ({ request }) => {
    await delay(1000)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const userMessage = body.message || ''

    // Generate a contextual mock response
    let responseMessage = 'I understand your request. How can I help you further?'

    if (userMessage.toLowerCase().includes('task') || userMessage.toLowerCase().includes('任务')) {
      responseMessage = `I see you have ${mockTasks.filter(t => !t.completed).length} pending tasks. Would you like me to help prioritize them or create a study plan?`
    } else if (userMessage.toLowerCase().includes('schedule') || userMessage.toLowerCase().includes('日程')) {
      responseMessage = `You have ${mockSchedules.length} events scheduled. Your next event is "${mockSchedules[0]?.title || 'None'}" at ${mockSchedules[0]?.start_time ? new Date(mockSchedules[0].start_time).toLocaleTimeString() : 'N/A'}.`
    } else if (userMessage.toLowerCase().includes('hello') || userMessage.toLowerCase().includes('hi')) {
      responseMessage = 'Hello! I\'m your AI assistant. I can help you manage tasks, schedules, and provide study plans. What would you like to work on today?'
    }

    const sessionId = body.session_id || `session-${Date.now()}`

    mockAgentHistory.push({
      id: ++messageIdCounter,
      session_id: sessionId,
      role: 'user',
      message: userMessage,
      created_at: new Date(Date.now() - 1000).toISOString()
    })
    mockAgentHistory.push({
      id: ++messageIdCounter,
      session_id: sessionId,
      role: 'assistant',
      message: responseMessage,
      created_at: new Date().toISOString()
    })

    return HttpResponse.json({
      response: responseMessage,
      thought_trace: [],
      tool_calls: [],
      requires_confirmation: false
    })
  }),

  // POST /agent/chat/file-manager
  http.post('/agent/chat/file-manager', async ({ request }) => {
    await delay(1000)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const userMessage = body.message || ''
    const workingDirectory = body.working_directory || ''

    if (!workingDirectory) {
      return HttpResponse.json(
        { detail: 'working_directory is required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      response: `已在目录 ${workingDirectory} 接收指令: ${userMessage}`,
      thought_trace: [],
      tool_calls: ['list_dir'],
      requires_confirmation: false
    })
  }),

  // POST /agent/file-manager/list
  http.post('/agent/file-manager/list', async ({ request }) => {
    await delay(400)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    const workingDirectory = body.working_directory || ''
    const relativePath = body.relative_path || ''

    if (!workingDirectory) {
      return HttpResponse.json(
        { detail: 'working_directory is required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      working_directory: workingDirectory,
      current_directory: relativePath ? `${workingDirectory}/${relativePath}` : workingDirectory,
      relative_path: relativePath,
      parent_relative_path: relativePath.includes('/')
        ? relativePath.split('/').slice(0, -1).join('/')
        : (relativePath ? '' : null),
      entries: [
        {
          name: 'Documents',
          relative_path: relativePath ? `${relativePath}/Documents` : 'Documents',
          is_directory: true,
          size: null,
          modified_at: new Date().toISOString()
        },
        {
          name: 'todo.md',
          relative_path: relativePath ? `${relativePath}/todo.md` : 'todo.md',
          is_directory: false,
          size: 128,
          modified_at: new Date().toISOString()
        }
      ]
    })
  }),

  // POST /agent/file-manager/file/create
  http.post('/agent/file-manager/file/create', async ({ request }) => {
    await delay(250)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    if (!body.working_directory || !body.filename) {
      return HttpResponse.json(
        { detail: 'working_directory and filename are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: `创建成功: ${body.filename}`,
      working_directory: body.working_directory,
      relative_path: body.relative_path || '',
      filename: body.filename,
      new_filename: null
    })
  }),

  // POST /agent/file-manager/file/rename
  http.post('/agent/file-manager/file/rename', async ({ request }) => {
    await delay(250)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    if (!body.working_directory || !body.old_filename || !body.new_filename) {
      return HttpResponse.json(
        { detail: 'working_directory, old_filename and new_filename are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: `重命名成功: ${body.old_filename} -> ${body.new_filename}`,
      working_directory: body.working_directory,
      relative_path: body.relative_path || '',
      filename: body.old_filename,
      new_filename: body.new_filename
    })
  }),

  // POST /agent/file-manager/file/delete
  http.post('/agent/file-manager/file/delete', async ({ request }) => {
    await delay(250)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = await request.json()
    if (!body.working_directory || !body.filename) {
      return HttpResponse.json(
        { detail: 'working_directory and filename are required' },
        { status: 400 }
      )
    }

    return HttpResponse.json({
      success: true,
      message: `删除成功: ${body.filename}`,
      working_directory: body.working_directory,
      relative_path: body.relative_path || '',
      filename: body.filename,
      new_filename: null
    })
  }),

  // GET /agent/history
  http.get('/agent/history', async ({ request }) => {
    await delay()
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json(mockAgentHistory)
  }),

  // ==================== Sync Handlers ====================

  // POST /sync/push
  http.post('/sync/push', async ({ request }) => {
    await delay(500)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      message: 'Data pushed to server successfully',
      synced_items: {
        tasks: mockTasks.length,
        schedules: mockSchedules.length
      },
      timestamp: new Date().toISOString()
    })
  }),

  // POST /sync/pull
  http.post('/sync/pull', async ({ request }) => {
    await delay(500)
    const token = checkAuth(request)

    if (!token) {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      message: 'Data pulled from server successfully',
      data: {
        tasks: mockTasks,
        schedules: mockSchedules
      },
      timestamp: new Date().toISOString()
    })
  })
]
