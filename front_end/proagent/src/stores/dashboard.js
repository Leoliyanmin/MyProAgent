import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useDashboardStore = defineStore('dashboard', () => {
  // ==============================
  // 1. 活动热力图状态 (Heatmap)
  // ==============================
  // 记录每天的“贡献值”，格式: { '2026-03-10': 5, '2026-03-11': 2 }
  const activityLog = ref({
    '2026-03-08': 3,
    '2026-03-09': 8 // 伪造的历史数据
  })

  // 获取今天的日期字符串 (YYYY-MM-DD)
  const getTodayString = () => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  // 核心 Action：记录一次有效操作（如勾选Todo、保存笔记）
  const recordActivity = (points = 1) => {
    const today = getTodayString()
    if (activityLog.value[today]) {
      activityLog.value[today] += points
    } else {
      activityLog.value[today] = points
    }
  }

  // 转换为 ECharts 需要的数据格式: [['2026-03-10', 5], ...]
  const heatmapData = computed(() => {
    return Object.entries(activityLog.value).map(([date, count]) => [date, count])
  })

  // ==============================
  // 2. TODO 状态
  // ==============================
  const todos = ref([
    { id: 1, title: 'Draft ECCV methodology section', completed: false, start: '2026-04-10', end: '2026-04-12', color: '#ff3b30' },
    { id: 2, title: 'CS305 Matrix operations assignment', completed: false, start: '2026-04-15', end: '2026-04-15', color: '#34c759' }
  ])

  const pendingTodosCount = computed(() => todos.value.filter(t => !t.completed).length)

  const addTodo = (taskPayload) => {
    if (typeof taskPayload === 'string') {
      const today = new Date().toISOString().split('T')[0]
      todos.value.unshift({ id: Date.now(), title: taskPayload, completed: false, start: today, end: today, color: '#007aff' })
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
        color: taskPayload.color || '#007aff'
      })
    }
  }

  const updateTodo = (updatedTask) => {
    const index = todos.value.findIndex(t => t.id === updatedTask.id)
    if (index !== -1) {
      todos.value.splice(index, 1, { ...todos.value[index], ...updatedTask })
    }
  }

  const toggleTodo = (id) => {
    const task = todos.value.find(t => t.id === id)
    if (task) {
      task.completed = !task.completed
      if (task.completed) {
        recordActivity(1)
      }
    }
  }

  const removeTodo = (id) => {
    todos.value = todos.value.filter(t => t.id !== id)
  }

  return {
    // 暴露出的状态与方法
    activityLog,
    heatmapData,
    recordActivity,
    
    todos,
    pendingTodosCount,
    addTodo,
    updateTodo,
    toggleTodo,
    removeTodo
  }
})