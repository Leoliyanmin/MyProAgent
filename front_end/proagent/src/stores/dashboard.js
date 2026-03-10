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
    { id: 1, title: 'Draft ECCV methodology section', completed: false },
    { id: 2, title: 'CS305 Matrix operations assignment', completed: false }
  ])

  const pendingTodosCount = computed(() => todos.value.filter(t => !t.completed).length)

  const addTodo = (title) => {
    todos.value.unshift({ id: Date.now(), title, completed: false })
  }

  const toggleTodo = (task) => {
    task.completed = !task.completed
    // 如果任务变为完成状态，给今天的热力图加 1 分
    if (task.completed) {
      recordActivity(1)
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
    toggleTodo,
    removeTodo
  }
})