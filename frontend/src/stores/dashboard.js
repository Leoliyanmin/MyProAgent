import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tasksAPI } from '../services/api.js'

const STORAGE_KEY = 'proagent_todos'
const LAYOUT_STORAGE_KEY = 'proagent_layout'

// 本地存储 helpers
const loadTodosFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (err) {
    console.error('Failed to load todos from localStorage:', err)
  }
  // 默认示例数据
  return [
    { id: 1, title: 'Draft ECCV methodology section', completed: false, start: '2026-04-10', end: '2026-04-12', priority: 0, color: '#ff3b30' },
    { id: 2, title: 'CS305 Matrix operations assignment', completed: false, start: '2026-04-15', end: '2026-04-15', priority: 3, color: '#34c759' }
  ]
}

const saveTodosToStorage = (todos) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(todos))
  } catch (err) {
    console.error('Failed to save todos to localStorage:', err)
  }
}

const DEFAULT_LAYOUT = [
  { x: 0, y: 0, w: 6, h: 5, i: '3', type: 'todo', minW: 3, minH: 4 },
  { x: 6, y: 0, w: 6, h: 5, i: '4', type: 'messages', minW: 4, minH: 3 }
]

const loadLayoutFromStorage = () => {
  try {
    const stored = localStorage.getItem(LAYOUT_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed) && parsed.length > 0) {
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

const isLocalGeneratedId = (id) => {
  const numericId = Number(id)
  return Number.isFinite(numericId) && numericId > 1000000000000
}

const extractLinkedScheduleId = (task) => {
  const explicitId = task.data_linked_schedule_id ?? task.linked_schedule_id
  if (explicitId != null) {
    const num = Number(explicitId)
    if (Number.isFinite(num) && num > 0) return num
  }
  const text = String(task.description || task.data_content_text || '')
  const match = text.match(/\[SCHEDULE_LINK:(\d+)\]/)
  if (!match) return null
  const linkedId = Number(match[1])
  return Number.isFinite(linkedId) ? linkedId : null
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
  const text = String(task.priority || task.data_priority || '').toLowerCase().trim()
  if (text === 'high' || text === 'p0' || text === 'p1') return 1
  if (text === 'low' || text === 'p3') return 3
  return 2
}

const inferColorByPriority = (priority) => {
  if (priority === 0) return '#ff3b30'
  if (priority === 1) return '#ff9500'
  if (priority === 3) return '#34c759'
  return '#007aff'
}

const mapRemoteTaskToTodo = (task) => {
  const dueDate = task.due_date || task.data_ddl_time || ''
  const { date, time } = parseDueDateTime(dueDate)
  const priority = inferPriority(task)
  const description = task.description || task.data_content_text || ''

  return {
    id: task.id ?? task.data_id,
    title: task.title ?? task.data_title ?? '未命名任务',
    completed: String(task.status || '').toLowerCase() === 'completed',
    start: date || new Date().toISOString().split('T')[0],
    end: date || new Date().toISOString().split('T')[0],
    startTime: time,
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

  const addTodo = (taskPayload) => {
    if (typeof taskPayload === 'string') {
      const today = new Date().toISOString().split('T')[0]
      todos.value.unshift({ id: Date.now(), title: taskPayload, completed: false, start: today, end: today, priority: 2, color: '#007aff', source: 'local' })
    } else {
      const today = new Date().toISOString().split('T')[0]
      todos.value.unshift({
        id: taskPayload.id || Date.now(),
        title: taskPayload.title,
        completed: taskPayload.completed || false,
        start: taskPayload.start || today,
        end: taskPayload.end || taskPayload.start || today,
        startTime: taskPayload.startTime || '',
        endTime: taskPayload.endTime || '',
        priority: taskPayload.priority !== undefined ? taskPayload.priority : 2,
        color: taskPayload.color || '#007aff',
        source: taskPayload.source || 'local',
        linkedScheduleId: taskPayload.linkedScheduleId || null,
        description: taskPayload.description || ''
      })
    }
    saveTodosToStorage(todos.value)
  }

  const updateTodo = (updatedTask) => {
    const index = todos.value.findIndex(t => t.id === updatedTask.id)
    if (index !== -1) {
      todos.value.splice(index, 1, { ...todos.value[index], ...updatedTask })
      saveTodosToStorage(todos.value)
    }
  }

  const toggleTodo = (id) => {
    const task = todos.value.find(t => t.id === id)
    if (task) {
      task.completed = !task.completed
      if (task.completed) {
        recordActivity(1)
      }
      saveTodosToStorage(todos.value)
    }
  }

  const removeTodo = (id) => {
    todos.value = todos.value.filter(t => t.id !== id)
    saveTodosToStorage(todos.value)
  }

  const loadTodosFromBackend = async () => {
    try {
      const remoteTasks = await tasksAPI.getTasks()
      const remoteTodos = (Array.isArray(remoteTasks) ? remoteTasks : []).map(mapRemoteTaskToTodo)

      // Keep local-only draft todos while syncing remote-backed items.
      const localOnlyTodos = todos.value.filter((todo) => {
        if (todo?.source === 'local') return true
        return isLocalGeneratedId(todo?.id)
      })

      todos.value = [...remoteTodos, ...localOnlyTodos]
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