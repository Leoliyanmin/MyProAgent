/**
 * Apple Calendar / Google Calendar event packing layout.
 *
 * Overlapping peer events are arranged horizontally in columns.
 * Container events, such as 08:00-13:00 behind shorter 09:00-10:00
 * overlaps, remain full width and render below their contained events.
 *
 * Algorithm:
 *   1. Sort by start time, then priority (P0 before P4), then duration
 *   2. Group into overlapping clusters (connected components)
 *   3. Assign top-level events to lanes
 *   4. Assign contained child events inside their top-level parent lane
 *   5. Width and left are expressed as percentages of the day column
 */

const toMinutes = (time) => {
  if (!time) return 0
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

const getPriority = (event) => {
  return Number.isFinite(Number(event.priority)) ? Number(event.priority) : 2
}

const childNestingStartThresholdMinutes = 30

const assignColumns = (events) => {
  const columns = []
  for (const ev of events) {
    let col = 0
    while (col < columns.length) {
      if (!columns[col].some(e => e._end > ev._start)) {
        break
      }
      col++
    }
    if (col >= columns.length) columns.push([])
    columns[col].push(ev)
    ev._col = col
  }
  return columns.length
}

/**
 * @param {Array} events — { id, startTime, endTime }
 * @param {Object} options
 * @param {number} options.hourHeight — px per hour (default 50)
 * @param {number} options.minHeight — minimum event height in px (default 25)
 */
export function computeEventLayout(events, options = {}) {
  const { hourHeight = 50, minHeight = 25 } = options

  if (!events || events.length === 0) return []

  // Parse to internal format
  const items = events.map(e => ({
    ...e,
    _start: toMinutes(e.startTime),
    _end: toMinutes(e.endTime || '23:59'),
  }))

  if (items.length === 1) {
    const ev = items[0]
    const dur = Math.max(0.5, (ev._end - ev._start) / 60)
    return [{
      ...ev,
      top: `${(ev._start / 60) * hourHeight}px`,
      height: `${Math.max(minHeight, dur * hourHeight)}px`,
      totalColumns: 1,
      column: 0,
    }]
  }

  // Sort: start time ascending, then priority, then duration descending.
  const sorted = [...items].sort((a, b) => {
    if (a._start !== b._start) return a._start - b._start
    const priorityDiff = getPriority(a) - getPriority(b)
    if (priorityDiff !== 0) return priorityDiff
    return (b._end - b._start) - (a._end - a._start)
  })

  // Phase 1: Group into overlapping clusters
  // Two events overlap if one starts before the other ends
  const clusters = []
  for (const ev of sorted) {
    let placed = false
    for (const cluster of clusters) {
      if (cluster.some(c => c._end > ev._start && c._start < ev._end)) {
        cluster.push(ev)
        placed = true
        break
      }
    }
    if (!placed) clusters.push([ev])
  }

  // Phase 2: Assign top-level lanes, then nested lanes inside each parent.
  for (const cluster of clusters) {
    const roots = []
    const children = []

    for (const ev of cluster) {
      const parentCandidates = cluster.filter(other => {
        if (other === ev) return false
        const startsDeepInsideParent = ev._start - other._start >= childNestingStartThresholdMinutes
        return other._start < ev._start &&
          other._end > ev._start &&
          startsDeepInsideParent &&
          (other._end - other._start) > (ev._end - ev._start)
      })

      if (parentCandidates.length === 0) {
        roots.push(ev)
      } else {
        children.push(ev)
      }
    }

    const rootCols = Math.max(1, assignColumns(roots))

    for (const root of roots) {
      root._rootCols = rootCols
      root._laneLeft = (root._col / rootCols) * 100
      root._laneWidth = 100 / rootCols
      root._children = []
    }

    for (const child of children) {
      const parent = roots
        .filter(root => root._start < child._start &&
          root._end > child._start &&
          child._start - root._start >= childNestingStartThresholdMinutes &&
          (root._end - root._start) > (child._end - child._start))
        .sort((a, b) => {
          if (a._col !== b._col) return a._col - b._col
          return (a._end - a._start) - (b._end - b._start)
        })[0]
      if (parent) {
        child._parent = parent
        parent._children.push(child)
      } else {
        roots.push(child)
        child._rootCols = rootCols
        child._laneLeft = 0
        child._laneWidth = 100
      }
    }

    for (const parent of roots) {
      if (!parent._children || parent._children.length === 0) continue

      parent._isBackgroundContainer = true
      const childCols = Math.max(rootCols === 1 ? 2 : 1, assignColumns(parent._children))
      for (const child of parent._children) {
        child._childCols = childCols
        child._laneLeft = parent._laneLeft + (child._col / childCols) * parent._laneWidth
        child._laneWidth = parent._laneWidth / childCols
      }
    }
  }

  // Phase 3: Build output
  return items.map(ev => {
    const cluster = clusters.find(c => c.includes(ev))
    const totalCols = ev._childCols || ev._rootCols || 1
    const col = ev._col !== undefined ? ev._col : 0

    const durHr = Math.max(0.5, (ev._end - ev._start) / 60)
    const top = (ev._start / 60) * hourHeight
    const height = Math.max(minHeight, durHr * hourHeight)

    const result = {
      ...ev,
      top: `${top}px`,
      height: `${height}px`,
      totalColumns: totalCols,
      column: col,
    }

    if (ev._isBackgroundContainer) {
      result.totalColumns = totalCols
      if (ev._rootCols > 1) {
        result.left = `${ev._laneLeft}%`
        result.width = `${ev._laneWidth}%`
      }
      result.zIndex = 8
      result.isBackgroundContainer = true
    } else if (ev._laneWidth !== undefined && ev._laneWidth < 100) {
      result.left = `${ev._laneLeft}%`
      result.width = `${ev._laneWidth}%`
      result.zIndex = 12 + col
    } else if (totalCols > 1) {
      result.left = `${(col / totalCols) * 100}%`
      result.width = `${100 / totalCols}%`
      result.zIndex = 12 + col
    } else {
      result.zIndex = 10
    }

    return result
  })
}
