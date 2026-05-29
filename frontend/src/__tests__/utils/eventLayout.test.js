import { describe, expect, it } from 'vitest'

import { computeEventLayout } from '@/utils/eventLayout'

describe('computeEventLayout', () => {
  it('keeps long containing events full width behind Apple-style overlaps', () => {
    const events = computeEventLayout([
      { id: 'long', title: 'New Event', startTime: '08:00', endTime: '13:00' },
      { id: 'left', title: 'New Event', startTime: '09:00', endTime: '10:00' },
      { id: 'right', title: 'New Event', startTime: '09:00', endTime: '10:00' },
    ])

    const long = events.find(event => event.id === 'long')
    const left = events.find(event => event.id === 'left')
    const right = events.find(event => event.id === 'right')

    expect(long.left).toBeUndefined()
    expect(long.width).toBeUndefined()
    expect(long.zIndex).toBeLessThan(left.zIndex)
    expect(left.width).toBe('50%')
    expect(right.width).toBe('50%')
    expect(new Set([left.left, right.left])).toEqual(new Set(['0%', '50%']))
  })

  it('still splits peer events that partially overlap', () => {
    const events = computeEventLayout([
      { id: 'first', startTime: '08:00', endTime: '10:00' },
      { id: 'second', startTime: '09:00', endTime: '11:00' },
    ])

    expect(events.find(event => event.id === 'first').width).toBe('50%')
    expect(events.find(event => event.id === 'second').width).toBe('50%')
  })

  it('keeps contained foreground events in a half-width lane even when they do not overlap each other', () => {
    const events = computeEventLayout([
      { id: 'long', startTime: '07:00', endTime: '12:00' },
      { id: 'first', startTime: '08:00', endTime: '10:00' },
      { id: 'second', startTime: '10:20', endTime: '12:10' },
    ])

    expect(events.find(event => event.id === 'long').width).toBeUndefined()
    expect(events.find(event => event.id === 'first').width).toBe('50%')
    expect(events.find(event => event.id === 'second').width).toBe('50%')
  })

  it('stacks foreground events into separate lanes when their times overlap but start differently', () => {
    const events = computeEventLayout([
      { id: 'long', startTime: '08:00', endTime: '13:00' },
      { id: 'early', startTime: '09:00', endTime: '12:55' },
      { id: 'later', startTime: '09:15', endTime: '10:15' },
    ])

    const early = events.find(event => event.id === 'early')
    const later = events.find(event => event.id === 'later')

    expect(early.left).toBe('0%')
    expect(later.left).toBe('50%')
    expect(early.top).toBe('450px')
    expect(later.top).toBe('462.5px')
  })

  it('orders same-start foreground events by priority from P0 to P4', () => {
    const events = computeEventLayout([
      { id: 'long', startTime: '07:00', endTime: '12:00', priority: 2 },
      { id: 'low', startTime: '08:00', endTime: '09:50', priority: 4 },
      { id: 'high', startTime: '08:00', endTime: '10:00', priority: 3 },
    ])

    expect(events.find(event => event.id === 'high').left).toBe('0%')
    expect(events.find(event => event.id === 'low').left).toBe('50%')
  })

  it('gives same-start external long events their own top-level lane', () => {
    const events = computeEventLayout([
      { id: 'main', startTime: '08:00', endTime: '13:00', priority: 2 },
      { id: 'external', startTime: '08:00', endTime: '11:55', priority: 2 },
      { id: 'child', startTime: '09:15', endTime: '10:15', priority: 2 },
    ])

    const main = events.find(event => event.id === 'main')
    const external = events.find(event => event.id === 'external')
    const child = events.find(event => event.id === 'child')

    expect(main.left).toBe('0%')
    expect(main.width).toBe('50%')
    expect(external.left).toBe('50%')
    expect(external.width).toBe('50%')
    expect(child.left).toBe('0%')
    expect(child.width).toBe('50%')
  })

  it('keeps near-start events as top-level lanes until they pass the nesting threshold', () => {
    const nearStart = computeEventLayout([
      { id: 'main', startTime: '08:00', endTime: '13:00' },
      { id: 'incoming', startTime: '08:25', endTime: '12:20' },
    ])

    expect(nearStart.find(event => event.id === 'main').width).toBe('50%')
    expect(nearStart.find(event => event.id === 'incoming').left).toBe('50%')

    const nested = computeEventLayout([
      { id: 'main', startTime: '08:00', endTime: '13:00' },
      { id: 'incoming', startTime: '08:30', endTime: '12:25' },
    ])

    expect(nested.find(event => event.id === 'main').width).toBeUndefined()
    expect(nested.find(event => event.id === 'incoming').width).toBe('50%')
  })
})
