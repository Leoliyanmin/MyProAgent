/**
 * Apple Calendar containment layout.
 *
 * Long events act as containers. Shorter overlapping events are nested inside
 * with pixel indentation instead of being placed in separate columns.
 *
 * Visual output:
 *   ┌──────────────────────────┐  depth=0 (parent, full width)
 *   │  ┌──────────┐            │  depth=1 (child, 18px indent)
 *   │  │  ┌────┐  │            │  depth=2 (grandchild, 36px indent)
 *   │  │  └────┘  │            │
 *   │  └──────────┘            │
 *   └──────────────────────────┘
 *
 * Algorithm:
 *   1. Sort by duration (longest first) — longest events are "containers"
 *   2. depth = count of longer events that strictly contain this event
 *   3. If siblings at same depth overlap → bump later one deeper
 *   4. left = depth * indentStep, width = 100% - depth * indentStep
 *   5. z-index proportional to depth (children render above parents)
 */

const toMinutes = (time) => {
  if (!time) return 0
  const [h, m] = time.split(':').map(Number)
  return h * 60 + m
}

/**
 * @param {Array} events — { id, startTime, endTime }
 * @param {Object} options
 * @param {number} options.indentStep — px per nesting level (default 18)
 * @param {number} options.hourHeight — px per hour (default 50)
 * @param {number} options.minHeight — minimum event height in px (default 25)
 */
export function computeEventLayout(events, options = {}) {
  const {
    indentStep = 18,
    hourHeight = 50,
    minHeight = 25,
  } = options

  if (!events || events.length <= 1) return events || []

  const items = events.map((e) => ({
    ...e,
    _startMin: toMinutes(e.startTime),
    _endMin: toMinutes(e.endTime || '23:59'),
    _durationMin: toMinutes(e.endTime || '23:59') - toMinutes(e.startTime),
    _depth: 0,
  }))

  const sorted = [...items].sort((a, b) => b._durationMin - a._durationMin)

  // Phase 1: compute depth by strict containment
  for (let i = 0; i < sorted.length; i++) {
    const ev = sorted[i]
    for (let j = 0; j < i; j++) {
      const longer = sorted[j]
      if (longer._startMin <= ev._startMin && longer._endMin >= ev._endMin) {
        ev._depth = Math.max(ev._depth, longer._depth + 1)
      }
    }
  }

  // Phase 2: bump depth for overlapping siblings at same level
  let changed = true
  while (changed) {
    changed = false
    const maxD = Math.max(...sorted.map(e => e._depth), 0)
    for (let d = 0; d <= maxD; d++) {
      const siblings = sorted
        .filter(e => e._depth === d)
        .sort((a, b) => a._startMin - b._startMin)
      for (let i = 1; i < siblings.length; i++) {
        if (siblings[i]._startMin < siblings[i - 1]._endMin) {
          siblings[i]._depth++
          changed = true
        }
      }
    }
  }

  // Phase 3: build output
  const maxDepth = Math.max(...sorted.map(e => e._depth), 0)

  return sorted.map((ev) => {
    const durationMinutes = Math.max(30, ev._endMin - ev._startMin)
    const top = (ev._startMin / 60) * hourHeight
    const height = Math.max(minHeight, (durationMinutes / 60) * hourHeight)

    const base = {
      ...ev,
      top: `${top}px`,
      height: `${height}px`,
      depth: ev._depth,
      maxDepth,
    }

    if (ev._depth === 0) return base

    const leftPx = ev._depth * indentStep
    return {
      ...base,
      left: `${leftPx}px`,
      width: `calc(100% - ${leftPx + 3}px)`,
    }
  })
}
