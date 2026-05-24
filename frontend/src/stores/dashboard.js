import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { eventsAPI } from '../services/api.js'

const LAYOUT_STORAGE_KEY = 'proagent_layout'
const PINNED_EMAILS_KEY = 'proagent_pinned_emails'

const TODOS_STORAGE_KEY = 'proagent_todos'

const saveTodosToStorage = (todos) => {
  try {
    localStorage.setItem(TODOS_STORAGE_KEY, JSON.stringify(todos))
  } catch (err) {
    console.error('Failed to save todos to localStorage:', err)
  }
}

const loadTodosFromStorage = () => {
  try {
    const stored = localStorage.getItem(TODOS_STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (err) {
    return []
  }
}

const DEFAULT_LAYOUT = [
  { x: 0, y: 0, w: 6, h: 5, i: '3', type: 'todo', minW: 3, minH: 4 },
  { x: 6, y: 0, w: 6, h: 5, i: '4', type: 'messages', minW: 4, minH: 3 },
  { x: 0, y: 5, w: 12, h: 8, i: '5', type: 'markdown', minW: 6, minH: 4 }
]

const loadLayoutFromStorage = () => {
  try {
    const stored = localStorage.getItem(LAYOUT_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed) && parsed.length > 0) {
        const savedTypes = new Set(parsed.map(item => item.type))
        const newItems = DEFAULT_LAYOUT.filter(item => !savedTypes.has(item.type))
        if (newItems.length > 0) {
          const merged = [...parsed, ...newItems]
          return merged
        }
        return parsed
      }
    }
  } catch (err) {
    console.error('Failed to load layout from localStorage:', err)
  }
  return DEFAULT_LAYOUT
}

const saveLayoutToStorage = (layout) => {
  try {
    localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout))
  } catch (err) {
    console.error('Failed to save layout to localStorage:', err)
  }
}

const parseDueDateTime = (value) => {
  if (!value) {
    return { date: '', time: '' }
  }

  const raw = String(value)
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T')
  const [datePart = '', timePart = ''] = normalized.split('T')
  return {
    date: datePart,
    time: (timePart || '').slice(0, 5)
  }
}

const inferPriority = (task) => {
  const raw = task.event_priority ?? task.priority
  if (typeof raw === 'number' && raw >= 0 && raw <= 3) return raw
  const text = String(raw || '').toLowerCase().trim()
  if (text === 'p0' || text === '0') return 0
  if (text === 'high' || text === 'p1' || text === '1') return 1
  if (text === 'p2' || text === '2') return 2
  if (text === 'low' || text === 'p3' || text === '3') return 3
  return 2
}

const inferColorByPriority = (priority) => {
  if (priority === 0) return '#ff3b30'
  if (priority === 1) return '#ff9500'
  if (priority === 3) return '#34c759'
  if (priority === 4) return '#8e8e93'
  return '#007aff'
}

const mapRemoteTaskToTodo = (task) => {
  const dueDate = task.due_date || ''
  const { date, time } = parseDueDateTime(dueDate)
  const priority = inferPriority(task)
  const description = task.description || ''

  return {
    id: task.task_id,
    title: task.title || '未命名任务',
    completed: String(task.status || '').toLowerCase() === 'completed',
    start: date || new Date().toISOString().split('T')[0],
    end: date || new Date().toISOString().split('T')[0],
    startTime: '',
    endTime: time,
    priority,
    color: inferColorByPriority(priority),
    description,
    linkedScheduleId: extractLinkedScheduleId(task),
    source: 'remote'
  }
}

export const useDashboardStore = defineStore('dashboard', () => {
  // ==============================
  // 1. 活动热力图状态 (Heatmap)
  // ==============================
  // 记录每天的"贡献值"，格式：{ '2026-03-10': 5, '2026-03-11': 2 }
  const activityLog = ref({
    '2026-03-08': 3,
    '2026-03-09': 8 // 伪造的历史数据
  })

  // 获取今天的日期字符串 (YYYY-MM-DD)
  const getTodayString = () => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  // 核心 Action：记录一次有效操作（如勾选 Todo、保存笔记）
  const recordActivity = (points = 1) => {
    const today = getTodayString()
    if (activityLog.value[today]) {
      activityLog.value[today] += points
    } else {
      activityLog.value[today] = points
    }
  }

  // 转换为 ECharts 需要的数据格式：[['2026-03-10', 5], ...]
  const heatmapData = computed(() => {
    return Object.entries(activityLog.value).map(([date, count]) => [date, count])
  })

  // ==============================
  // 2. TODO 状态 (本地存储)
  // ==============================
  // priority: 0 (P0 紧急且重要 - 红色), 1 (P1 重要不紧急 - 橙色)
  //           2 (P2 紧急不重要 - 蓝色), 3 (P3 不重要不紧急 - 绿色)
  const todos = ref(loadTodosFromStorage())

  // 未完成任务数
  const pendingTodosCount = computed(() => todos.value.filter(t => !t.completed).length)

  // 根据完成状态和优先级排序的 TODO 列表
  const sortedTodos = computed(() => {
    return [...todos.value].sort((a, b) => {
      // 1. 已完成的排在最后
      if (a.completed !== b.completed) return a.completed ? 1 : -1;
      // 2. 未完成的按优先级排序 (0 最高, 3 最低)
      const priorityA = a.priority !== undefined ? a.priority : 3;
      const priorityB = b.priority !== undefined ? b.priority : 3;
      if (priorityA !== priorityB) return priorityA - priorityB;
      // 3. 优先级相同则按时间或 ID
      return b.id - a.id;
    })
  })

  const addTodo = async (taskPayload) => {
    const today = new Date().toISOString().split('T')[0]
    const title = typeof taskPayload === 'string' ? taskPayload : (taskPayload.title || '')
    const priority = typeof taskPayload === 'object' ? (taskPayload.priority ?? 2) : 2

    const dueDate = taskPayload.startTime
      ? `${taskPayload.start || today}T${taskPayload.startTime}:00`
      : (taskPayload.start || today)

    try {
      const result = await eventsAPI.create({
        event_title: title,
        event_description: (taskPayload.description || ''),
        event_start_time: dueDate || undefined,
        event_show_in_todo: 1,
        event_priority: priority,
        event_type: 'manual',
        event_source: 'manual',
      })

      const newTodo = {
        id: result.event_id,
        title: title,
        completed: taskPayload.completed === true || taskPayload.completed === 1,
        start: taskPayload.start || today,
        end: taskPayload.end || taskPayload.start || today,
        startTime: taskPayload.startTime || '',
        endTime: taskPayload.endTime || '',
        priority: priority,
        color: taskPayload.color || inferColorByPriority(priority),
        source: 'remote',
        linkedScheduleId: taskPayload.linkedScheduleId || null,
        description: taskPayload.description || '',
      }

      todos.value.unshift(newTodo)
      saveTodosToStorage(todos.value)
    } catch (err) {
      console.error('Failed to create todo:', err)
    }
  }

  const updateTodo = (updatedTask) => {
    const index = todos.value.findIndex(t => t.id === updatedTask.id)
    if (index !== -1) {
      todos.value.splice(index, 1, { ...todos.value[index], ...updatedTask })
      saveTodosToStorage(todos.value)
    }
  }

  const toggleTodo = async (id) => {
    const task = todos.value.find(t => t.id === id)
    if (!task) return

    task.completed = !task.completed
    if (task.completed) {
      recordActivity(1)
    }
    saveTodosToStorage(todos.value)

    try {
      await eventsAPI.update(id, {
        event_is_completed: task.completed ? 1 : 0
      })
    } catch (err) {
      console.error('Failed to sync todo status:', err)
    }
  }

  const removeTodo = async (id) => {
    try {
      await eventsAPI.delete(id)
    } catch (err) {
      console.error('Failed to delete event:', err)
    }
    todos.value = todos.value.filter(t => t.id !== id)
    saveTodosToStorage(todos.value)
  }

  const loadTodosFromBackend = async () => {
    try {
      const res = await eventsAPI.list({ show_in_todo: '1' })
      const remoteEvents = res.events || []
      const remoteTodos = remoteEvents.map(e => ({
        id: e.event_id,
        title: e.event_title,
        completed: !!e.event_is_completed,
        priority: e.event_priority ?? 2,
        color: inferColorByPriority(e.event_priority ?? 2),
        source: e.event_source,
        description: e.event_description || '',
        start: e.event_start_time || '',
        end: e.event_end_time || '',
        linkedScheduleId: null,
      }))

      todos.value = remoteTodos
      saveTodosToStorage(todos.value)
      return { success: true, count: remoteTodos.length }
    } catch (err) {
      console.error('Failed to load todos from backend:', err)
      return { success: false, message: err?.message || '加载任务失败' }
    }
  }

// ==============================
  // 3. 布局配置状态 (本地存储)
  // ==============================
  const layoutConfig = ref(loadLayoutFromStorage())

  const saveLayout = () => {
    saveLayoutToStorage(layoutConfig.value)
  }

  const resetLayout = () => {
    layoutConfig.value = DEFAULT_LAYOUT
    saveLayoutToStorage(layoutConfig.value)
  }

  // ==============================
  // 4. 主页置顶邮件 (Pinned Emails)
  // ==============================
  const pinnedEmails = ref(loadPinnedEmailsFromStorage())

  function loadPinnedEmailsFromStorage() {
    try {
      const stored = localStorage.getItem(PINNED_EMAILS_KEY)
      return stored ? JSON.parse(stored) : []
    } catch { return [] }
  }

  function savePinnedEmails() {
    localStorage.setItem(PINNED_EMAILS_KEY, JSON.stringify(pinnedEmails.value))
  }

  function pinEmail(email) {
    const exists = pinnedEmails.value.some(e => e.id === email.id)
    if (!exists) {
      pinnedEmails.value.unshift({ ...email, pinnedAt: new Date().toISOString() })
      savePinnedEmails()
    }
  }

  function unpinEmail(id) {
    pinnedEmails.value = pinnedEmails.value.filter(e => e.id !== id)
    savePinnedEmails()
  }

  function isEmailPinned(id) {
    return pinnedEmails.value.some(e => e.id === id)
  }

  return {
    activityLog, heatmapData, recordActivity,
    todos, sortedTodos, pendingTodosCount, addTodo, updateTodo, toggleTodo, removeTodo, loadTodosFromBackend,
    layoutConfig, saveLayout, resetLayout,
    pinnedEmails, pinEmail, unpinEmail, isEmailPinned,
  }

  return {
    activityLog,
    heatmapData,
    recordActivity,
    
    todos,
    sortedTodos,
    pendingTodosCount,
    addTodo,
    updateTodo,
    toggleTodo,
    removeTodo,
    loadTodosFromBackend,

    layoutConfig,
    saveLayout,
    resetLayout
  }
})