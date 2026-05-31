import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useBehaviorProfileStore } from './behaviorProfile.js'
import { eventsAPI, activityAPI, dashboardPresetsAPI } from '../services/api.js'
import { useCalendarStore } from './calendar.js'
import {
  DEFAULT_DASHBOARD_LAYOUT_PRESETS,
  applyLayoutPreset,
  arrangeDashboardLayout,
  createLayoutKey,
  createLayoutPreset
} from '../utils/dashboardLayout.js'

const LAYOUT_STORAGE_KEY = 'proagent_layout'
const LAYOUT_PRESETS_STORAGE_KEY = 'proagent_layout_presets'

const ACTIVITY_LOG_STORAGE_KEY = 'proagent_activity_log'
const MINI_WIDGETS_STORAGE_KEY = 'proagent_mini_widgets'
const TODOS_STORAGE_KEY = 'proagent_todos'

// ── Activity Log (heatmap data) ──
const saveActivityLog = (log) => {
  try {
    localStorage.setItem(ACTIVITY_LOG_STORAGE_KEY, JSON.stringify(log))
  } catch (err) {
    console.error('Failed to save activity log to localStorage:', err)
  }
}

const loadActivityLog = () => {
  try {
    const stored = localStorage.getItem(ACTIVITY_LOG_STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch (err) {
    return {}
  }
}

// ── Mini Widgets active set ──
const saveMiniWidgets = (widgets) => {
  try {
    localStorage.setItem(MINI_WIDGETS_STORAGE_KEY, JSON.stringify([...widgets]))
  } catch (err) {
    console.error('Failed to save mini widgets to localStorage:', err)
  }
}

const loadMiniWidgets = () => {
  try {
    const stored = localStorage.getItem(MINI_WIDGETS_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return Array.isArray(parsed) ? new Set(parsed) : new Set()
    }
  } catch (err) {
    // fall through
  }
  return new Set()
}

const saveTodosToStorage = (todos) => {
  try {
    localStorage.setItem(TODOS_STORAGE_KEY, JSON.stringify(todos))
  } catch (err) {
    console.error('Failed to save todos to localStorage:', err)
  }
}

const loadTodosFromStorage = () => {
  try {
    const stored = localStorage.getItem(TODOS_STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (err) {
    return []
  }
}

const DEFAULT_LAYOUT = [
  { x: 0, y: 0, w: 6, h: 5, i: '3', type: 'todo', minW: 3, minH: 4 },
  { x: 6, y: 0, w: 6, h: 5, i: '4', type: 'messages', minW: 4, minH: 3 },
  { x: 0, y: 5, w: 12, h: 8, i: '5', type: 'markdown', minW: 6, minH: 4 }
]

export const HEATMAP_LAYOUT_PRESETS = [
  { name: 'compact', w: 2, h: 1 },
  { name: 'wide', w: 4, h: 1 },
  { name: 'tall', w: 2, h: 2 },
  { name: 'full', w: 6, h: 1 },
  { name: 'banner', w: 8, h: 1 }
]

export const getHeatmapLayoutPreset = (w = 4, h = 1) => {
  return HEATMAP_LAYOUT_PRESETS.reduce((best, preset) => {
    const bestScore = Math.abs(best.w - w) + Math.abs(best.h - h) * 1.5
    const score = Math.abs(preset.w - w) + Math.abs(preset.h - h) * 1.5
    return score < bestScore ? preset : best
  }, HEATMAP_LAYOUT_PRESETS[1])
}

const normalizeLayoutItem = (item) => {
  if (item?.type !== 'heatmap' && item?.i !== 'mini-heatmap') {
    return item
  }
  const preset = getHeatmapLayoutPreset(item.w, item.h)
  return {
    ...item,
    minW: 2,
    minH: 1,
    maxW: 12,
    maxH: 2,
    w: preset.w,
    h: preset.h,
    heatmapVariant: preset.name
  }
}

const loadLayoutFromStorage = () => {
  try {
    const stored = localStorage.getItem(LAYOUT_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed) && parsed.length > 0) {
        // Clean stale types that no longer have components
        const cleaned = parsed
          .filter(item => item.type !== 'inbox-mini')
          .map(normalizeLayoutItem)
        const savedTypes = new Set(cleaned.map(item => item.type))
        const newItems = DEFAULT_LAYOUT.filter(item => !savedTypes.has(item.type))
        if (newItems.length > 0) {
          const merged = [...cleaned, ...newItems]
          return merged
        }
        return cleaned
      }
    }
  } catch (err) {
    console.error('Failed to load layout from localStorage:', err)
  }
  return DEFAULT_LAYOUT
}

const saveLayoutToStorage = (layout) => {
  try {
    localStorage.setItem(LAYOUT_STORAGE_KEY, JSON.stringify(layout))
  } catch (err) {
    console.error('Failed to save layout to localStorage:', err)
  }
}

const loadLayoutPresetsFromStorage = () => {
  try {
    const stored = localStorage.getItem(LAYOUT_PRESETS_STORAGE_KEY)
    return stored ? JSON.parse(stored) : {}
  } catch { return {} }
}

const saveLayoutPresetsToStorage = (presets) => {
  try { localStorage.setItem(LAYOUT_PRESETS_STORAGE_KEY, JSON.stringify(presets)) } catch {}
}

async function loadPresetsFromAPI() {
  try {
    const list = await dashboardPresetsAPI.list()
    const presets = {}
    for (const p of list) {
      let items
      try { items = JSON.parse(p.preset_data) } catch { items = [] }
      presets[String(p.preset_id)] = {
        name: p.preset_name,
        items,
        createdAt: p.created_at,
        _apiId: p.preset_id
      }
    }
    if (Object.keys(presets).length > 0) {
      customLayoutPresets.value = presets
      saveLayoutPresetsToStorage(presets)
    }
  } catch (err) {
    console.warn('Failed to load presets from API, using localStorage:', err)
  }
}

async function savePresetToAPI(key, preset) {
  try {
    const data = JSON.stringify(preset.items)
    const body = { preset_name: preset.name, preset_data: data }
    if (preset._apiId) body.preset_id = preset._apiId
    const result = await dashboardPresetsAPI.save(body.preset_name, body.preset_data, body.preset_id)
    return result.preset_id
  } catch (err) {
    console.warn('Failed to save preset to API:', err)
    return null
  }
}

async function deletePresetFromAPI(apiId) {
  try {
    await dashboardPresetsAPI.delete(apiId)
    return true
  } catch (err) {
    console.warn('Failed to delete preset from API:', err)
    return false
  }
}

const parseDueDateTime = (value) => {
  if (!value) {
    return { date: '', time: '' }
  }

  const raw = String(value)
  const normalized = raw.includes('T') ? raw : raw.replace(' ', 'T')
  const [datePart = '', timePart = ''] = normalized.split('T')
  return {
    date: datePart,
    time: (timePart || '').slice(0, 5)
  }
}

const inferPriority = (task) => {
  const raw = task.event_priority ?? task.priority
  if (typeof raw === 'number' && raw >= 0 && raw <= 3) return raw
  const text = String(raw || '').toLowerCase().trim()
  if (text === 'p0' || text === '0') return 0
  if (text === 'high' || text === 'p1' || text === '1') return 1
  if (text === 'p2' || text === '2') return 2
  if (text === 'low' || text === 'p3' || text === '3') return 3
  return 2
}

const inferColorByPriority = (priority) => {
  if (priority === 0) return '#ff3b30'
  if (priority === 1) return '#ff9500'
  if (priority === 3) return '#34c759'
  if (priority === 4) return '#8e8e93'
  return '#007aff'
}

const mapRemoteTaskToTodo = (task) => {
  const dueDate = task.due_date || ''
  const { date, time } = parseDueDateTime(dueDate)
  const priority = inferPriority(task)
  const description = task.description || ''

  return {
    id: task.task_id,
    title: task.title || '未命名任务',
    completed: String(task.status || '').toLowerCase() === 'completed',
    start: date || new Date().toISOString().split('T')[0],
    end: date || new Date().toISOString().split('T')[0],
    startTime: '',
    endTime: time,
    priority,
    color: inferColorByPriority(priority),
    description,
    linkedScheduleId: extractLinkedScheduleId(task),
    source: 'remote'
  }
}

export const useDashboardStore = defineStore('dashboard', () => {
  const behaviorProfileStore = useBehaviorProfileStore()
  // ==============================
  // 1. 活动热力图状态 (Heatmap)
  // ==============================
  // 记录每天每小时的活跃度：{ '2026-05-29': { 9: 2, 14: 3 } }
  const activityLog = ref(loadActivityLog())

  const getTodayString = () => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  const recordActivity = (points = 1) => {
    const today = getTodayString()
    const hour = new Date().getHours()
    if (!activityLog.value[today]) activityLog.value[today] = {}
    if (!activityLog.value[today][hour]) activityLog.value[today][hour] = 0
    activityLog.value[today][hour] += points
    saveActivityLog(activityLog.value)
    _dirtyActivityLog()
  }

  // 今日 24 小时分布 [count0, count1, ... count23]
  const todayHourly = computed(() => {
    const today = getTodayString()
    const hours = activityLog.value[today] || {}
    return Array.from({ length: 24 }, (_, h) => hours[h] || 0)
  })

  // 过去 7 天，每天的总量 [{ date, dayLabel, total }]
  const weeklyHeatmap = computed(() => {
    const result = []
    const now = new Date()
    const DAYS = ['日', '一', '二', '三', '四', '五', '六']
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(d.getDate() - i)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      const hours = activityLog.value[key] || {}
      const total = Object.values(hours).reduce((s, v) => s + v, 0)
      result.push({ date: key, dayLabel: DAYS[d.getDay()], short: `${d.getMonth() + 1}/${d.getDate()}`, total })
    }
    return result
  })

  // 过去 30 天，每天的总量 [{ date, total }]
  const monthlyHeatmap = computed(() => {
    const result = []
    const now = new Date()
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(d.getDate() - i)
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      const hours = activityLog.value[key] || {}
      const total = Object.values(hours).reduce((s, v) => s + v, 0)
      result.push({ date: key, short: `${d.getMonth() + 1}/${d.getDate()}`, total })
    }
    return result
  })

  let _activityFlushTimer = null
  let _activityDirty = false

  const _dirtyActivityLog = () => {
    _activityDirty = true
    if (_activityFlushTimer) clearTimeout(_activityFlushTimer)
    _activityFlushTimer = setTimeout(flushActivityLog, 10000)
  }

  const _onVisibilityChange = () => {
    if (document.visibilityState === 'hidden') {
      flushActivityLog()
    }
  }

  const flushActivityLog = async () => {
    if (!_activityDirty) return
    const logs = Object.entries(activityLog.value).flatMap(([date, hours]) =>
      Object.entries(hours).map(([hour, count]) => ({
        log_date: date,
        hour: parseInt(hour),
        count
      }))
    )
    if (logs.length === 0) return
    try {
      await activityAPI.recordBatch(logs)
      _activityDirty = false
    } catch (err) {
      console.error('Failed to flush activity log:', err)
    }
    if (_activityFlushTimer) clearTimeout(_activityFlushTimer)
    _activityFlushTimer = null
  }

  let _visibilityBound = false

  const syncActivityLog = async () => {
    if (!_visibilityBound) {
      _visibilityBound = true
      document.addEventListener('visibilitychange', _onVisibilityChange)
    }
    try {
      const now = new Date()
      const toDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
      const from = new Date(now)
      from.setDate(from.getDate() - 30)
      const fromDate = `${from.getFullYear()}-${String(from.getMonth() + 1).padStart(2, '0')}-${String(from.getDate()).padStart(2, '0')}`
      const res = await activityAPI.getHeatmap(fromDate, toDate)
      const serverData = res?.heatmap || {}
      const local = { ...activityLog.value }
      for (const [date, hours] of Object.entries(serverData)) {
        if (!local[date]) {
          local[date] = { ...hours }
        } else {
          for (const [hour, count] of Object.entries(hours)) {
            local[date][hour] = Math.max(local[date][hour] || 0, count)
          }
        }
      }
      activityLog.value = local
      saveActivityLog(activityLog.value)
    } catch (err) {
      console.error('Failed to sync activity log from server:', err)
    }
  }

  const cleanupActivitySync = () => {
    flushActivityLog()
    document.removeEventListener('visibilitychange', _onVisibilityChange)
    _visibilityBound = false
    if (_activityFlushTimer) clearTimeout(_activityFlushTimer)
  }

  // ==============================
  // 2. TODO 状态 (本地存储)
  // ==============================
  // priority: 0 (P0 紧急且重要 - 红色), 1 (P1 重要不紧急 - 橙色)
  //           2 (P2 紧急不重要 - 蓝色), 3 (P3 不重要不紧急 - 绿色)
  const todos = ref(loadTodosFromStorage())

  // 未完成任务数
  const pendingTodosCount = computed(() => todos.value.filter(t => !t.completed).length)

  // 根据完成状态和优先级排序的 TODO 列表
  const sortedTodos = computed(() => {
    return [...todos.value].sort((a, b) => {
      // 1. 已完成的排在最后
      if (a.completed !== b.completed) return a.completed ? 1 : -1;
      // 2. 未完成的按优先级排序 (0 最高, 3 最低)
      const priorityA = a.priority !== undefined ? a.priority : 3;
      const priorityB = b.priority !== undefined ? b.priority : 3;
      if (priorityA !== priorityB) return priorityA - priorityB;
      // 3. 优先级相同则按时间或 ID
      return b.id - a.id;
    })
  })

  const addTodo = async (taskPayload) => {
    const today = new Date().toISOString().split('T')[0]
    const title = typeof taskPayload === 'string' ? taskPayload : (taskPayload.title || '')
    const priority = typeof taskPayload === 'object' ? (taskPayload.priority ?? 2) : 2

    const dueDate = taskPayload.startTime
      ? `${taskPayload.start || today}T${taskPayload.startTime}:00`
      : (taskPayload.start || today)

    try {
      const result = await eventsAPI.create({
        event_title: title,
        event_description: (taskPayload.description || ''),
        event_start_time: dueDate || undefined,
        event_show_in_todo: 1,
        event_priority: priority,
        event_type: 'manual',
        event_source: 'manual',
      })

      const newTodo = {
        id: result.event_id,
        title: title,
        completed: taskPayload.completed === true || taskPayload.completed === 1,
        start: taskPayload.start || today,
        end: taskPayload.end || taskPayload.start || today,
        startTime: taskPayload.startTime || '',
        endTime: taskPayload.endTime || '',
        priority: priority,
        color: taskPayload.color || inferColorByPriority(priority),
        source: 'remote',
        linkedScheduleId: taskPayload.linkedScheduleId || null,
        description: taskPayload.description || '',
      }

      todos.value.unshift(newTodo)
      saveTodosToStorage(todos.value)
    } catch (err) {
      console.error('Failed to create todo:', err)
    }
  }

  const updateTodo = (updatedTask) => {
    const index = todos.value.findIndex(t => t.id === updatedTask.id)
    if (index !== -1) {
      todos.value.splice(index, 1, { ...todos.value[index], ...updatedTask })
      saveTodosToStorage(todos.value)
    }
  }

  const toggleTodo = async (id) => {
    const task = todos.value.find(t => t.id === id)
    if (!task) return

    task.completed = !task.completed
    if (task.completed) {
      recordActivity(1)
      behaviorProfileStore.recordBehaviorEvent('todo_completed', {
        module: 'todo',
        priority: task.priority ?? 2,
        source: task.source || 'local'
      })
    }
    saveTodosToStorage(todos.value)

    try {
      await eventsAPI.update(id, {
        event_is_completed: task.completed ? 1 : 0
      })
    } catch (err) {
      console.error('Failed to sync todo status:', err)
      task.completed = !task.completed
      saveTodosToStorage(todos.value)
      return
    }

    const calendarStore = useCalendarStore()
    const idx = calendarStore.basicEvents.findIndex(e => e.id === id)
    if (idx !== -1) {
      calendarStore.basicEvents[idx] = { ...calendarStore.basicEvents[idx], completed: task.completed }
    }
  }

  const removeTodo = async (id) => {
    try {
      await eventsAPI.delete(id)
    } catch (err) {
      console.error('Failed to delete event:', err)
    }
    todos.value = todos.value.filter(t => t.id !== id)
    saveTodosToStorage(todos.value)

    const calendarStore = useCalendarStore()
    calendarStore.basicEvents = calendarStore.basicEvents.filter(e => e.id !== id)
  }

  const loadTodosFromBackend = async () => {
    try {
      const res = await eventsAPI.list({ show_in_todo: '1' })
      const remoteEvents = res.events || []
      const remoteTodos = remoteEvents.map(e => ({
        id: e.event_id,
        title: e.event_title,
        completed: !!e.event_is_completed,
        priority: e.event_priority ?? 2,
        color: inferColorByPriority(e.event_priority ?? 2),
        source: e.event_source,
        description: e.event_description || '',
        start: e.event_start_time || '',
        end: e.event_end_time || '',
        linkedScheduleId: null,
      }))

      todos.value = remoteTodos
      saveTodosToStorage(todos.value)
      return { success: true, count: remoteTodos.length }
    } catch (err) {
      console.error('Failed to load todos from backend:', err)
      return { success: false, message: err?.message || '加载任务失败' }
    }
  }

// ==============================
  // 3. 布局配置状态 (本地存储)
  // ==============================
  const layoutConfig = ref(loadLayoutFromStorage())
  const customLayoutPresets = ref(loadLayoutPresetsFromStorage())
  const activePresetKey = ref('')

  const saveLayout = () => {
    saveLayoutToStorage(layoutConfig.value)
  }

  const autoArrangeLayout = () => {
    const normalized = layoutConfig.value.map(normalizeLayoutItem)
    const key = createLayoutKey(normalized)
    const preset = customLayoutPresets.value[key] || DEFAULT_DASHBOARD_LAYOUT_PRESETS[key]
    const arranged = applyLayoutPreset(normalized, preset) || arrangeDashboardLayout(normalized)
    layoutConfig.value.splice(0, layoutConfig.value.length, ...arranged)
    saveLayoutToStorage(layoutConfig.value)
    behaviorProfileStore.recordBehaviorEvent('dashboard_auto_arranged', {
      module: 'dashboard',
      layoutKey: key,
      source: preset ? 'preset' : 'algorithm'
    })
  }

  const ensureDefaultPreset = () => {
    const keys = Object.keys(customLayoutPresets.value)
    if (keys.length === 0) {
      const preset = createLayoutPreset(layoutConfig.value.map(normalizeLayoutItem))
      const key = preset.key
      customLayoutPresets.value = { [key]: { ...preset, name: '默认布局' } }
      saveLayoutPresetsToStorage(customLayoutPresets.value)
      activePresetKey.value = key
      savePresetToAPI(key, { ...preset, name: '默认布局' }).then(id => {
        if (id && customLayoutPresets.value[key]) customLayoutPresets.value[key]._apiId = id
      }).then(id => {
        if (id && customLayoutPresets.value[key]) customLayoutPresets.value[key]._apiId = id
      })
    } else if (!activePresetKey.value || !customLayoutPresets.value[activePresetKey.value]) {
      activePresetKey.value = keys[0]
    }
  }

  const saveCurrentLayoutAsPreset = (name) => {
    const normalized = layoutConfig.value.map(normalizeLayoutItem)
    const preset = createLayoutPreset(normalized)
    const key = preset.key

    if (activePresetKey.value) {
      const existing = customLayoutPresets.value[activePresetKey.value]
      customLayoutPresets.value[activePresetKey.value] = { ...preset, name: name || '默认布局', _apiId: existing?._apiId }
      saveLayoutPresetsToStorage(customLayoutPresets.value)
      savePresetToAPI(activePresetKey.value, customLayoutPresets.value[activePresetKey.value])
      return preset
    }

    customLayoutPresets.value = {
      ...customLayoutPresets.value,
      [key]: { ...preset, name: name || preset.key }
    }
    activePresetKey.value = key
    saveLayoutPresetsToStorage(customLayoutPresets.value)
    savePresetToAPI(key, { ...preset, name: name || preset.key })
    behaviorProfileStore.recordBehaviorEvent('dashboard_template_saved', {
      module: 'dashboard',
      layoutKey: key,
      name,
      widgetCount: normalized.length
    })
    return preset
  }

  const namedPresets = computed(() =>
    Object.entries(customLayoutPresets.value)
      .filter(([, p]) => p.name)
      .map(([key, p]) => ({ key, name: p.name }))
  )

  const activePresetName = computed(() => {
    const p = customLayoutPresets.value[activePresetKey.value]
    return p?.name || '默认布局'
  })

  const createNewPreset = (name) => {
    const normalized = layoutConfig.value.map(normalizeLayoutItem)
    const preset = createLayoutPreset(normalized)
    const key = preset.key + '_' + Date.now()
    customLayoutPresets.value = {
      ...customLayoutPresets.value,
      [key]: { ...preset, name: name || '新模板' }
    }
    activePresetKey.value = key
    saveLayoutPresetsToStorage(customLayoutPresets.value)
    saveLayoutToStorage(layoutConfig.value)
    savePresetToAPI(key, { ...preset, name: name || '新模板' })
    return key
  }

  const deletePreset = (key) => {
    const keys = Object.keys(customLayoutPresets.value)
    if (keys.length <= 1) return false
    const deleted = customLayoutPresets.value[key]
    const newPresets = { ...customLayoutPresets.value }
    delete newPresets[key]
    customLayoutPresets.value = newPresets
    if (activePresetKey.value === key) {
      activePresetKey.value = Object.keys(newPresets)[0]
    }
    saveLayoutPresetsToStorage(customLayoutPresets.value)
    if (deleted?._apiId) deletePresetFromAPI(deleted._apiId)
    return true
  }

  const renamePreset = (key, newName) => {
    const p = customLayoutPresets.value[key]
    if (!p) return
    customLayoutPresets.value[key] = { ...p, name: newName }
    saveLayoutPresetsToStorage(customLayoutPresets.value)
    savePresetToAPI(key, { ...p, name: newName })
  }

  const applyPreset = (key) => {
    const preset = customLayoutPresets.value[key]
    if (!preset) return

    const presetTypes = new Set(preset.items.map(item => item.type))

    // Sync miniWidgets to match preset types
    const newWidgets = new Set()
    for (const widgetType of miniWidgets.value) {
      const mapped = MINI_LAYOUT_MAP[widgetType]?.type
      if (mapped && presetTypes.has(mapped)) newWidgets.add(widgetType)
    }
    for (const item of preset.items) {
      const miniType = TYPE_TO_QUICK_TOGGLE[item.type]
      if (miniType) newWidgets.add(miniType)
    }
    miniWidgets.value = newWidgets

    // Directly rebuild layout from preset items
    const newLayout = preset.items.map(pItem => {
      const miniType = TYPE_TO_QUICK_TOGGLE[pItem.type]
      const defaults = miniType ? MINI_LAYOUT_MAP[miniType] : null
      return {
        x: pItem.x,
        y: pItem.y,
        w: pItem.w,
        h: pItem.h,
        i: defaults?.i || pItem.type,
        type: pItem.type,
        minW: defaults?.minW || 2,
        minH: defaults?.minH || 1,
        heatmapVariant: pItem.heatmapVariant,
      }
    })

    layoutConfig.value = newLayout
    activePresetKey.value = key
    saveLayoutToStorage(newLayout)
    saveMiniWidgets(miniWidgets.value)
  }

  const resetLayout = () => {
    layoutConfig.value.splice(0, layoutConfig.value.length, ...DEFAULT_LAYOUT)
    saveLayoutToStorage(layoutConfig.value)
  }

  // ── Mini widgets ──
  const miniWidgets = ref(loadMiniWidgets())

  const MINI_LAYOUT_MAP = {
    'compose': { w: 4, h: 7, i: 'mini-compose', type: 'compose-mini', minW: 3, minH: 5 },
    'inbox':   { w: 5, h: 6, i: 'mini-inbox',   type: 'messages',    minW: 4, minH: 4 },
    'note':    { w: 6, h: 8, i: 'mini-note',    type: 'markdown',    minW: 6, minH: 4 },
    'todo':    { w: 4, h: 6, i: 'mini-todo',    type: 'todo',        minW: 3, minH: 4 },
    'heatmap': { w: 4, h: 1, i: 'mini-heatmap', type: 'heatmap',     minW: 2, minH: 1, maxW: 12, maxH: 2, heatmapVariant: 'wide' },
    'agent':   { w: 5, h: 6, i: 'mini-agent',   type: 'agent-mini',  minW: 4, minH: 4 },
  }

  const TYPE_TO_QUICK_TOGGLE = {
    'todo': 'todo', 'messages': 'inbox', 'markdown': 'note',
    'heatmap': 'heatmap', 'compose-mini': 'compose', 'agent-mini': 'agent',
  }

  const _removedCache = new Map()

  function _findBestPosition(w, h) {
    const items = layoutConfig.value
    if (items.length === 0) return { x: 0, y: 0 }

    const occupied = items.map(it => ({ x: it.x, y: it.y, w: it.w, h: it.h }))

    // Try position by position, prefer top-left
    for (let row = 0; row < 20; row++) {
      for (let col = 0; col <= 12 - w; col++) {
        const overlaps = occupied.some(r =>
          col < r.x + r.w && col + w > r.x && row < r.y + r.h && row + h > r.y
        )
        if (!overlaps) return { x: col, y: row }
      }
    }
    // fallback: below everything
    const maxBottom = Math.max(0, ...occupied.map(r => r.y + r.h))
    return { x: 0, y: maxBottom }
  }

  function isMiniWidgetActive(type) {
    return miniWidgets.value.has(type)
  }

  function toggleMiniWidget(type) {
    const next = new Set(miniWidgets.value)
    const isVisible = type === 'inbox'
      ? layoutConfig.value.some(item => item.type === 'messages')
      : type === 'note'
        ? layoutConfig.value.some(item => item.type === 'markdown')
        : type === 'todo'
          ? layoutConfig.value.some(item => item.type === 'todo')
          : layoutConfig.value.some(item => item.i === MINI_LAYOUT_MAP[type]?.i)

    if (isVisible) {
      next.delete(type)
      _removeMiniFromLayout(type)
    } else {
      next.add(type)
      _addMiniToLayout(type)
      recordActivity(1)
    }
    recordActivity(1)
    miniWidgets.value = next
    saveMiniWidgets(miniWidgets.value)
    behaviorProfileStore.recordBehaviorEvent('widget_toggled', {
      module: 'dashboard',
      widget: type,
      visible: !isVisible
    })
  }

  function _addMiniToLayout(type) {
    const cached = _removedCache.get(type)
    if (type === 'inbox') {
      if (!layoutConfig.value.some(item => item.type === 'messages')) {
        if (cached) {
          layoutConfig.value.push({ ...cached })
          _removedCache.delete('inbox')
        } else {
          const pos = _findBestPosition(6, 5)
          layoutConfig.value.push({ x: pos.x, y: pos.y, w: 6, h: 5, i: '4', type: 'messages', minW: 4, minH: 3 })
        }
      }
      return
    }
    if (type === 'note') {
      if (!layoutConfig.value.some(item => item.type === 'markdown')) {
        if (cached) {
          layoutConfig.value.push({ ...cached })
          _removedCache.delete('note')
        } else {
          const pos = _findBestPosition(6, 8)
          layoutConfig.value.push({ x: pos.x, y: pos.y, w: 6, h: 8, i: '5', type: 'markdown', minW: 6, minH: 4 })
        }
      }
      return
    }
    if (type === 'todo') {
      if (!layoutConfig.value.some(item => item.type === 'todo')) {
        if (cached) {
          layoutConfig.value.push({ ...cached })
          _removedCache.delete('todo')
        } else {
          const pos = _findBestPosition(4, 6)
          layoutConfig.value.push({ x: pos.x, y: pos.y, w: 4, h: 6, i: '3', type: 'todo', minW: 3, minH: 4 })
        }
      }
      return
    }
    const def = MINI_LAYOUT_MAP[type]
    if (!def) return
    if (layoutConfig.value.some(item => item.i === def.i)) return
    if (cached) {
      layoutConfig.value.push({ ...cached })
      _removedCache.delete(type)
    } else {
      const pos = _findBestPosition(def.w, def.h)
      layoutConfig.value.push({ ...def, x: pos.x, y: pos.y })
    }
  }

  function _removeMiniFromLayout(type) {
    if (type === 'inbox') {
      const idx = layoutConfig.value.findIndex(item => item.type === 'messages')
      if (idx !== -1) {
        _removedCache.set('inbox', { ...layoutConfig.value[idx] })
        layoutConfig.value.splice(idx, 1)
      }
      return
    }
    if (type === 'note') {
      const idx = layoutConfig.value.findIndex(item => item.type === 'markdown')
      if (idx !== -1) {
        _removedCache.set('note', { ...layoutConfig.value[idx] })
        layoutConfig.value.splice(idx, 1)
      }
      return
    }
    if (type === 'todo') {
      const idx = layoutConfig.value.findIndex(item => item.type === 'todo')
      if (idx !== -1) {
        _removedCache.set('todo', { ...layoutConfig.value[idx] })
        layoutConfig.value.splice(idx, 1)
      }
      return
    }
    const def = MINI_LAYOUT_MAP[type]
    if (!def) return
    const idx = layoutConfig.value.findIndex(item => item.i === def.i)
    if (idx !== -1) {
      _removedCache.set(type, { ...layoutConfig.value[idx] })
      layoutConfig.value.splice(idx, 1)
    }
  }

  return {
    activityLog,
    todayHourly,
    weeklyHeatmap,
    monthlyHeatmap,
    recordActivity,
    flushActivityLog,
    syncActivityLog,
    cleanupActivitySync,
    
    todos,
    sortedTodos,
    pendingTodosCount,
    addTodo,
    updateTodo,
    toggleTodo,
    removeTodo,
    loadTodosFromBackend,

    layoutConfig,
    customLayoutPresets,
    saveLayout,
    autoArrangeLayout,
    saveCurrentLayoutAsPreset,
    namedPresets,
    activePresetKey,
    activePresetName,
    createNewPreset,
    deletePreset,
    renamePreset,
    applyPreset,
    ensureDefaultPreset,
    loadPresetsFromAPI,
    resetLayout,

    miniWidgets,
    isMiniWidgetActive,
    toggleMiniWidget,
  }
})
