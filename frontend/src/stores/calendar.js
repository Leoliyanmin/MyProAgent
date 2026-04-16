import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useDashboardStore } from './dashboard.js'
import { schedulesAPI } from '../services/api.js'

export const useCalendarStore = defineStore('calendar', () => {
  const dashboardStore = useDashboardStore()
  
  const basicEvents = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Combine Calendar-only events and Todo events from Dashboard
  const allEvents = computed(() => {
    const calendarEvents = basicEvents.value.map(e => ({ ...e, isTodo: false }))
    const todoEvents = dashboardStore.todos.map(t => {
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
        color: t.color || '#007aff'
      }
    })
    return [...calendarEvents, ...todoEvents]
  })

  const addEvent = (event) => {
    const newEvent = { ...event, id: event.id || Date.now() }
    if (newEvent.completed === undefined) newEvent.completed = false
    if (!newEvent.color) newEvent.color = newEvent.isTodo ? '#34c759' : '#007aff'
    
    if (newEvent.isTodo) {
      dashboardStore.addTodo(newEvent)
    } else {
      basicEvents.value.push(newEvent)
    }
  }

  const updateEvent = (updatedEvent) => {
    const origInBasic = basicEvents.value.find(e => e.id === updatedEvent.id)
    const origInTodos = dashboardStore.todos.find(t => t.id === updatedEvent.id)

    if (updatedEvent.isTodo) {
      if (origInBasic) {
        // Switch from Basic to Todo
        basicEvents.value = basicEvents.value.filter(e => e.id !== updatedEvent.id)
        dashboardStore.addTodo(updatedEvent)
      } else if (origInTodos) {
        // Update existing Todo
        dashboardStore.updateTodo(updatedEvent)
      } else {
        // Create new Todo
        dashboardStore.addTodo(updatedEvent)
      }
    } else {
      if (origInTodos) {
        // Switch from Todo to Basic
        dashboardStore.removeTodo(updatedEvent.id)
        basicEvents.value.push(updatedEvent)
      } else if (origInBasic) {
        // Update existing Basic
        const idx = basicEvents.value.findIndex(e => e.id === updatedEvent.id)
        basicEvents.value.splice(idx, 1, updatedEvent)
      } else {
        // Create new Basic
        basicEvents.value.push(updatedEvent)
      }
    }
  }

  const removeEvent = async (id) => {
    const event = basicEvents.value.find(e => e.id === id)
    if (event && !event.isTodo) {
      try {
        await schedulesAPI.deleteSchedule(id)
        basicEvents.value = basicEvents.value.filter(e => e.id !== id)
      } catch (err) {
        console.error('Failed to delete schedule:', err)
      }
    }
    dashboardStore.removeTodo(id)
  }

  // Backend sync for schedules
  const loadSchedules = async () => {
    loading.value = true
    error.value = null
    try {
      const schedules = await schedulesAPI.getSchedules()
      basicEvents.value = schedules.map(schedule => ({
        id: schedule.id,
        title: schedule.title,
        start: schedule.start_date,
        end: schedule.end_date,
        startTime: schedule.start_time || '',
        endTime: schedule.end_time || '',
        isTodo: false,
        color: schedule.color || '#ff9500',
        description: schedule.description || ''
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
        start_date: eventData.start,
        end_date: eventData.end,
        start_time: eventData.startTime || '',
        end_time: eventData.endTime || '',
        color: eventData.color || '#ff9500'
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
        start_date: eventData.start,
        end_date: eventData.end,
        start_time: eventData.startTime,
        end_time: eventData.endTime,
        color: eventData.color
      })
      return result
    } catch (err) {
      console.error('Failed to update schedule:', err)
      throw err
    }
  }

  return { 
    allEvents, 
    addEvent, 
    updateEvent, 
    removeEvent,
    loading,
    error,
    loadSchedules,
    createScheduleOnBackend,
    updateScheduleOnBackend
  }
})
