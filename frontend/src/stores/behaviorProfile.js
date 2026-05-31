import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { computeBehaviorProfile } from '../utils/behaviorProfile.js'

const STORAGE_KEY = 'proagent_behavior_events'
const MAX_EVENTS = 800

const loadEvents = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    const parsed = stored ? JSON.parse(stored) : []
    return Array.isArray(parsed) ? parsed : []
  } catch (err) {
    console.error('Failed to load behavior events:', err)
    return []
  }
}

const saveEvents = (events) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(-MAX_EVENTS)))
  } catch (err) {
    console.error('Failed to save behavior events:', err)
  }
}

export const useBehaviorProfileStore = defineStore('behaviorProfile', () => {
  const events = ref(loadEvents())

  const profile = computed(() => computeBehaviorProfile(events.value))
  const hasBehaviorData = computed(() => profile.value.recentEventCount > 0)

  const recordBehaviorEvent = (type, metadata = {}) => {
    if (!type) return null
    const event = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type,
      timestamp: new Date().toISOString(),
      metadata
    }
    events.value.push(event)
    if (events.value.length > MAX_EVENTS) {
      events.value.splice(0, events.value.length - MAX_EVENTS)
    }
    saveEvents(events.value)
    return event
  }

  const clearBehaviorEvents = () => {
    events.value = []
    saveEvents(events.value)
  }

  return {
    events,
    profile,
    hasBehaviorData,
    recordBehaviorEvent,
    clearBehaviorEvents
  }
})
