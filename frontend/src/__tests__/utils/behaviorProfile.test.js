import { describe, expect, it } from 'vitest'
import { computeBehaviorProfile } from '@/utils/behaviorProfile.js'

const makeEvent = (type, hour, metadata = {}) => ({
  type,
  timestamp: `2026-05-30T${String(hour).padStart(2, '0')}:00:00.000Z`,
  metadata
})

describe('computeBehaviorProfile', () => {
  it('derives work preferences and behavior patterns from recent events', () => {
    const profile = computeBehaviorProfile([
      makeEvent('dashboard_auto_arranged', 8, { module: 'dashboard' }),
      makeEvent('dashboard_template_saved', 9, { module: 'dashboard' }),
      makeEvent('calendar_event_created', 14, { module: 'calendar' }),
      makeEvent('todo_completed', 15, { module: 'todo' }),
      makeEvent('widget_toggled', 20, { module: 'dashboard' })
    ], new Date('2026-05-30T22:00:00.000Z'))

    expect(profile.recentEventCount).toBe(5)
    expect(profile.workPreferenceText).toContain('结构化')
    expect(profile.behaviorPatternText).toContain('工作台')
    expect(profile.indicators.organization_driven).toBeGreaterThan(0.5)
  })

  it('ignores events outside the recent window', () => {
    const profile = computeBehaviorProfile([
      {
        type: 'dashboard_auto_arranged',
        timestamp: '2026-04-01T08:00:00.000Z',
        metadata: { module: 'dashboard' }
      }
    ], new Date('2026-05-30T22:00:00.000Z'))

    expect(profile.eventCount).toBe(1)
    expect(profile.recentEventCount).toBe(0)
  })
})
