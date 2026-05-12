import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useDashboardStore } from './dashboard.js'
import { schedulesAPI, tisAPI, blackboardAPI } from '../services/api.js'

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
    return Number.isFinite(numericId) && numericId > 1000000000000
  }

  const addEvent = (event) => {
    const newEvent = {
      ...event,
      id: event.id || Date.now(),
      source: event.source || (event.id ? 'remote' : 'local')
    }
    if (newEvent.completed === undefined) newEvent.completed = false
    if (!newEvent.color) newEvent.color = '#007aff'

    basicEvents.value.push(newEvent)

    dashboardStore.addTodo({
      ...newEvent,
      linkedScheduleId: newEvent.id,
    })
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
      dashboardStore.updateTodo({
        ...linkedTodo,
        title: updatedEvent.title,
        start: updatedEvent.start,
        end: updatedEvent.end || updatedEvent.start,
        startTime: updatedEvent.startTime,
        endTime: updatedEvent.endTime,
        priority: updatedEvent.priority,
        color: updatedEvent.color,
      })
    }
  }

  const deleteTaskFromBackend = async (taskId) => {
    try {
      const { tasksAPI } = await import('../services/api.js')
      await tasksAPI.deleteTask(taskId)
    } catch (err) {
      console.error('Failed to delete task from backend:', err)
    }
  }

  const removeEvent = async (id) => {
    const linkedTodo = dashboardStore.todos.find(t => t.linkedScheduleId === Number(id))

    if (linkedTodo) {
      await deleteTaskFromBackend(linkedTodo.id)
      dashboardStore.removeTodo(linkedTodo.id)
    } else {
      await deleteTaskFromBackend(id)
      dashboardStore.removeTodo(id)
    }

    const shouldDeleteRemote = !isLocalGeneratedId(id)
    if (shouldDeleteRemote) {
      try {
        await schedulesAPI.deleteSchedule(id)
      } catch (err) {
        const message = String(err?.message || '').toLowerCase()
        const isNotFound = message.includes('404') || message.includes('not found')
        if (!isNotFound) {
          console.error('Failed to delete schedule:', err)
        }
      }
    }

    basicEvents.value = basicEvents.value.filter(e => e.id !== id)
  }

  // Backend sync for schedules
  const loadSchedules = async () => {
    loading.value = true
    error.value = null
    try {
      const schedules = await schedulesAPI.getSchedules()
      basicEvents.value = schedules.map(schedule => ({
        id: schedule.id ?? schedule.schedule_id,
        title: schedule.title ?? schedule.schedule_title,
        start: toDateTimeParts(schedule.start_time ?? schedule.schedule_start_time).date,
        end: toDateTimeParts(schedule.end_time ?? schedule.schedule_end_time).date,
        startTime: toDateTimeParts(schedule.start_time ?? schedule.schedule_start_time).time,
        endTime: toDateTimeParts(schedule.end_time ?? schedule.schedule_end_time).time,
        isTodo: false,
        source: schedule.source || 'remote',
        color: schedule.color || schedule.color_tag || schedule.schedule_color_tag || '#ff9500',
        description: schedule.description || schedule.schedule_description || ''
      }))
    } catch (err) {
      error.value = err.message
      console.error('Failed to load schedules:', err)
    } finally {
      loading.value = false
    }
  }

  const createScheduleOnBackend = async (eventData) => {
    try {
      const result = await schedulesAPI.createSchedule({
        title: eventData.title,
        description: eventData.description || '',
        start_time: combineDateAndTime(eventData.start, eventData.startTime, '00:00'),
        end_time: combineDateAndTime(eventData.end || eventData.start, eventData.endTime, eventData.startTime || '23:59'),
        color_tag: eventData.color || '#ff9500',
        priority: normalizePriority(eventData.priority, 'p2')
      })
      return result
    } catch (err) {
      console.error('Failed to create schedule:', err)
      throw err
    }
  }

  const updateScheduleOnBackend = async (scheduleId, eventData) => {
    try {
      const result = await schedulesAPI.updateSchedule(scheduleId, {
        title: eventData.title,
        description: eventData.description,
        start_time: combineDateAndTime(eventData.start, eventData.startTime, '00:00'),
        end_time: combineDateAndTime(eventData.end || eventData.start, eventData.endTime, eventData.startTime || '23:59'),
        color_tag: eventData.color,
        priority: eventData.priority !== undefined ? normalizePriority(eventData.priority, 'p2') : undefined
      })
      return result
    } catch (err) {
      console.error('Failed to update schedule:', err)
      throw err
    }
  }

  const importTISSchedule = async () => {
    loading.value = true
    error.value = null
    try {
      const result = await tisAPI.getSchedule()
      const tisEvents = result.events || []
      const existingIds = new Set(basicEvents.value.map(e => e.id))

      let added = 0
      const newEvents = tisEvents.filter(e => !existingIds.has(e.id)).map(e => ({
        ...e,
        id: `tis_${e.title}_${e.start}_${e.startTime}`.replace(/\s+/g, '_'),
        priority: 0,
        color: '#ff3b30',
        source: 'tis',
        isTodo: false,
      }))

      for (const ev of newEvents) {
        basicEvents.value.push(ev)
        added++
      }

      return { success: true, added, total: newEvents.length }
    } catch (err) {
      error.value = err.message
      console.error('Failed to import TIS schedule:', err)
      return { success: false, added: 0, total: 0, message: err.message }
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

      const existingIds = new Set(basicEvents.value.map(e => e.id))

      let eventsAdded = 0
      let todosAdded = 0

      for (const ev of bbEvents) {
        const id = `bb_${ev.title}`.replace(/\s+/g, '_').slice(0, 80)
        if (existingIds.has(id)) continue
        const event = {
          ...ev,
          id,
          source: 'blackboard',
          isTodo: true,
          completed: false,
        }
        if (!event.start && !event.startTime) {
          const today = new Date().toISOString().split('T')[0]
          event.start = today
          event.end = today
        }
        basicEvents.value.push(event)
        existingIds.add(id)
        eventsAdded++
      }

      const existingTodoTitles = new Set(dashboardStore.todos.map(t => t.title))
      const now = new Date()
      now.setHours(0, 0, 0, 0)
      for (const todo of bbTodos) {
        if (existingTodoTitles.has(todo.title)) continue
        const dueDate = todo.start || ''
        if (!dueDate) continue
        const dueDateObj = new Date(dueDate)
        if (isNaN(dueDateObj.getTime()) || dueDateObj < now) continue
        dashboardStore.addTodo({
          ...todo,
          priority: 0,
          color: '#ff3b30',
          linkedScheduleId: null,
        })
        existingTodoTitles.add(todo.title)
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
    currentDate,
    viewType
  }
})
