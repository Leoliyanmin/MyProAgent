/**
 * Apple Calendar-style event layout algorithm.
 *
 * Input: array of { id, startTime, endTime }
 * Output: each event gets { top, height, left, width, column, totalColumns }
 *
 * Strategy: greedy column assignment on sorted intervals.
 * Each column = one horizontal lane. Events that don't overlap can share a column.
 * Width = 100% / totalColumns.
 *
 * Complexity: O(n log n) from sorting, O(n * columns) for assignment.
 * For calendar views, n ≤ 50, columns ≤ 10 — negligible.
 */

/** "HH:MM" → minutes from midnight */
const toMinutes = (time) => {
  if (!time) return 0
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

/**
 * @param {Array} events — raw event objects with at least { id, startTime, endTime }
 * @param {Object} options
 * @param {number} options.hourHeight — px per hour (default 50)
 * @param {number} options.columnGap — px gap between columns (default 4)
 * @param {number} options.minHeight — minimum event height in px (default 25)
 * @returns {Array} same events augmented with layout props:
 *   { top, height, left, width, column, totalColumns }
 */
export function computeEventLayout(events, options = {}) {
  const {
    hourHeight = 50,
    columnGap = 4,
    minHeight = 25,
  } = options

  if (!events || events.length === 0) return []

  const items = events.map((e) => ({
    ...e,
    _startMin: toMinutes(e.startTime),
    _endMin: toMinutes(e.endTime || '23:59'),
  }))

  const sorted = [...items].sort((a, b) => {
    const d = a._startMin - b._startMin
    if (d !== 0) return d
    return b._endMin - a._endMin
  })

  const columns = []
  const assignment = new Array(sorted.length)

  for (let i = 0; i < sorted.length; i++) {
    const ev = sorted[i]
    let placed = false

    for (let col = 0; col < columns.length; col++) {
      if (columns[col] <= ev._startMin) {
        columns[col] = ev._endMin
        assignment[i] = col
        placed = true
        break
      }
    }

    if (!placed) {
      assignment[i] = columns.length
      columns.push(ev._endMin)
    }
  }

  const totalColumns = columns.length

  return sorted.map((ev, i) => {
    const col = assignment[i]
    const durationMinutes = Math.max(30, ev._endMin - ev._startMin)
    const top = (ev._startMin / 60) * hourHeight
    const height = Math.max(minHeight, (durationMinutes / 60) * hourHeight)

    const base = {
      ...ev,
      top: `${top}px`,
      height: `${height}px`,
      column: col,
      totalColumns,
    }

    if (totalColumns <= 1) return base

    return {
      ...base,
      left: `${(col / totalColumns) * 100}%`,
      width: `calc(${100 / totalColumns}% - ${columnGap + 2}px)`,
    }
  })
}
