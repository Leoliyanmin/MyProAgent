import { defineStore } from 'pinia'
import { ref, computed, onMounted } from 'vue'

const STORAGE_KEY = 'proagent_todos'

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
      todos.value.unshift({ id: Date.now(), title: taskPayload, completed: false, start: today, end: today, priority: 2, color: '#007aff' })
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
        color: taskPayload.color || '#007aff'
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
    console.log('[DashboardStore] Removing todo with id:', id)
    console.log('[DashboardStore] Todos before:', todos.value)
    todos.value = todos.value.filter(t => t.id !== id)
    console.log('[DashboardStore] Todos after:', todos.value)
    saveTodosToStorage(todos.value)
    console.log('[DashboardStore] Saved to localStorage')
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
    removeTodo
  }
})