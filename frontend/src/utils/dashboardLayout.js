const COLS = 12

const TYPE_META = {
  todo: { priority: 100, group: 0 },
  'agent-mini': { priority: 90, group: 0 },
  messages: { priority: 80, group: 0 },
  'compose-mini': { priority: 70, group: 1 },
  heatmap: { priority: 60, group: 1 },
  markdown: { priority: 20, group: 2 }
}

const getMeta = (item) => TYPE_META[item.type] || { priority: 40, group: 1 }

export const createLayoutKey = (layout) => {
  return layout
    .map(item => item.type)
    .filter(Boolean)
    .sort()
    .join('|')
}

export const DEFAULT_DASHBOARD_LAYOUT_PRESETS = {
  'markdown|messages|todo': {
    items: [
      { type: 'todo', x: 0, y: 0, w: 4, h: 6 },
      { type: 'messages', x: 4, y: 0, w: 8, h: 6 },
      { type: 'markdown', x: 0, y: 6, w: 12, h: 8 }
    ]
  },
  'heatmap|messages|todo': {
    items: [
      { type: 'todo', x: 0, y: 0, w: 4, h: 6 },
      { type: 'messages', x: 4, y: 0, w: 5, h: 6 },
      { type: 'heatmap', x: 9, y: 0, w: 3, h: 1, heatmapVariant: 'wide' }
    ]
  },
  'agent-mini|messages|todo': {
    items: [
      { type: 'todo', x: 0, y: 0, w: 4, h: 6 },
      { type: 'messages', x: 4, y: 0, w: 4, h: 6 },
      { type: 'agent-mini', x: 8, y: 0, w: 4, h: 6 }
    ]
  },
  'compose-mini|heatmap': {
    items: [
      { type: 'compose-mini', x: 0, y: 0, w: 4, h: 7 },
      { type: 'heatmap', x: 4, y: 0, w: 3, h: 1, heatmapVariant: 'wide' }
    ]
  },
  'agent-mini|compose-mini|heatmap|markdown|messages|todo': {
    items: [
      { type: 'todo', x: 0, y: 0, w: 4, h: 6 },
      { type: 'messages', x: 4, y: 0, w: 4, h: 6 },
      { type: 'agent-mini', x: 8, y: 0, w: 4, h: 6 },
      { type: 'compose-mini', x: 0, y: 6, w: 4, h: 7 },
      { type: 'heatmap', x: 4, y: 6, w: 3, h: 1, heatmapVariant: 'wide' },
      { type: 'markdown', x: 0, y: 13, w: 12, h: 8 }
    ]
  }
}

const clampSize = (item) => {
  const minW = item.minW || 1
  const minH = item.minH || 1
  const maxW = Number.isFinite(item.maxW) ? item.maxW : COLS
  const maxH = Number.isFinite(item.maxH) ? item.maxH : Infinity

  return {
    ...item,
    w: Math.min(Math.max(item.w || minW, minW), maxW, COLS),
    h: Math.min(Math.max(item.h || minH, minH), maxH)
  }
}

export const createLayoutPreset = (layout) => {
  const items = layout.map(item => ({
    type: item.type,
    x: item.x,
    y: item.y,
    w: item.w,
    h: item.h,
    heatmapVariant: item.heatmapVariant
  }))

  return {
    key: createLayoutKey(layout),
    createdAt: new Date().toISOString(),
    items
  }
}

export const applyLayoutPreset = (layout, preset) => {
  if (!preset?.items?.length) return null

  const byType = new Map(layout.map(item => [item.type, item]))
  const placedTypes = new Set()
  const placed = []

  for (const presetItem of preset.items) {
    const current = byType.get(presetItem.type)
    if (!current) continue

    placedTypes.add(presetItem.type)
    placed.push(clampSize({
      ...current,
      x: presetItem.x,
      y: presetItem.y,
      w: presetItem.w,
      h: presetItem.h,
      heatmapVariant: presetItem.heatmapVariant || current.heatmapVariant
    }))
  }

  if (placed.length !== layout.length) {
    return null
  }

  return placed
}

const sortForArrangement = (items) => {
  return [...items].sort((a, b) => {
    const metaA = getMeta(a)
    const metaB = getMeta(b)
    if (metaA.group !== metaB.group) return metaA.group - metaB.group
    if (metaA.priority !== metaB.priority) return metaB.priority - metaA.priority

    const areaA = (a.w || 1) * (a.h || 1)
    const areaB = (b.w || 1) * (b.h || 1)
    if (areaA !== areaB) return areaB - areaA

    return String(a.i).localeCompare(String(b.i))
  })
}

const getPlacementScore = (columns, item, x) => {
  const span = columns.slice(x, x + item.w)
  const y = Math.max(...span)
  const nextColumns = [...columns]
  for (let col = x; col < x + item.w; col += 1) {
    nextColumns[col] = y + item.h
  }

  const maxHeight = Math.max(...nextColumns)
  const minHeight = Math.min(...nextColumns)
  const roughness = nextColumns.reduce((sum, height, index) => {
    if (index === 0) return sum
    return sum + Math.abs(height - nextColumns[index - 1])
  }, 0)
  const buriedSpace = span.reduce((sum, height) => sum + (y - height), 0)

  return {
    x,
    y,
    score: maxHeight * 100 + (maxHeight - minHeight) * 8 + roughness * 3 + buriedSpace * 12 + x * 0.5
  }
}

const findBestPlacement = (columns, item) => {
  let best = null
  const maxX = COLS - item.w

  for (let x = 0; x <= maxX; x += 1) {
    const placement = getPlacementScore(columns, item, x)
    if (!best || placement.score < best.score) {
      best = placement
    }
  }

  return best || { x: 0, y: Math.max(...columns) }
}

export const arrangeDashboardLayout = (layout) => {
  const columns = Array(COLS).fill(0)
  const arranged = []

  for (const item of sortForArrangement(layout.map(clampSize))) {
    const placement = findBestPlacement(columns, item)
    const placed = { ...item, x: placement.x, y: placement.y }

    for (let col = placed.x; col < placed.x + placed.w; col += 1) {
      columns[col] = placed.y + placed.h
    }

    arranged.push(placed)
  }

  return arranged
}

export const hasLayoutCollisions = (layout) => {
  return layout.some((item, index) => {
    return layout.slice(index + 1).some(other => {
      return item.x < other.x + other.w &&
        item.x + item.w > other.x &&
        item.y < other.y + other.h &&
        item.y + item.h > other.y
    })
  })
}
