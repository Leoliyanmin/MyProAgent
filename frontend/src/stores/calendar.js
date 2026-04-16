import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useDashboardStore } from './dashboard.js'

export const useCalendarStore = defineStore('calendar', () => {
  const dashboardStore = useDashboardStore()
  
  // Only store non-Todo events here
  const basicEvents = ref([
    { id: 102, title: 'Meeting with tutor', start: '2026-04-15', end: '2026-04-15', isTodo: false, color: '#ff9500' }
  ])

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

  const removeEvent = (id) => {
    basicEvents.value = basicEvents.value.filter(e => e.id !== id)
    dashboardStore.removeTodo(id)
  }

  return { allEvents, addEvent, updateEvent, removeEvent }
})
