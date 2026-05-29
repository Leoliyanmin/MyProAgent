import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useDashboardStore } from './dashboard.js'
import { eventsAPI, tisAPI, blackboardAPI } from '../services/api.js'

export const useCalendarStore = defineStore('calendar', () => {
  const dashboardStore = useDashboardStore()
  
  const basicEvents = ref([])
  const loading = ref(false)
  const error = ref(null)
  const currentDate = ref(new Date())
  const viewType = ref('month')

  const toDateTimeParts = (value) => {
    if (!value) return { date: '', time: '' }
    const raw = String(value)
    const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T')
    const [datePart = '', timePart = ''] = normalized.split('T')
    return {
      date: datePart,
      time: (timePart || '').slice(0, 5)
    }
  }

  const combineDateAndTime = (date, time, defaultTime = '00:00') => {
    if (!date) return ''
    const safeTime = time && String(time).trim() ? String(time).trim() : defaultTime
    return `${date}T${safeTime}:00`
  }

  const normalizePriority = (value, fallback = 'p2') => {
    if (value === undefined || value === null || value === '') return fallback
    if (typeof value === 'number' && value >= 0 && value <= 3) return `p${value}`

    const raw = String(value).trim().toLowerCase()
    if (/^p[0-3]$/.test(raw)) return raw
    if (/^[0-3]$/.test(raw)) return `p${raw}`
    return fallback
  }

// Combine Calendar events with Todo metadata
  const allEvents = computed(() => {
    const calendarEvents = basicEvents.value.map(e => ({ ...e, isTodo: false }))

    const todoByScheduleId = new Map()
    for (const t of dashboardStore.todos) {
      const linkedId = Number(t.linkedScheduleId)
      if (Number.isFinite(linkedId) && linkedId > 0) {
        todoByScheduleId.set(linkedId, t)
      }
    }

    const enrichedCalendarEvents = calendarEvents.map(evt => {
      const linkedTodo = todoByScheduleId.get(Number(evt.id))
      if (linkedTodo) {
        return { ...evt, completed: linkedTodo.completed, linkedScheduleId: Number(evt.id) }
      }
      return evt
    })

    const standaloneTodos = dashboardStore.todos
      .filter(t => {
        const linkedId = Number(t.linkedScheduleId)
        return !Number.isFinite(linkedId) || linkedId <= 0
      })
      .map(t => {
        const today = new Date().toISOString().split('T')[0]
        return {
          id: t.id,
          title: t.title,
          start: t.start || today,
          end: t.end || t.start || today,
          startTime: t.startTime,
          endTime: t.endTime,
          isTodo: true,
          completed: t.completed,
          priority: t.priority !== undefined ? t.priority : 2,
          color: t.color || '#34c759',
          linkedScheduleId: null,
          description: t.description || ''
        }
      })

    return [...enrichedCalendarEvents, ...standaloneTodos]
  })

  const isLocalGeneratedId = (id) => {
    const numericId = Number(id)
    if (!Number.isFinite(numericId)) return true
    return numericId > 1000000000000
  }

  const addEvent = (event) => {
    const newEvent = {
      ...event,
      id: event.id || Date.now(),
      source: event.source || (event.id ? 'remote' : 'local')
    }
    if (newEvent.completed === undefined) newEvent.completed = false
    if (!newEvent.color) newEvent.color = priorityColors[newEvent.priority] || '#007aff'

    basicEvents.value.push(newEvent)

    if (newEvent.showInTodo !== false) {
      dashboardStore.todos.unshift({
        id: newEvent.id,
        title: newEvent.title,
        completed: false,
        priority: newEvent.priority ?? 2,
        color: newEvent.color || '#007aff',
        start: newEvent.start || '',
        end: newEvent.end || newEvent.start || '',
        startTime: newEvent.startTime || '',
        endTime: newEvent.endTime || '',
        linkedScheduleId: newEvent.id,
        description: newEvent.description || '',
        source: newEvent.source || 'remote',
      })
    }
  }

  const updateEvent = (updatedEvent) => {
    const idx = basicEvents.value.findIndex(e => e.id === updatedEvent.id)
    if (idx !== -1) {
      basicEvents.value.splice(idx, 1, { ...basicEvents.value[idx], ...updatedEvent })
    } else {
      basicEvents.value.push(updatedEvent)
    }

    const linkedTodo = dashboardStore.todos.find(t => t.linkedScheduleId === Number(updatedEvent.id))
    if (linkedTodo) {
      if (updatedEvent.showInTodo === false) {
        const todoIdx = dashboardStore.todos.findIndex(t => t.id === linkedTodo.id)
        if (todoIdx !== -1) {
          dashboardStore.todos.splice(todoIdx, 1)
        }
      } else {
        dashboardStore.updateTodo({
          ...linkedTodo,
          title: updatedEvent.title,
          start: updatedEvent.start,
          end: updatedEvent.end || updatedEvent.start,
          startTime: updatedEvent.startTime,
          endTime: updatedEvent.endTime,
          priority: updatedEvent.priority,
          color: updatedEvent.color,
          completed: updatedEvent.completed,
        })
      }
    }
  }

  const removeEvent = async (id) => {
    const linkedTodo = dashboardStore.todos.find(t => t.linkedScheduleId === Number(id) || t.id === id)
    if (linkedTodo) {
      await dashboardStore.removeTodo(linkedTodo.id)
    }

    const numericId = Number(id)
    if (Number.isFinite(numericId)) {
      try { await eventsAPI.delete(id) } catch (err) { /* ignore 404 */ }
    }

    basicEvents.value = basicEvents.value.filter(e => e.id !== id)
  }

  // Backend sync for schedules
  const priorityColors = ['#ff3b30', '#ff9500', '#007aff', '#34c759', '#8e8e93']

  const loadSchedules = async () => {
    loading.value = true
    error.value = null
    try {
      const res = await eventsAPI.list()
      const events = res.events || []
      const scheduleEvents = events.map(e => ({
        id: e.event_id,
        title: e.event_title,
        start: (e.event_start_time || '').slice(0, 10),
        end: (e.event_end_time || '').slice(0, 10),
        startTime: (e.event_start_time || '').slice(11, 16) || '',
        endTime: (e.event_end_time || '').slice(11, 16) || '',
        isTodo: !!e.event_show_in_todo,
        showInTodo: !!e.event_show_in_todo,
        source: e.event_source,
        color: e.event_color_tag || priorityColors[e.event_priority] || '#007aff',
        priority: e.event_priority ?? 2,
        description: e.event_description || '',
        completed: !!e.event_is_completed,
      }))
      basicEvents.value = scheduleEvents
    } catch (err) {
      error.value = err.message
      console.error('Failed to load schedules:', err)
    } finally {
      loading.value = false
    }
  }

  const createScheduleOnBackend = async (eventData) => {
    try {
      const result = await eventsAPI.create({
        event_title: eventData.title,
        event_description: eventData.description || '',
        event_start_time: combineDateAndTime(eventData.start, eventData.startTime, '00:00'),
        event_end_time: combineDateAndTime(eventData.end || eventData.start, eventData.endTime, eventData.startTime || '23:59'),
        event_color_tag: eventData.color || priorityColors[eventData.priority] || '#007aff',
        event_priority: normalizePriority(eventData.priority, 'p2'),
        event_type: 'manual',
        event_source: 'manual',
        event_show_in_todo: eventData.showInTodo !== false ? 1 : 0,
        event_is_completed: eventData.completed ? 1 : 0,
      })
      return result
    } catch (err) {
      console.error('Failed to create event:', err)
      throw err
    }
  }

  const updateScheduleOnBackend = async (scheduleId, eventData) => {
    try {
      const result = await eventsAPI.update(scheduleId, {
        event_title: eventData.title,
        event_description: eventData.description,
        event_start_time: combineDateAndTime(eventData.start, eventData.startTime, '00:00'),
        event_end_time: combineDateAndTime(eventData.end || eventData.start, eventData.endTime, eventData.startTime || '23:59'),
        event_color_tag: eventData.color,
        event_priority: eventData.priority !== undefined ? normalizePriority(eventData.priority, 'p2') : undefined,
        event_show_in_todo: eventData.showInTodo !== undefined ? (eventData.showInTodo ? 1 : 0) : undefined,
        event_is_completed: eventData.completed !== undefined ? (eventData.completed ? 1 : 0) : undefined,
      })
      return result
    } catch (err) {
      console.error('Failed to update event:', err)
      throw err
    }
  }

  const importTISSchedule = async () => {
    loading.value = true
    error.value = null
    try {
      await loadSchedules()
      return { success: true, message: 'TIS课表已刷新' }
    } catch (err) {
      error.value = err.message
      console.error('Failed to import TIS schedule:', err)
      return { success: false, message: err.message }
    } finally {
      loading.value = false
    }
  }

  const importBlackboardAssignments = async () => {
    loading.value = true
    error.value = null
    try {
      const result = await blackboardAPI.getAssignments()
      const bbEvents = result.events || []
      const bbTodos = result.todos || []

      let eventsAdded = 0
      let todosAdded = 0

      for (const ev of bbEvents) {
        if (!ev.id) continue
        const existing = basicEvents.value.find(e => e.id === ev.id)
        if (existing) continue
        const event = {
          ...ev,
          source: 'blackboard',
          isTodo: true,
          completed: false,
        }
        if (!event.start && !event.startTime) {
          continue
        }
        basicEvents.value.push(event)
        eventsAdded++
      }

      const existingTodoIds = new Set(dashboardStore.todos.map(t => t.id))
      const now = new Date()
      now.setHours(0, 0, 0, 0)
      for (const todo of bbTodos) {
        if (!todo.id) continue
        if (existingTodoIds.has(todo.id)) continue
        const dueDate = todo.start || ''
        if (!dueDate) continue
        const dueDateObj = new Date(dueDate)
        if (isNaN(dueDateObj.getTime()) || dueDateObj < now) continue
        dashboardStore.todos.unshift({
          id: todo.id,
          title: todo.title,
          completed: false,
          start: todo.start,
          end: todo.end || todo.start,
          priority: 0,
          color: '#ff3b30',
          source: 'blackboard',
          linkedScheduleId: todo.id,
          description: todo.description || '',
        })
        existingTodoIds.add(todo.id)
        todosAdded++
      }

      return { success: true, eventsAdded, todosAdded, total: bbEvents.length }
    } catch (err) {
      error.value = err.message
      console.error('Failed to import Blackboard assignments:', err)
    return { success: false, eventsAdded: 0, todosAdded: 0, total: 0, message: err.message }
  } finally {
    loading.value = false
  }
  }

  const clearTisEvents = () => {
    basicEvents.value = basicEvents.value.filter(e => e.source !== 'tis')
  }

  const clearBlackboardEvents = () => {
    basicEvents.value = basicEvents.value.filter(e => e.source !== 'blackboard')
    for (const t of [...dashboardStore.todos]) {
      if (t.source === 'blackboard') dashboardStore.removeTodo(t.id)
    }
  }

  return {
    basicEvents,
    allEvents, 
    addEvent, 
    updateEvent, 
    removeEvent,
    loading,
    error,
    loadSchedules,
    createScheduleOnBackend,
    updateScheduleOnBackend,
    importTISSchedule,
    importBlackboardAssignments,
    clearTisEvents,
    clearBlackboardEvents,
    currentDate,
    viewType
  }
})
