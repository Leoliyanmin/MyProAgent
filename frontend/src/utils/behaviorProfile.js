const DAY_MS = 24 * 60 * 60 * 1000
const RECENT_WINDOW_DAYS = 30

const ACTIVE_PERIODS = [
  { key: 'morning', label: '上午', start: 6, end: 12 },
  { key: 'afternoon', label: '下午', start: 12, end: 18 },
  { key: 'evening', label: '晚上', start: 18, end: 23 },
  { key: 'late_night', label: '深夜', start: 23, end: 30 }
]

const MODULE_LABELS = {
  calendar: '日历',
  dashboard: '工作台',
  todo: 'Todo',
  email: '邮件',
  files: '文件',
  chat: 'AI 对话'
}

const clamp01 = (value) => Math.max(0, Math.min(1, value))

const scoreFromCount = (count, target = 6) => {
  return clamp01(count / target)
}

const getEventHour = (event) => {
  const date = new Date(event.timestamp)
  if (Number.isNaN(date.getTime())) return null
  return date.getHours()
}

const getActivePeriod = (hour) => {
  if (hour === null) return null
  return ACTIVE_PERIODS.find(period => {
    const normalizedHour = hour < 6 ? hour + 24 : hour
    return normalizedHour >= period.start && normalizedHour < period.end
  })?.key || null
}

const recentEvents = (events, now = new Date()) => {
  const cutoff = now.getTime() - RECENT_WINDOW_DAYS * DAY_MS
  return events.filter(event => {
    const time = new Date(event.timestamp).getTime()
    return Number.isFinite(time) && time >= cutoff
  })
}

const countBy = (events, getter) => {
  return events.reduce((acc, event) => {
    const key = getter(event)
    if (!key) return acc
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})
}

const topEntries = (counts, limit = 3) => {
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit)
}

const buildPreferenceText = (indicators) => {
  const prefs = []
  if (indicators.visual_sensitive >= 0.55) prefs.push('偏好可视化反馈')
  if (indicators.detail_oriented >= 0.55) prefs.push('喜欢细调细节')
  if (indicators.automation_preference >= 0.55) prefs.push('倾向自动化整理')
  if (indicators.organization_driven >= 0.55) prefs.push('重视结构化安排')
  return prefs.length ? prefs.join(' · ') : '偏好仍在学习中'
}

const buildBehaviorText = ({ moduleCounts, periodCounts, indicators }) => {
  const modules = topEntries(moduleCounts, 3).map(([module]) => MODULE_LABELS[module] || module)
  const periods = topEntries(periodCounts, 2).map(([period]) => ACTIVE_PERIODS.find(p => p.key === period)?.label || period)
  const style = indicators.iterative >= 0.65
    ? '迭代调整型'
    : indicators.organization_driven >= 0.6
      ? '规划整理型'
      : '灵活推进型'

  return [
    modules.length ? `最近常用: ${modules.join('、')}` : '',
    periods.length ? `活跃时段: ${periods.join('、')}` : '',
    `工作方式: ${style}`
  ].filter(Boolean).join('；')
}

export const computeBehaviorProfile = (events, now = new Date()) => {
  const allEvents = Array.isArray(events) ? events : []
  const recent = recentEvents(allEvents, now)
  const typeCounts = countBy(recent, event => event.type)
  const moduleCounts = countBy(recent, event => event.metadata?.module)
  const periodCounts = countBy(recent, event => getActivePeriod(getEventHour(event)))

  const indicators = {
    detail_oriented: clamp01(0.35 +
      scoreFromCount((typeCounts.calendar_event_moved || 0) + (typeCounts.dashboard_template_saved || 0), 6) * 0.5),
    visual_sensitive: clamp01(0.35 +
      scoreFromCount((typeCounts.dashboard_template_saved || 0) + (typeCounts.widget_toggled || 0), 5) * 0.45),
    organization_driven: clamp01(0.35 +
      scoreFromCount(
        (typeCounts.calendar_event_created || 0) +
        (typeCounts.dashboard_auto_arranged || 0) +
        (typeCounts.dashboard_template_saved || 0) +
        (typeCounts.todo_completed || 0),
        8
      ) * 0.55),
    automation_preference: clamp01(0.3 +
      scoreFromCount((typeCounts.dashboard_auto_arranged || 0) + (typeCounts.dashboard_template_saved || 0), 5) * 0.55),
    iterative: clamp01(0.35 +
      scoreFromCount(
        (typeCounts.calendar_event_moved || 0) +
        (typeCounts.dashboard_auto_arranged || 0) +
        (typeCounts.dashboard_template_saved || 0),
        7
      ) * 0.55)
  }

  return {
    eventCount: allEvents.length,
    recentEventCount: recent.length,
    typeCounts,
    moduleCounts,
    periodCounts,
    workPreferenceText: buildPreferenceText(indicators),
    behaviorPatternText: buildBehaviorText({ moduleCounts, periodCounts, indicators }),
    indicators,
    generatedAt: now.toISOString()
  }
}
