import { beforeEach, describe, expect, it } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBehaviorProfileStore } from '@/stores/behaviorProfile.js'

describe('behavior profile store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('records behavior events and exposes a derived profile', () => {
    const store = useBehaviorProfileStore()

    store.recordBehaviorEvent('dashboard_auto_arranged', { module: 'dashboard' })
    store.recordBehaviorEvent('dashboard_template_saved', { module: 'dashboard' })

    expect(store.events.length).toBe(2)
    expect(store.hasBehaviorData).toBe(true)
    expect(store.profile.indicators.automation_preference).toBeGreaterThan(0.3)
  })

  it('persists behavior events to localStorage', () => {
    const store = useBehaviorProfileStore()
    store.recordBehaviorEvent('calendar_event_created', { module: 'calendar' })

    const saved = JSON.parse(localStorage.getItem('proagent_behavior_events'))
    expect(saved[0].type).toBe('calendar_event_created')
  })
})
