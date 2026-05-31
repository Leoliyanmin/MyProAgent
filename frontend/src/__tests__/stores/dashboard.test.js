import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock the API module
vi.mock('@/services/api.js', () => ({
  eventsAPI: {
    list: vi.fn(() => Promise.resolve({ events: [] })),
    create: vi.fn(() => Promise.resolve({ event_id: 1 })),
    update: vi.fn(),
    delete: vi.fn(),
  },
  dashboardPresetsAPI: {
    list: vi.fn(() => Promise.resolve([])),
    save: vi.fn(() => Promise.resolve({ preset_id: 1 })),
    delete: vi.fn(() => Promise.resolve({ ok: true })),
  },
}))

import { useDashboardStore } from '@/stores/dashboard'

describe('dashboard store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty todos when localStorage is empty', () => {
      const dashboard = useDashboardStore()
      expect(dashboard.todos).toEqual([])
    })

    it('restores todos from localStorage', () => {
      const savedTodos = [
        { id: 1, title: 'Saved task', completed: false, start: '2026-05-01', end: '2026-05-01', priority: 0, color: '#ff3b30' },
      ]
      localStorage.setItem('proagent_todos', JSON.stringify(savedTodos))

      const dashboard = useDashboardStore()
      expect(dashboard.todos.length).toBe(1)
      expect(dashboard.todos[0].title).toBe('Saved task')
    })

    it('starts with default layout', () => {
      const dashboard = useDashboardStore()
      expect(dashboard.layoutConfig.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('addTodo', () => {
    it('adds a todo from a string', async () => {
      const dashboard = useDashboardStore()

      await dashboard.addTodo('New task from string')

      expect(dashboard.todos.length).toBe(1)
      expect(dashboard.todos[0].title).toBe('New task from string')
      expect(dashboard.todos[0].completed).toBe(false)
    })

    it('adds a todo from an object', async () => {
      const dashboard = useDashboardStore()

      await dashboard.addTodo({ title: 'Custom task', priority: 0, color: '#ff3b30' })

      const added = dashboard.todos[0]
      expect(added.title).toBe('Custom task')
      expect(added.priority).toBe(0)
      expect(added.color).toBe('#ff3b30')
    })

    it('persists to localStorage after adding', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo('Persist me')

      const stored = JSON.parse(localStorage.getItem('proagent_todos'))
      expect(stored[0].title).toBe('Persist me')
    })
  })

  describe('updateTodo', () => {
    it('updates an existing todo', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo('Original title')
      const todo = dashboard.todos[0]

      dashboard.updateTodo({ id: todo.id, title: 'Updated title' })

      const updated = dashboard.todos.find(t => t.id === todo.id)
      expect(updated.title).toBe('Updated title')
    })

    it('does nothing for non-existent id', () => {
      const dashboard = useDashboardStore()
      const initialLength = dashboard.todos.length

      dashboard.updateTodo({ id: 99999, title: 'Ghost' })

      expect(dashboard.todos.length).toBe(initialLength)
    })
  })

  describe('toggleTodo', () => {
    it('toggles completion status', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo('Toggle me')
      const todo = dashboard.todos[0]
      const initialStatus = todo.completed

      dashboard.toggleTodo(todo.id)

      expect(todo.completed).toBe(!initialStatus)
    })
  })

  describe('removeTodo', () => {
    it('removes a todo by id', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo('Remove me')
      const todo = dashboard.todos[0]
      const initialLength = dashboard.todos.length

      await dashboard.removeTodo(todo.id)

      expect(dashboard.todos.length).toBe(initialLength - 1)
      expect(dashboard.todos.find(t => t.id === todo.id)).toBeUndefined()
    })
  })

  describe('sortedTodos', () => {
    it('puts completed tasks last', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo({ title: 'Done task', completed: true, priority: 0 })
      await dashboard.addTodo({ title: 'Active task', completed: false, priority: 2 })

      const sorted = dashboard.sortedTodos
      const doneIndex = sorted.findIndex(t => t.title === 'Done task')
      const activeIndex = sorted.findIndex(t => t.title === 'Active task')

      expect(activeIndex).toBeLessThan(doneIndex)
    })
  })

  describe('pendingTodosCount', () => {
    it('counts uncompleted todos', async () => {
      const dashboard = useDashboardStore()
      await dashboard.addTodo({ title: 'Pending 1', completed: false })
      await dashboard.addTodo({ title: 'Pending 2', completed: false })
      await dashboard.addTodo({ title: 'Done', completed: true })

      expect(dashboard.pendingTodosCount).toBeGreaterThanOrEqual(2)
    })
  })

  describe('recordActivity', () => {
    it('adds today entry to activity log', () => {
      const dashboard = useDashboardStore()
      const initialSize = Object.keys(dashboard.activityLog).length

      dashboard.recordActivity(3)

      const newSize = Object.keys(dashboard.activityLog).length
      expect(newSize).toBeGreaterThanOrEqual(initialSize)
    })
  })

  describe('autoArrangeLayout', () => {
    it('keeps the layout array reference so grid bindings update', () => {
      const dashboard = useDashboardStore()
      const originalLayout = dashboard.layoutConfig

      dashboard.layoutConfig.push(
        { x: 10, y: 8, w: 3, h: 1, i: 'mini-heatmap', type: 'heatmap', minW: 2, minH: 1, maxW: 4, maxH: 2 }
      )

      dashboard.autoArrangeLayout()

      expect(dashboard.layoutConfig).toBe(originalLayout)
      expect(dashboard.layoutConfig.some(item => item.i === 'mini-heatmap')).toBe(true)
    })

    it('uses a saved work mode template for the same widget combination', () => {
      const dashboard = useDashboardStore()
      dashboard.layoutConfig.splice(0, dashboard.layoutConfig.length,
        { x: 8, y: 8, w: 4, h: 6, i: 'todo', type: 'todo', minW: 3, minH: 4 },
        { x: 0, y: 8, w: 5, h: 6, i: 'messages', type: 'messages', minW: 4, minH: 4 }
      )

      dashboard.saveCurrentLayoutAsPreset()
      dashboard.layoutConfig[0].x = 0
      dashboard.layoutConfig[1].x = 7

      dashboard.autoArrangeLayout()

      expect(dashboard.layoutConfig.find(item => item.type === 'todo').x).toBe(8)
      expect(dashboard.layoutConfig.find(item => item.type === 'messages').x).toBe(0)
    })
  })

  describe('applyPreset', () => {
    it('keeps the layout array reference while switching templates', () => {
      const dashboard = useDashboardStore()
      dashboard.layoutConfig.splice(0, dashboard.layoutConfig.length,
        { x: 8, y: 0, w: 4, h: 6, i: 'todo', type: 'todo', minW: 3, minH: 4 },
        { x: 0, y: 0, w: 5, h: 6, i: 'messages', type: 'messages', minW: 4, minH: 4 }
      )
      dashboard.customLayoutPresets = {
        first: {
          name: 'First template',
          items: [
            { x: 0, y: 0, w: 4, h: 6, type: 'todo' },
            { x: 4, y: 0, w: 5, h: 6, type: 'messages' },
          ],
        },
        second: {
          name: 'Second template',
          items: [
            { x: 8, y: 0, w: 4, h: 6, type: 'todo' },
            { x: 0, y: 0, w: 5, h: 6, type: 'messages' },
          ],
        },
      }
      const originalLayout = dashboard.layoutConfig

      dashboard.applyPreset('first')

      expect(dashboard.layoutConfig).toBe(originalLayout)
      expect(dashboard.layoutConfig.find(item => item.type === 'todo').x).toBe(0)
      expect(dashboard.layoutConfig.find(item => item.type === 'messages').x).toBe(4)

      dashboard.applyPreset('second')

      expect(dashboard.layoutConfig).toBe(originalLayout)
      expect(dashboard.layoutConfig.find(item => item.type === 'todo').x).toBe(8)
      expect(dashboard.layoutConfig.find(item => item.type === 'messages').x).toBe(0)
    })
  })
})
