/**
 * Apple Calendar / Google Calendar event packing layout.
 *
 * Overlapping events are arranged horizontally in columns.
 * Width = 1 / (concurrent events in the overlapping group).
 * Non-overlapping events expand to full width.
 *
 * Algorithm:
 *   1. Sort by start time, then duration (longer first)
 *   2. Group into overlapping clusters (connected components)
 *   3. Within each cluster, greedy column assignment:
 *      place each event in the first column not occupied at its start time
 *   4. Width = 100% / totalColumns, Left = colIndex * (100% / totalColumns)
 */

const toMinutes = (time) => {
  if (!time) return 0
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
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

  // Sort: start time ascending, then duration descending (longer first)
  const sorted = [...items].sort((a, b) => {
    if (a._start !== b._start) return a._start - b._start
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

  // Phase 2: Greedy column assignment within each cluster
  for (const cluster of clusters) {
    const columns = [] // columns[colIdx] = events in this column
    for (const ev of cluster) {
      let col = 0
      while (col < columns.length) {
        // Column is available if no event in it still runs when we start
        if (!columns[col].some(e => e._end > ev._start)) {
          break
        }
        col++
      }
      if (col >= columns.length) columns.push([])
      columns[col].push(ev)
      ev._col = col
    }
    cluster._totalCols = columns.length
  }

  // Phase 3: Build output
  return items.map(ev => {
    const cluster = clusters.find(c => c.includes(ev))
    const totalCols = cluster._totalCols || 1
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

    if (totalCols > 1) {
      result.left = `${(col / totalCols) * 100}%`
      result.width = `${100 / totalCols}%`
    }

    return result
  })
}
