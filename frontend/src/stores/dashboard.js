import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tasksAPI } from '../services/api.js'

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
  // priority: 0 (P0 紧急且重要 - 红色), 1 (P1 重要不紧急 - 橙色)
  //           2 (P2 紧急不重要 - 蓝色), 3 (P3 不重要不紧急 - 绿色)
  const todos = ref([
    { id: 1, title: 'Draft ECCV methodology section', completed: false, start: '2026-04-10', end: '2026-04-12', priority: 0, color: '#ff3b30' },
    { id: 2, title: 'CS305 Matrix operations assignment', completed: false, start: '2026-04-15', end: '2026-04-15', priority: 3, color: '#34c759' }
  ])

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

  const removeTodo = async (id) => {
    try {
      await tasksAPI.deleteTask(id)
      todos.value = todos.value.filter(t => t.id !== id)
    } catch (err) {
      console.error('Failed to delete task:', err)
    }
  }

  // Backend sync actions
  const loading = ref(false)
  const error = ref(null)

  // Load tasks from backend
  const loadTasks = async () => {
    loading.value = true
    error.value = null
    try {
      const tasks = await tasksAPI.getTasks()
      // Map backend task format to frontend format
      todos.value = tasks.map(task => ({
        id: task.id,
        title: task.title,
        completed: task.completed || false,
        start: task.start_date || task.start || new Date().toISOString().split('T')[0],
        end: task.end_date || task.end || task.start_date || new Date().toISOString().split('T')[0],
        startTime: task.start_time || '',
        endTime: task.end_time || '',
        priority: task.priority !== undefined ? task.priority : 2,
        color: task.color || '#007aff',
        description: task.description || ''
      }))
    } catch (err) {
      error.value = err.message
      console.error('Failed to load tasks:', err)
    } finally {
      loading.value = false
    }
  }

  // Create task on backend
  const createTaskOnBackend = async (taskData) => {
    try {
      const result = await tasksAPI.createTask({
        title: taskData.title,
        description: taskData.description || '',
        start_date: taskData.start,
        end_date: taskData.end,
        start_time: taskData.startTime || '',
        end_time: taskData.endTime || '',
        priority: taskData.priority,
        completed: taskData.completed || false
      })
      return result
    } catch (err) {
      console.error('Failed to create task on backend:', err)
      throw err
    }
  }

  // Update task on backend
  const updateTaskOnBackend = async (taskId, taskData) => {
    try {
      const result = await tasksAPI.updateTask(taskId, {
        title: taskData.title,
        description: taskData.description,
        start_date: taskData.start,
        end_date: taskData.end,
        start_time: taskData.startTime,
        end_time: taskData.endTime,
        priority: taskData.priority,
        completed: taskData.completed
      })
      return result
    } catch (err) {
      console.error('Failed to update task on backend:', err)
      throw err
    }
  }

  // Get AI study plan
  const getStudyPlan = async () => {
    try {
      const result = await tasksAPI.getStudyPlan()
      return result
    } catch (err) {
      console.error('Failed to get study plan:', err)
      throw err
    }
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
    
    loading,
    error,
    loadTasks,
    createTaskOnBackend,
    updateTaskOnBackend,
    getStudyPlan
  }
})