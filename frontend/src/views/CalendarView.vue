<template>
  <div class="calendar-wrapper">
    <div class="calendar-toolbar">
      <div class="toolbar-left">
        <button class="mac-btn" @click="goToToday">今天</button>
        <div class="nav-arrows">
          <button class="icon-btn" @click="prevPeriod">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>
          <button class="icon-btn" @click="nextPeriod">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
        </div>
      </div>

      <div class="toolbar-center">
        <h2 class="current-date">{{ headerTitle }}</h2>
      </div>

      <div class="toolbar-right">
        <button class="icon-btn import-btn" @click="handleImportTIS" :class="{ spinning: isImporting }" title="导入课表">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        </button>
        <button class="icon-btn import-bb-btn" @click="handleImportBB" :class="{ spinning: isImportingBB }" title="导入作业">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="9" y1="7" x2="16" y2="7"/><line x1="9" y1="11" x2="14" y2="11"/></svg>
        </button>
        <button class="icon-btn refresh-btn" @click="refreshFromBackend" :class="{ spinning: isRefreshing }" title="同步">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
        </button>
        <div class="segmented-control">
<button class="segment" :class="{ active: calendarStore.viewType === 'day' }" @click="calendarStore.viewType = 'day'">日</button>
        <button class="segment" :class="{ active: calendarStore.viewType === 'week' }" @click="calendarStore.viewType = 'week'">周</button>
        <button class="segment" :class="{ active: calendarStore.viewType === 'month' }" @click="calendarStore.viewType = 'month'">月</button>
        </div>
      </div>
    </div>

    <div v-if="importToast.message" class="import-toast" :class="importToast.type">
      <span>{{ importToast.message }}</span>
      <button class="toast-close" @click="importToast.message = ''">&times;</button>
    </div>

    <div class="calendar-grid-container" v-if="calendarStore.viewType === 'month'">
      <div class="mock-calendar-body">
        <div class="weekdays-header">
          <span v-for="w in weekdays" :key="w">{{ w }}</span>
        </div>
        <div class="days-grid">
          <div 
            v-for="(day, index) in calendarDays" 
            :key="index" 
            class="day-cell"
            :class="{ 'is-other-month': !day.isCurrentMonth, 'is-today': day.isToday, 'drag-over': dragOverCellIndex === day.date }"
            @click.self="openEventModal(day.date)"
            @dragover.prevent="onDragOver($event, day)"
            @dragenter="onDragEnter($event, day)"
            @dragleave="onDragLeave"
            @drop="onDrop($event, day)"
          >
            <span class="date-num" :class="{ 'is-today-text': day.isToday }" @click.stop="openEventModal(day.date)">{{ day.dayNum }}</span>
            <div class="events-container" @click.self="openEventModal(day.date)">
              <div
                v-for="event in day.events.slice(0, 3)"
                :key="event.id"
                class="event-bar"
                :class="{'is-completed': event.completed, 'multi-start': event.isStart, 'multi-mid': event.isMid, 'multi-end': event.isEnd}"
              :style="{ backgroundColor: event.color ? event.color + '25' : '', color: event.priority >= 4 ? '#000000' : (event.color || '') }"
                @click.stop="editEvent(event)"
                :title="event.title"
                draggable="true"
                @dragstart="onDragStart($event, event)"
                @dragend="onDragEnd"
              >
                {{ event.isStart || day.date === event.start ? event.title : '\u00A0' }}
              </div>
              <div
                v-if="day.events.length > 3"
                class="more-events"
                @click.stop="switchToDayView(day.date)"
              >
                +{{ day.events.length - 3 }} 更多
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="calendar-grid-container" v-else>
      <div class="week-timeline-body">
        <div class="week-timeline-header" ref="weekTimelineHeaderRef">
          <div class="time-axis-placeholder"></div>
          <div 
            v-for="(day, i) in visibleDays" 
            :key="'wh'+i" 
            class="week-timeline-day-header"
            :class="{ 'is-today-text': day.isToday }"
            @click="openEventModal(day.date)"
          >
            <span class="day-name">{{ weekdays[calendarStore.viewType === 'week' ? i : calendarStore.currentDate.getDay()] }}</span>
            <span class="day-num" :class="{ 'is-today-bg': day.isToday }">{{ day.dayNum }}</span>
          </div>
        </div>
        <div class="week-all-day-row" ref="weekAllDayRowRef" :class="{'day-layout': calendarStore.viewType === 'day'}">
          <div class="time-axis-placeholder"><span class="all-day-label">全天</span></div>
          <div 
            v-for="(day, i) in visibleDays" 
            :key="'wa'+i" 
            class="week-all-day-cell"
            :class="{ 'is-today-col': day.isToday }"
            @click.self="openEventModal(day.date)"
          >
            <div
              v-for="event in calendarStore.viewType === 'day' ? day.allDayEvents : day.allDayEvents.slice(0, 2)"
              :key="event.id"
              class="event-bar"
              :class="{'is-completed': event.completed}"
              :style="{ backgroundColor: event.color ? event.color + '25' : '', color: event.source === 'tis' ? '#1c1c1e' : (event.color || '') }"
              @click.stop="editEvent(event)"
              :title="event.title"
            >
              {{ event.title }}
            </div>
            <div
              v-if="calendarStore.viewType !== 'day' && day.allDayEvents.length > 2"
              class="more-events"
              @click.stop="switchToDayView(day.date)"
            >
              +{{ day.allDayEvents.length - 2 }} 更多
            </div>
          </div>
        </div>
        <div class="week-timeline-scroll" ref="weekTimelineScrollRef">
          <div class="week-timeline-grid" :class="{'day-layout': calendarStore.viewType === 'day'}">
            <div class="time-axis">
              <div class="time-slot" v-for="h in hours" :key="'t'+h">
                <span>{{ String(h).padStart(2, '0') }}:00</span>
                <div class="time-separator"></div>
              </div>
            </div>
            <div class="week-day-columns" :class="{'day-layout': calendarStore.viewType === 'day'}">
              <div 
                v-for="(day, i) in visibleDays" 
                :key="'wc'+i" 
                class="week-day-column"
                :data-date="day.date"
                :class="{ 'is-today-col': day.isToday, 'drag-over-col': timedDragOverDate === day.date }"
                @click.self="openEventModal(day.date)"
                @dragover.prevent="onTimedColumnDragOver($event, day)"
                @drop="onTimedColumnDrop($event, day)"
              >
                <div
                  class="hour-slot"
                  v-for="h in hours"
                  :key="'ts'+h"
                  @click.self="openEventModal(day.date, h)"
                  @dragover.prevent.stop="onTimedColumnDragOver($event, day)"
                  @drop.prevent.stop="onTimedColumnDrop($event, day)"
                ></div>
                
                <div
                  v-for="event in day.timedEvents"
                  :key="event.id"
                  class="timed-event-card"
                  :class="{'is-completed': event.completed}"
                  :style="getTimedEventStyle(event)"
                  @click.stop="onTimedCardClick(event)"
                  @mousedown.stop="onTimedMouseDragStart($event, event)"
                  draggable="true"
                  @dragstart="onTimedDragStart($event, event)"
                  @dragover.prevent.stop="onTimedColumnDragOver($event, day)"
                  @drop.prevent.stop="onTimedColumnDrop($event, day)"
                  @dragend="onTimedDragEnd"
                >
                  <div class="timed-event-title">{{ event.title }}</div>
                  <div class="timed-event-time">{{ event.startTime }} - {{ event.endTime || '23:59' }}</div>
                  <div class="resize-handle" @mousedown="onResizeStart($event, event)"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Event Edit Modal -->
    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal-content mac-modal">
        <h3>{{ isEditing ? '编辑日程' : '添加日程' }}</h3>
        <label>标题</label>
        <input type="text" v-model="draftEvent.title" class="mac-input" placeholder="输入日程或TODO标题" />
        <div class="date-row">
          <div>
            <label>开始日期</label>
            <input type="date" v-model="draftEvent.start" class="mac-input" />
          </div>
          <div>
            <label>开始时间</label>
            <div class="time-picker-row">
              <select v-model="startTimeHour" class="mac-input time-select">
                <option value="">--</option>
                <option v-for="h in hours24" :key="h" :value="h">{{ h }}</option>
              </select>
              <span class="time-sep">:</span>
              <select v-model="startTimeMinute" class="mac-input time-select">
                <option value="">--</option>
                <option v-for="m in minutes60" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="date-row">
          <div>
            <label>结束日期</label>
            <input type="date" v-model="draftEvent.end" class="mac-input" />
          </div>
          <div>
            <label>结束时间</label>
            <div class="time-picker-row">
              <select v-model="endTimeHour" class="mac-input time-select">
                <option value="">--</option>
                <option v-for="h in hours24" :key="h" :value="h">{{ h }}</option>
              </select>
              <span class="time-sep">:</span>
              <select v-model="endTimeMinute" class="mac-input time-select">
                <option value="">--</option>
                <option v-for="m in minutes60" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>
        <div class="color-picker-row">
          <label>优先级(分色)</label>
          <div class="priority-options">
            <div 
              v-for="p in priorityOptions" 
              :key="p.level" 
              class="priority-chip"
              :class="{ active: draftEvent.priority === p.level }"
              :style="{ backgroundColor: p.color + (draftEvent.priority === p.level ? '' : '15'), color: draftEvent.priority === p.level ? '#fff' : p.color, borderColor: p.color }"
              @click="setPriority(p)"
            >
              P{{ p.level }} - {{ p.label }}
            </div>
          </div>
        </div>
        <div class="mac-checkbox-row">
          <label class="mac-checkbox-label">
            <input type="checkbox" v-model="draftEvent.showInTodo" class="mac-checkbox" />
            <span>在 Todo 中显示</span>
          </label>
        </div>
        <label>备注</label>
        <textarea v-model="draftEvent.description" class="mac-input" placeholder="添加备注..." rows="2"></textarea>
        <p v-if="validationMessage" class="form-validation-message">{{ validationMessage }}</p>
        <div class="modal-actions">
          <button class="mac-btn delete-btn-modal" v-if="isEditing" @click="deleteEvent">删除</button>
          <div style="flex: 1"></div>
          <button class="mac-btn secondary" @click="closeModal">取消</button>
          <button class="mac-btn primary" @click="saveEvent">{{ isEditing ? '保存' : '添加' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useCalendarStore } from '../stores/calendar.js'
import { useDashboardStore } from '../stores/dashboard.js'

const calendarStore = useCalendarStore()
const dashboardStore = useDashboardStore()

const isRefreshing = ref(false)
const isImporting = ref(false)
const isImportingBB = ref(false)

const importToast = reactive({ message: '', type: 'error' })

const handleImportTIS = async () => {
  if (isImporting.value) return
  isImporting.value = true
  try {
    const result = await calendarStore.importTISSchedule()
    if (result.success) {
      if (result.added > 0) {
        importToast.message = `已导入 ${result.uniqueCourses} 门课程（共 ${result.total} 节课）`
        importToast.type = 'success'
      } else {
        importToast.message = `课表已是最新，共 ${result.uniqueCourses || 0} 门课程`
        importToast.type = 'success'
      }
      setTimeout(() => { importToast.message = '' }, 4000)
    } else if (result.message) {
      importToast.message = result.message
      importToast.type = 'error'
      setTimeout(() => { importToast.message = '' }, 6000)
    }
  } catch (err) {
    console.error('导入课表异常:', err)
  } finally {
    isImporting.value = false
  }
}

const handleImportBB = async () => {
  if (isImportingBB.value) return
  isImportingBB.value = true
  try {
    const result = await calendarStore.importBlackboardAssignments()
    if (result.success) {
      importToast.message = `成功导入 ${result.eventsAdded} 个日历事件, ${result.todosAdded} 个待办`
      importToast.type = 'success'
      setTimeout(() => { importToast.message = '' }, 4000)
    } else if (result.message) {
      importToast.message = result.message
      importToast.type = 'error'
      setTimeout(() => { importToast.message = '' }, 6000)
    }
  } catch (err) {
    console.error('导入作业异常:', err)
  } finally {
    isImportingBB.value = false
  }
}

const refreshFromBackend = async () => {
  if (isRefreshing.value) return
  isRefreshing.value = true
  try {
    await Promise.all([
      calendarStore.loadSchedules(),
      dashboardStore.loadTodosFromBackend()
    ])
  } catch (err) {
    console.error('Failed to refresh calendar data:', err)
  } finally {
    isRefreshing.value = false
  }
}

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const showModal = ref(false)
const isEditing = ref(false)
const draftEvent = ref({ id: null, title: '', start: '', end: '', startTime: '', endTime: '', priority: 3, color: '#34c759', description: '', showInTodo: true })
const validationMessage = ref('')
const weekTimelineHeaderRef = ref(null)
const weekAllDayRowRef = ref(null)
const weekTimelineScrollRef = ref(null)
let weekScrollbarSyncRaf = 0

// Drag-and-drop state
const draggingEvent = ref(null)
const dragOverCellIndex = ref(null)
const timedDragOverDate = ref(null)
const manualDragEvent = ref(null)
const manualDragging = ref(false)
const manualDragStartX = ref(0)
const manualDragStartY = ref(0)
const suppressNextCardClick = ref(false)
const isResizing = ref(false)
const resizeStartY = ref(0)
const resizeOriginalEnd = ref('')
const resizeEvent = ref(null)

const priorityOptions = [
  { level: 0, color: '#ff3b30', label: '紧急且重要' },
  { level: 1, color: '#ff9500', label: '重要不紧急' },
  { level: 2, color: '#007aff', label: '紧急不重要' },
  { level: 3, color: '#34c759', label: '不重要不紧急' },
  { level: 4, color: '#8e8e93', label: '固定课程' },
]

const hours24 = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const minutes60 = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))

const startTimeHour = computed({
  get: () => (draftEvent.value.startTime || '').split(':')[0] || '',
  set: (v) => {
    const m = (draftEvent.value.startTime || '').split(':')[1] || '00'
    draftEvent.value.startTime = v ? `${v}:${m}` : ''
  }
})
const startTimeMinute = computed({
  get: () => { const p = (draftEvent.value.startTime || '').split(':'); return p[1] || '' },
  set: (v) => {
    const h = (draftEvent.value.startTime || '').split(':')[0] || '00'
    draftEvent.value.startTime = v !== '' ? `${h}:${v}` : ''
  }
})
const endTimeHour = computed({
  get: () => (draftEvent.value.endTime || '').split(':')[0] || '',
  set: (v) => {
    const m = (draftEvent.value.endTime || '').split(':')[1] || '00'
    draftEvent.value.endTime = v ? `${v}:${m}` : ''
  }
})
const endTimeMinute = computed({
  get: () => { const p = (draftEvent.value.endTime || '').split(':'); return p[1] || '' },
  set: (v) => {
    const h = (draftEvent.value.endTime || '').split(':')[0] || '00'
    draftEvent.value.endTime = v !== '' ? `${h}:${v}` : ''
  }
})

const setPriority = (p) => {
  draftEvent.value.priority = p.level
  draftEvent.value.color = p.color
}

const headerTitle = computed(() => {
  const y = calendarStore.currentDate.getFullYear()
  const m = calendarStore.currentDate.getMonth() + 1
  const d = calendarStore.currentDate.getDate()
  if (calendarStore.viewType === 'month') {
    return `${y}年 ${m}月`
  } else if (calendarStore.viewType === 'week') {
    const sun = new Date(calendarStore.currentDate)
    sun.setDate(d - sun.getDay())
    const sat = new Date(sun)
    sat.setDate(sat.getDate() + 6)
    return `${sun.getFullYear()}年 ${sun.getMonth() + 1}月 ${sun.getDate()}日 - ${sat.getMonth() + 1}月 ${sat.getDate()}日`
  }
  return `${y}年 ${m}月 ${d}日 ${weekdays[calendarStore.currentDate.getDay()]}`
})

const daysInMonth = computed(() => {
  const year = calendarStore.currentDate.getFullYear()
  const month = calendarStore.currentDate.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  const days = []
  // Fill preview month days
  for (let i = 0; i < firstDay.getDay(); i++) {
    const d = new Date(year, month, -i)
    days.unshift(createDayObject(d, false))
  }
  // Fill current month
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const d = new Date(year, month, i)
    days.push(createDayObject(d, true))
  }
  // Fill next month days to complete grid
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i)
    days.push(createDayObject(d, false))
  }
  return days
})

const getISODate = (d) => {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const todayISO = getISODate(new Date())

const createDayObject = (d, isCurrentMonth) => {
  const iso = getISODate(d)
  const events = getEventsForDay(iso)
  return {
    date: iso,
    dayNum: d.getDate(),
    isCurrentMonth,
    isToday: iso === todayISO,
    events: events,
    timedEvents: events.filter(e => !e.isAllDay),
    allDayEvents: events.filter(e => e.isAllDay)
  }
}

const getEventsForDay = (isoDate) => {
    return calendarStore.allEvents.filter(e => {
        return isoDate >= e.start && isoDate <= e.end
    }).map(e => {
        const startTime = e.startTime || ''
        const endTime = e.endTime || ''
        const isAllDay = (e.start === e.end) && (!startTime || startTime === '00:00') && (!endTime || endTime === '23:59' || endTime === '23:59:59')
            || (e.start !== e.end && !startTime && !endTime)
        return {
            ...e,
            isAllDay,
            isStart: isoDate === e.start,
            isEnd: isoDate === e.end,
            isMid: isoDate > e.start && isoDate < e.end
        }
    }).sort((a, b) => {
        const pa = a.priority ?? 2
        const pb = b.priority ?? 2
        if (pa !== pb) return pa - pb
        const timeA = a.startTime || '00:00'
        const timeB = b.startTime || '00:00'
        if (timeA !== timeB) return timeA.localeCompare(timeB)
        return (a.title || '').localeCompare(b.title || '')
    })
  }

const getTimedEventStyle = (event) => {
  const start = event.startTime || "00:00";
  const end = event.endTime || "23:59";
  
  const [sh, sm] = start.split(':').map(Number);
  const [eh, em] = end.split(':').map(Number);
  
  const top = sh * 50 + (sm / 60) * 50;
  let duration = (eh + em / 60) - (sh + sm / 60);
  if (duration < 0.5) duration = 0.5; // min height 30 mins
  const height = duration * 50;
  
  return {
    top: `${top}px`,
    height: `${height}px`,
    backgroundColor: event.color ? event.color + '25' : '',
    color: event.priority >= 4 ? '#000000' : (event.color || ''),
    borderLeft: `3px solid ${event.color || '#007aff'}`
  }
}

const calendarDays = computed(() => daysInMonth.value)

const weekDays = computed(() => {
  const current = calendarStore.currentDate
  const d = current.getDate()
  const day = current.getDay()
  const sun = new Date(current.getFullYear(), current.getMonth(), d - day)
  
  const result = []
  for (let i = 0; i < 7; i++) {
    const temp = new Date(sun.getFullYear(), sun.getMonth(), sun.getDate() + i)
    result.push(createDayObject(temp, true))
  }
  return result
})

const singleDay = computed(() => {
  return [createDayObject(calendarStore.currentDate, true)]
})

const visibleDays = computed(() => {
  return calendarStore.viewType === 'week' ? weekDays.value : singleDay.value
})

const hours = Array.from({ length: 24 }, (_, i) => i)

const syncWeekGridColumns = () => {
  const timelineScrollEl = weekTimelineScrollRef.value
  const scrollbarWidth = timelineScrollEl ? Math.max(0, timelineScrollEl.offsetWidth - timelineScrollEl.clientWidth) : 0
  const offsetPx = `${scrollbarWidth}px`
  if (weekTimelineHeaderRef.value) {
    weekTimelineHeaderRef.value.style.setProperty('--week-scrollbar-offset', offsetPx)
  }
  if (weekAllDayRowRef.value) {
    weekAllDayRowRef.value.style.setProperty('--week-scrollbar-offset', offsetPx)
  }
}

const scheduleWeekGridSync = () => {
  if (typeof window === 'undefined') return
  if (weekScrollbarSyncRaf) {
    window.cancelAnimationFrame(weekScrollbarSyncRaf)
  }
  weekScrollbarSyncRaf = window.requestAnimationFrame(() => {
    weekScrollbarSyncRaf = 0
    syncWeekGridColumns()
  })
}

const goToToday = () => { calendarStore.currentDate = new Date() }

const switchToDayView = (dateStr) => {
  calendarStore.currentDate = new Date(dateStr)
  calendarStore.viewType = 'day'
}

const prevPeriod = () => {
  const c = calendarStore.currentDate
  if (calendarStore.viewType === 'month') {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth() - 1, 1)
  } else if (calendarStore.viewType === 'week') {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth(), c.getDate() - 7)
  } else {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth(), c.getDate() - 1)
  }
}
const nextPeriod = () => {
  const c = calendarStore.currentDate
  if (calendarStore.viewType === 'month') {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth() + 1, 1)
  } else if (calendarStore.viewType === 'week') {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth(), c.getDate() + 7)
  } else {
    calendarStore.currentDate = new Date(c.getFullYear(), c.getMonth(), c.getDate() + 1)
  }
}

const openEventModal = (dateStr, hour = null) => {
  validationMessage.value = ''
  let startTime = ''
  let endTime = ''
  if (hour !== null && typeof hour === 'number') {
    startTime = `${String(hour).padStart(2, '0')}:00`
    endTime = `${String(hour + 1).padStart(2, '0')}:00`
  }
  draftEvent.value = { id: null, title: '', start: dateStr, end: dateStr, startTime, endTime, priority: 3, color: '#34c759', description: '', showInTodo: true }
  isEditing.value = false
  showModal.value = true
}

const editEvent = (event) => {
  validationMessage.value = ''
  draftEvent.value = { 
    ...event, 
    color: event.color || '#007aff',
    priority: event.priority !== undefined ? event.priority : 2,
    startTime: event.startTime || '',
    endTime: event.endTime || '',
    description: event.description || '',
    showInTodo: event.showInTodo !== undefined ? event.showInTodo : (event.isTodo !== false),
  }
  isEditing.value = true
  showModal.value = true
}

const closeModal = () => { showModal.value = false }

const toDateTime = (dateStr, timeStr, fallbackTime) => {
  return new Date(`${dateStr}T${timeStr || fallbackTime}:00`)
}

const saveEvent = async () => {
  validationMessage.value = ''

  if (!draftEvent.value.title.trim()) {
    validationMessage.value = '请输入日程或任务的标题'
    return
  }

  if (!draftEvent.value.start || !draftEvent.value.end) {
    validationMessage.value = '请完整填写开始日期和结束日期'
    return
  }

  if ((draftEvent.value.startTime && !draftEvent.value.endTime) || (!draftEvent.value.startTime && draftEvent.value.endTime)) {
    validationMessage.value = '请同时填写开始时间和结束时间，或都留空'
    return
  }

  if (draftEvent.value.start > draftEvent.value.end) {
    validationMessage.value = '开始日期不能晚于结束日期'
    return
  }

  const startAt = toDateTime(draftEvent.value.start, draftEvent.value.startTime, '00:00')
  const endAt = toDateTime(draftEvent.value.end, draftEvent.value.endTime, '23:59')
  if (Number.isNaN(startAt.getTime()) || Number.isNaN(endAt.getTime())) {
    validationMessage.value = '时间格式无效，请重新输入'
    return
  }

  if (endAt.getTime() < startAt.getTime()) {
    validationMessage.value = '结束时间不能早于开始时间'
    return
  }

  if (isEditing.value) {
    calendarStore.updateEvent(draftEvent.value)
    const existingInBasic = calendarStore.basicEvents.find(e => e.id === draftEvent.value.id)
    if (existingInBasic) {
      try {
        await calendarStore.updateScheduleOnBackend(draftEvent.value.id, draftEvent.value)
      } catch (err) {
        console.error('Failed to sync schedule update to backend:', err)
      }
    }
  } else {
    try {
      // 先创建后端日程，拿到真实 schedule_id
      const result = await calendarStore.createScheduleOnBackend(draftEvent.value)
      const scheduleId = result?.schedule_id || draftEvent.value.id

      // 用真实 ID 创建本地事件和关联 TODO
      calendarStore.addEvent({ ...draftEvent.value, id: scheduleId })

      if (result?.schedule_id) {
        const idx = calendarStore.basicEvents.findIndex(e => e.id === scheduleId)
        if (idx !== -1) {
          calendarStore.basicEvents[idx] = { ...calendarStore.basicEvents[idx], source: 'remote' }
        }
      }
    } catch (err) {
      console.error('Failed to sync new schedule to backend:', err)
      // 后端失败时用本地 ID 兜底
      calendarStore.addEvent(draftEvent.value)
    }
  }
  closeModal()

  await calendarStore.loadSchedules()
  await dashboardStore.loadTodosFromBackend()
}

const deleteEvent = () => {
  validationMessage.value = ''
  if (draftEvent.value.id) {
    calendarStore.removeEvent(draftEvent.value.id)
  }
  closeModal()
}

// Month view drag-and-drop handlers
const onDragStart = (e, event) => {
  draggingEvent.value = event
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', event.id)
  const ghost = e.target.cloneNode(true)
  ghost.style.opacity = '0.5'
  ghost.style.position = 'absolute'
  ghost.style.top = '-1000px'
  document.body.appendChild(ghost)
  e.dataTransfer.setDragImage(ghost, 0, 0)
  setTimeout(() => document.body.removeChild(ghost), 0)
}

const onDragOver = (e, day) => {
  e.preventDefault()
  dragOverCellIndex.value = day.date
}

const onDragEnter = (e, day) => {
  dragOverCellIndex.value = day.date
}

const onDragLeave = () => {
  dragOverCellIndex.value = null
}

const onDrop = async (e, day) => {
  e.preventDefault()
  dragOverCellIndex.value = null
  if (!draggingEvent.value) return

  const event = draggingEvent.value
  const oldStart = new Date(event.start)
  const newStart = new Date(day.date)
  const diffDays = Math.round((newStart - oldStart) / (1000 * 60 * 60 * 24))

  if (diffDays !== 0) {
    const newEnd = new Date(event.end)
    newEnd.setDate(newEnd.getDate() + diffDays)
    const newEndDate = newEnd.toISOString().split('T')[0]

    // Only pass core data properties — NOT view-layer flags (isAllDay, isStart, etc.)
    const updatedData = {
      id: event.id,
      title: event.title,
      start: day.date,
      end: newEndDate,
      // Explicitly preserve the same time period (startTime / endTime unchanged)
      startTime: event.startTime || '',
      endTime: event.endTime || '',
      color: event.color,
      priority: event.priority,
      description: event.description,
      source: event.source,
      isTodo: event.isTodo || false,
      completed: event.completed || false,
      linkedScheduleId: event.linkedScheduleId
    }

    // Standalone todos live in dashboardStore.todos, NOT in basicEvents
    const isStandaloneTodo = event.isTodo && !event.linkedScheduleId
    if (isStandaloneTodo) {
      dashboardStore.updateTodo(updatedData)
    } else {
      calendarStore.updateEvent(updatedData)

      // Sync to backend after drag (was missing — changes were local-only)
      const existingInBasic = calendarStore.basicEvents.find(e => e.id === event.id)
      if (existingInBasic) {
        try {
          await calendarStore.updateScheduleOnBackend(event.id, updatedData)
        } catch (err) {
          console.error('Failed to sync dragged schedule to backend:', err)
        }
      }
    }
  }
  draggingEvent.value = null
}

const onDragEnd = () => {
  dragOverCellIndex.value = null
  draggingEvent.value = null
}

// Week/Day view drag-and-drop handlers
const onTimedDragStart = (e, event) => {
  draggingEvent.value = event
  timedDragOverDate.value = event.start
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', event.id)
}

const onTimedColumnDragOver = (e, day) => {
  e.preventDefault()
  timedDragOverDate.value = day.date
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
}

const minutesToTime = (minutes) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

const onTimedColumnDrop = (e, day) => {
  e.preventDefault()
  if (!draggingEvent.value) {
    timedDragOverDate.value = null
    return
  }

  const columnEl = e.currentTarget.classList.contains('week-day-column')
    ? e.currentTarget
    : e.currentTarget.closest('.week-day-column')
  if (!columnEl) {
    timedDragOverDate.value = null
    draggingEvent.value = null
    return
  }

  const columnRect = columnEl.getBoundingClientRect()
  const event = draggingEvent.value
  applyTimedDrop(event, day.date, columnRect, e.clientY)

  draggingEvent.value = null
  timedDragOverDate.value = null
}

const onTimedDragEnd = () => {
  draggingEvent.value = null
  timedDragOverDate.value = null
}

const onTimedCardClick = (event) => {
  if (suppressNextCardClick.value) {
    suppressNextCardClick.value = false
    return
  }
  editEvent(event)
}

const applyTimedDrop = (event, targetDate, columnRect, clientY) => {
  const relativeY = Math.max(0, Math.min(columnRect.height - 1, clientY - columnRect.top))
  const rawMinutes = Math.round((relativeY / 50) * 60 / 30) * 30
  const startMinutes = Math.max(0, Math.min(23 * 60 + 30, rawMinutes))

  const [sh, sm] = (event.startTime || '00:00').split(':').map(Number)
  const [eh, em] = (event.endTime || '23:59').split(':').map(Number)
  const startBase = Number.isNaN(sh) || Number.isNaN(sm) ? 0 : sh * 60 + sm
  const endBase = Number.isNaN(eh) || Number.isNaN(em) ? 23 * 60 + 59 : eh * 60 + em
  const durationMinutes = Math.max(30, endBase - startBase)

  const safeStartMinutes = Math.min(startMinutes, 23 * 60 + 59)
  const safeEndMinutes = Math.min(23 * 60 + 59, safeStartMinutes + durationMinutes)

  calendarStore.updateEvent({
    ...event,
    start: targetDate,
    end: targetDate,
    startTime: minutesToTime(safeStartMinutes),
    endTime: minutesToTime(safeEndMinutes)
  })
}

const clearManualDragState = () => {
  manualDragEvent.value = null
  manualDragging.value = false
  timedDragOverDate.value = null
  document.removeEventListener('mousemove', onTimedMouseMove)
  document.removeEventListener('mouseup', onTimedMouseUp)
}

const onTimedMouseMove = (e) => {
  if (!manualDragEvent.value) {
    return
  }

  const movedX = Math.abs(e.clientX - manualDragStartX.value)
  const movedY = Math.abs(e.clientY - manualDragStartY.value)

  if (!manualDragging.value && movedX < 4 && movedY < 4) {
    return
  }

  manualDragging.value = true
  const target = document.elementFromPoint(e.clientX, e.clientY)
  const column = target?.closest('.week-day-column')
  timedDragOverDate.value = column?.dataset?.date || null
}

const onTimedMouseUp = (e) => {
  if (!manualDragEvent.value) {
    clearManualDragState()
    return
  }

  if (manualDragging.value) {
    const target = document.elementFromPoint(e.clientX, e.clientY)
    const column = target?.closest('.week-day-column')
    const targetDate = column?.dataset?.date
    if (column && targetDate) {
      applyTimedDrop(manualDragEvent.value, targetDate, column.getBoundingClientRect(), e.clientY)
      suppressNextCardClick.value = true
    }
  }

  clearManualDragState()
}

const onTimedMouseDragStart = (e, event) => {
  if (e.button !== 0) {
    return
  }

  if (e.target.closest('.resize-handle')) {
    return
  }

  manualDragEvent.value = event
  manualDragging.value = false
  manualDragStartX.value = e.clientX
  manualDragStartY.value = e.clientY
  document.addEventListener('mousemove', onTimedMouseMove)
  document.addEventListener('mouseup', onTimedMouseUp)
}

// Resize handler for week/day view
const onResizeStart = (e, event) => {
  e.preventDefault()
  e.stopPropagation()
  isResizing.value = true
  resizeStartY.value = e.clientY
  resizeOriginalEnd.value = event.endTime || '23:59'
  resizeEvent.value = event

  const onMouseMove = (e) => {
    if (!isResizing.value || !resizeEvent.value) return
    const deltaY = e.clientY - resizeStartY.value
    const deltaMinutes = Math.round(deltaY / 50 * 60 / 30) * 30

    const [eh, em] = resizeOriginalEnd.value.split(':').map(Number)
    const totalMinutes = eh * 60 + em + deltaMinutes
    const clampedMinutes = Math.max(0, Math.min(23 * 60 + 59, totalMinutes))
    const newHour = Math.floor(clampedMinutes / 60)
    const newMin = clampedMinutes % 60
    const newEndTime = `${String(newHour).padStart(2, '0')}:${String(newMin).padStart(2, '0')}`

    calendarStore.updateEvent({
      ...resizeEvent.value,
      endTime: newEndTime
    })
  }

  const onMouseUp = () => {
    isResizing.value = false
    resizeEvent.value = null
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

watch(
  () => [calendarStore.viewType, visibleDays.value.length],
  async () => {
    await nextTick()
    scheduleWeekGridSync()
  }
)

onMounted(async () => {
  await nextTick()
  scheduleWeekGridSync()
  window.addEventListener('resize', scheduleWeekGridSync)
  await calendarStore.loadSchedules()
  await dashboardStore.loadTodosFromBackend()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', scheduleWeekGridSync)
  if (weekScrollbarSyncRaf) {
    window.cancelAnimationFrame(weekScrollbarSyncRaf)
    weekScrollbarSyncRaf = 0
  }
})

</script>

<style scoped>
.priority-options { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.priority-chip {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.priority-chip:hover { opacity: 0.8; }
.color-picker-row { margin-bottom: 12px; }
.color-picker-row label { font-size: 12px; color: #555; }

.form-validation-message {
  margin: 8px 0 0;
  font-size: 12px;
  color: #ff3b30;
}

.calendar-wrapper {
  background: var(--clr-bg-app, #ffffff);
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.calendar-toolbar {
  height: 56px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #ffffff;
  flex-shrink: 0;
}

.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 12px; flex: 1; }
.toolbar-right { justify-content: flex-end; }
.toolbar-center { flex: 1; text-align: center; }

.current-date { font-size: 16px; font-weight: 600; margin: 0; color: #1d1d1f;}

.mac-btn {
  background: #ffffff; border: 1px solid rgba(0, 0, 0, 0.1); border-radius: 6px;
  padding: 4px 12px; font-size: 13px; font-weight: 500; cursor: pointer; color: #1d1d1f;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}
.mac-btn:hover { background: var(--clr-bg-content, #f5f5f7); }
.mac-btn.primary { background: #007aff; color: white; border-color: #007aff; }
.mac-btn.primary:hover { background: #0062cc; }

.nav-arrows { display: flex; gap: 4px; }
.icon-btn {
  background: transparent; border: none; border-radius: 6px; padding: 4px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; color: #86868b;
}
.icon-btn:hover { background: rgba(0, 0, 0, 0.05); }

.refresh-btn { transition: transform 0.3s ease; }
.refresh-btn.spinning svg { animation: spin 0.8s linear infinite; }
.import-btn { margin-right: 4px; }
.import-bb-btn { margin-right: 4px; }
.import-btn.spinning svg, .import-bb-btn.spinning svg { animation: spin 0.8s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.segmented-control { display: flex; background: rgba(0, 0, 0, 0.05); padding: 2px; border-radius: 8px; }
.segment {
  background: transparent; border: none; padding: 4px 12px; font-size: 13px;
  font-weight: 500; border-radius: 6px; cursor: pointer; color: #1d1d1f;
}
.segment.active { background: var(--clr-bg-card, #ffffff); box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }

.calendar-grid-container { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.mock-calendar-body { flex: 1; display: flex; flex-direction: column; }
.placeholder-view { align-items: center; justify-content: center; color: #86868b; display: flex;}

.weekdays-header {
  display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  text-align: right; padding: 8px 8px 4px 8px; font-size: 12px; font-weight: 600; color: #86868b;
}
.days-grid { flex: 1; display: grid; grid-template-columns: repeat(7, 1fr); grid-template-rows: repeat(6, 100px); background: #fafafa; align-content: start;}

.day-cell {
  border-right: 1px solid rgba(0, 0, 0, 0.04); border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding: 4px; text-align: right; display: flex; flex-direction: column; cursor: pointer;
  background: var(--clr-bg-card, #ffffff);
  height: 100px;
  min-height: 100px;
  max-height: 100px;
  overflow: hidden;
}
.day-cell.is-other-month { background: #fafafa; opacity: 0.6; }
.day-cell.is-today { background: rgba(0, 122, 255, 0.03); }

.date-num {
  font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; justify-content: center;
  width: 20px; height: 20px; border-radius: 50%; margin-bottom: 2px; align-self: flex-end; color: #1d1d1f;
}
.date-num.is-today-text { background: #007aff; color: white; }

.events-container { flex: 1; display: flex; flex-direction: column; gap: 2px; overflow: hidden; pointer-events: none;}
.event-bar {
  font-size: 10px; padding: 2px 4px; border-radius: 4px; cursor: pointer; pointer-events: auto;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left;
  background: rgba(0, 122, 255, 0.15); color: #005bb5; height: 18px; line-height: 14px;
  position: relative;
}
.event-bar.is-todo { background: rgba(52, 199, 89, 0.15); color: #248a3d; }
.event-bar.is-completed { text-decoration: line-through; opacity: 0.5; }
.event-bar:hover { filter: brightness(0.9); }

.more-events {
  font-size: 10px;
  color: #86868b;
  text-align: center;
  cursor: pointer;
  padding: 2px 0;
  pointer-events: auto;
}
.more-events:hover {
  color: #007aff;
  text-decoration: underline;
}

/* 跨天条块 */
.event-bar.multi-start { border-top-right-radius: 0; border-bottom-right-radius: 0; margin-right: -4px; width: calc(100% + 4px); z-index: 1;}
.event-bar.multi-mid { border-radius: 0; margin-left: -4px; margin-right: -4px; width: calc(100% + 8px); padding-left: 8px; z-index: 1;}
.event-bar.multi-end { border-top-left-radius: 0; border-bottom-left-radius: 0; margin-left: -4px; width: calc(100% + 4px); padding-left: 8px; z-index: 1; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100;}
.mac-modal { background: #fff; width: 320px; border-radius: 12px; padding: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
.mac-modal h3 { margin-top: 0; margin-bottom: 16px; font-size: 16px; color: #1d1d1f; }
.mac-modal label { display: block; font-size: 12px; color: #555; margin-bottom: 4px; }
.mac-input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin-bottom: 12px; font-size: 13px; height: 35px; }
.time-picker-row { display: flex; align-items: center; gap: 4px; margin-bottom: 12px; }
.time-select { flex: 1; margin-bottom: 0; }
.time-sep { font-weight: 600; color: #1d1d1f; }
.date-row { display: flex; gap: 12px; }
.date-row > div { flex: 1; }
.checkbox-row { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #1d1d1f; font-size: 12px; }
.modal-actions { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.delete-btn-modal { color: #ff3b30; border-color: transparent; padding: 4px 0;}
.delete-btn-modal:hover { background: rgba(255,59,48,0.1); border-color: rgba(255,59,48,0.2); }

/* Week and Day Timeline View */
.week-timeline-body { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--clr-bg-card, #ffffff);}
.week-timeline-header { display: flex; border-bottom: 1px solid rgba(0,0,0,0.08); background: #fafafa; padding-top: 8px; padding-right: var(--week-scrollbar-offset, 0px); overflow-y: scroll; scrollbar-gutter: stable; scrollbar-width: none; }
.week-timeline-header::-webkit-scrollbar { display: none; }
.time-axis-placeholder { width: 50px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-right: 1px solid rgba(0,0,0,0.08); }
.week-timeline-day-header { flex: 1; text-align: center; padding: 4px 0 8px; border-right: 1px solid rgba(0,0,0,0.04); cursor: pointer; }
.week-timeline-day-header:last-child { border-right: none; }
.day-name { display: block; font-size: 11px; color: #86868b; text-transform: uppercase; font-weight: 500; margin-bottom: 4px; }
.day-num { display: inline-block; font-size: 18px; font-weight: 400; width: 32px; height: 32px; line-height: 32px; border-radius: 50%; color: #1d1d1f; }
.is-today-text .day-name { color: #007aff; }
.day-num.is-today-bg { background: #007aff; color: white; font-weight: 500; }

.week-all-day-row { display: flex; border-bottom: 1px solid rgba(0,0,0,0.08); height: 80px; min-height: 80px; overflow: hidden; background: var(--clr-bg-card, #ffffff); padding-right: var(--week-scrollbar-offset, 0px); overflow-y: scroll; scrollbar-gutter: stable; scrollbar-width: none; }
.week-all-day-row::-webkit-scrollbar { display: none; }
.week-all-day-row.day-layout { height: auto; min-height: 40px; overflow: visible; }
.all-day-label { font-size: 11px; color: #86868b; font-weight: 500; }
.week-all-day-cell { flex: 1; border-right: 1px solid rgba(0,0,0,0.04); padding: 4px; display: flex; flex-direction: column; gap: 2px; cursor: pointer; overflow: hidden; }
.week-all-day-cell:last-child { border-right: none; }

.week-timeline-scroll { flex: 1; overflow-y: auto; position: relative; scrollbar-gutter: stable; }
.week-timeline-grid { display: flex; min-height: 1200px; }
.time-axis { width: 50px; flex-shrink: 0; border-right: 1px solid rgba(0,0,0,0.08); background: var(--clr-bg-card, #ffffff); position: relative; padding-top: 16px;}
.time-slot { height: 50px; position: relative; }
.time-slot span { position: absolute; top: -7px; right: 8px; font-size: 10px; color: #86868b; background: #fff; padding-left: 4px;}
.time-separator { position: absolute; right: 0; top: 0; width: 4px; height: 1px; background: rgba(0,0,0,0.08); }
.week-day-columns { flex: 1; display: flex; background: var(--clr-bg-card, #ffffff);}
.week-day-column { flex: 1; display: flex; flex-direction: column; border-right: 1px solid rgba(0,0,0,0.04); position: relative; }
.week-day-column:last-child { border-right: none; }
.is-today-col { background: rgba(0, 122, 255, 0.02); }
.hour-slot { height: 50px; border-bottom: 1px solid rgba(0,0,0,0.04); box-sizing: border-box; cursor: text; }
.hour-slot:hover { background: rgba(0,0,0,0.02); }

.timed-event-card {
  position: absolute;
  left: 2px;
  right: 6px;
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 11px;
  overflow: hidden;
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: filter 0.15s;
}
.timed-event-card:hover { filter: brightness(0.95); z-index: 15; }
.timed-event-title { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }
.timed-event-time { font-size: 9px; opacity: 0.8; }
.timed-event-card.is-completed { opacity: 0.6; }
.timed-event-card.is-completed .timed-event-title { text-decoration: line-through; }

/* Drag-over states */
.day-cell.drag-over {
  background: rgba(0, 122, 255, 0.08) !important;
  box-shadow: inset 0 0 0 2px rgba(0, 122, 255, 0.3);
}
.day-cell.drag-over .date-num {
  background: #007aff;
  color: white;
}

.week-day-column.drag-over-col {
  background: rgba(0, 122, 255, 0.04);
}

/* Resize handle */
.resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 6px;
  cursor: ns-resize;
  z-index: 20;
}
.resize-handle:hover {
  background: rgba(0, 122, 255, 0.3);
  border-radius: 0 0 4px 4px;
}

.import-toast {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  margin: 8px 0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}
.import-toast.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}
.import-toast.success {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}
.toast-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  padding: 0 4px;
}
.toast-close:hover {
  opacity: 1;
}
</style>
