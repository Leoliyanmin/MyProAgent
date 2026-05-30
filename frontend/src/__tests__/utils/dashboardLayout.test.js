import { describe, expect, it } from 'vitest'
import {
  applyLayoutPreset,
  arrangeDashboardLayout,
  createLayoutKey,
  createLayoutPreset,
  hasLayoutCollisions
} from '@/utils/dashboardLayout.js'

const messyLayout = [
  { x: 8, y: 9, w: 6, h: 8, i: 'note', type: 'markdown', minW: 6, minH: 4 },
  { x: 0, y: 12, w: 3, h: 1, i: 'heat', type: 'heatmap', minW: 2, minH: 1, maxW: 4, maxH: 2 },
  { x: 6, y: 4, w: 5, h: 6, i: 'agent', type: 'agent-mini', minW: 4, minH: 4 },
  { x: 2, y: 1, w: 4, h: 6, i: 'todo', type: 'todo', minW: 3, minH: 4 },
  { x: 9, y: 0, w: 4, h: 7, i: 'compose', type: 'compose-mini', minW: 3, minH: 5 },
  { x: 1, y: 8, w: 5, h: 6, i: 'messages', type: 'messages', minW: 4, minH: 4 }
]

describe('arrangeDashboardLayout', () => {
  it('packs widgets without collisions', () => {
    const arranged = arrangeDashboardLayout(messyLayout)

    expect(hasLayoutCollisions(arranged)).toBe(false)
  })

  it('keeps every widget inside the 12-column grid', () => {
    const arranged = arrangeDashboardLayout(messyLayout)

    for (const item of arranged) {
      expect(item.x).toBeGreaterThanOrEqual(0)
      expect(item.x + item.w).toBeLessThanOrEqual(12)
    }
  })

  it('is stable when arranging an already arranged layout', () => {
    const arranged = arrangeDashboardLayout(messyLayout)
    const arrangedAgain = arrangeDashboardLayout(arranged)

    expect(arrangedAgain).toEqual(arranged)
  })

  it('places higher priority primary widgets before long-form content', () => {
    const arranged = arrangeDashboardLayout(messyLayout)
    const todo = arranged.find(item => item.type === 'todo')
    const markdown = arranged.find(item => item.type === 'markdown')

    expect(todo.y).toBeLessThanOrEqual(markdown.y)
  })

  it('creates stable keys from visible widget types', () => {
    expect(createLayoutKey(messyLayout)).toBe('agent-mini|compose-mini|heatmap|markdown|messages|todo')
  })

  it('records and reapplies a layout preset by widget type', () => {
    const preset = createLayoutPreset([
      { x: 4, y: 0, w: 4, h: 6, i: 'todo', type: 'todo' },
      { x: 0, y: 0, w: 4, h: 6, i: 'messages', type: 'messages' }
    ])
    const applied = applyLayoutPreset([
      { x: 9, y: 9, w: 4, h: 6, i: 'other-todo-id', type: 'todo' },
      { x: 9, y: 15, w: 4, h: 6, i: 'other-message-id', type: 'messages' }
    ], preset)

    expect(applied.find(item => item.type === 'messages').x).toBe(0)
    expect(applied.find(item => item.type === 'todo').x).toBe(4)
  })
})
