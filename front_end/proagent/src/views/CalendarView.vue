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
        <div class="segmented-control">
          <button class="segment" :class="{ active: viewType === 'day' }" @click="viewType = 'day'">日</button>
          <button class="segment" :class="{ active: viewType === 'week' }" @click="viewType = 'week'">周</button>
          <button class="segment" :class="{ active: viewType === 'month' }" @click="viewType = 'month'">月</button>
        </div>
      </div>
    </div>

    <div class="calendar-grid-container" v-if="viewType === 'month'">
      <div class="mock-calendar-body">
        <div class="weekdays-header">
          <span v-for="w in weekdays" :key="w">{{ w }}</span>
        </div>
        <div class="days-grid">
          <div 
            v-for="(day, index) in calendarDays" 
            :key="index" 
            class="day-cell"
            :class="{ 'is-other-month': !day.isCurrentMonth, 'is-today': day.isToday }"
            @click.self="openEventModal(day.date)"
          >
            <span class="date-num" :class="{ 'is-today-text': day.isToday }" @click.stop="openEventModal(day.date)">{{ day.dayNum }}</span>
            <div class="events-container" @click.self="openEventModal(day.date)">
              <div 
                v-for="event in day.events" 
                :key="event.id"
                class="event-bar"
                :class="{'is-todo': event.isTodo, 'is-completed': event.completed, 'multi-start': event.isStart, 'multi-mid': event.isMid, 'multi-end': event.isEnd}"
                :style="{ backgroundColor: event.color ? event.color + '25' : '', color: event.color || '' }"
                @click.stop="editEvent(event)"
                :title="event.title"
              >
                {{ event.isStart || day.date === event.start ? event.title : '\u00A0' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="calendar-grid-container" v-else>
      <div class="week-timeline-body">
        <div class="week-timeline-header">
          <div class="time-axis-placeholder"></div>
          <div 
            v-for="(day, i) in visibleDays" 
            :key="'wh'+i" 
            class="week-timeline-day-header"
            :class="{ 'is-today-text': day.isToday }"
            @click="openEventModal(day.date)"
          >
            <span class="day-name">{{ weekdays[viewType === 'week' ? i : currentDate.getDay()] }}</span>
            <span class="day-num" :class="{ 'is-today-bg': day.isToday }">{{ day.dayNum }}</span>
          </div>
        </div>
        <div class="week-all-day-row">
          <div class="time-axis-placeholder"><span class="all-day-label">全天</span></div>
          <div 
            v-for="(day, i) in visibleDays" 
            :key="'wa'+i" 
            class="week-all-day-cell"
            :class="{ 'is-today-col': day.isToday }"
            @click.self="openEventModal(day.date)"
          >
            <div 
              v-for="event in day.allDayEvents" 
              :key="event.id"
              class="event-bar"
              :class="{'is-todo': event.isTodo, 'is-completed': event.completed}"
              :style="{ backgroundColor: event.color ? event.color + '25' : '', color: event.color || '' }"
              @click.stop="editEvent(event)"
              :title="event.title"
            >
              {{ event.title }}
            </div>
          </div>
        </div>
        <div class="week-timeline-scroll">
          <div class="week-timeline-grid" :class="{'day-layout': viewType === 'day'}">
            <div class="time-axis">
              <div class="time-slot" v-for="h in hours" :key="'t'+h">
                <span>{{ h === 0 ? '12 AM' : (h < 12 ? h + ' AM' : (h === 12 ? '12 PM' : (h - 12) + ' PM')) }}</span>
                <div class="time-separator"></div>
              </div>
            </div>
            <div class="week-day-columns" :class="{'day-layout': viewType === 'day'}">
              <div 
                v-for="(day, i) in visibleDays" 
                :key="'wc'+i" 
                class="week-day-column"
                :class="{ 'is-today-col': day.isToday }"
                @click.self="openEventModal(day.date)"
              >
                <div class="hour-slot" v-for="h in hours" :key="'ts'+h" @click.self="openEventModal(day.date, h)"></div>
                
                <div
                  v-for="event in day.timedEvents"
                  :key="event.id"
                  class="timed-event-card"
                  :class="{'is-completed': event.completed}"
                  :style="getTimedEventStyle(event)"
                  @click.stop="editEvent(event)"
                >
                  <div class="timed-event-title">{{ event.title }}</div>
                  <div class="timed-event-time">{{ event.startTime }} - {{ event.endTime || '23:59' }}</div>
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
            <label>时间 (可选)</label>
            <input type="time" v-model="draftEvent.startTime" class="mac-input" />
          </div>
        </div>
        <div class="date-row">
          <div>
            <label>结束日期</label>
            <input type="date" v-model="draftEvent.end" class="mac-input" />
          </div>
          <div>
            <label>时间 (可选)</label>
            <input type="time" v-model="draftEvent.endTime" class="mac-input" />
          </div>
        </div>
        <div class="color-picker-row">
          <label>标签颜色</label>
          <div class="color-options">
            <span v-for="c in colorOptions" :key="c" class="color-dot" :style="{ backgroundColor: c }" :class="{ active: draftEvent.color === c }" @click="draftEvent.color = c"></span>
          </div>
        </div>
        <label class="checkbox-row" style="margin-top: 10px;">
          <input type="checkbox" v-model="draftEvent.isTodo" />
          同步到主界面 TODO list
        </label>
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
import { ref, computed } from 'vue'
import { useCalendarStore } from '../stores/calendar.js'

const calendarStore = useCalendarStore()

const currentDate = ref(new Date())
const viewType = ref('month')
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const showModal = ref(false)
const isEditing = ref(false)
const draftEvent = ref({ id: null, title: '', start: '', end: '', startTime: '', endTime: '', isTodo: true, color: '#34c759' })
const colorOptions = ['#007aff', '#ff3b30', '#ff9500', '#34c759', '#af52de']

const headerTitle = computed(() => {
  const y = currentDate.value.getFullYear()
  const m = currentDate.value.getMonth() + 1
  const d = currentDate.value.getDate()
  if (viewType.value === 'month') {
    return `${y}年 ${m}月`
  } else if (viewType.value === 'week') {
    const sun = new Date(currentDate.value)
    sun.setDate(d - sun.getDay())
    const sat = new Date(sun)
    sat.setDate(sat.getDate() + 6)
    return `${sun.getFullYear()}年 ${sun.getMonth() + 1}月 ${sun.getDate()}日 - ${sat.getMonth() + 1}月 ${sat.getDate()}日`
  }
  return `${y}年 ${m}月 ${d}日 ${weekdays[currentDate.value.getDay()]}`
})

const daysInMonth = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
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
    }).map(e => ({
        ...e,
        isAllDay: e.start !== e.end || !e.startTime,
        isStart: isoDate === e.start,
        isEnd: isoDate === e.end,
        isMid: isoDate > e.start && isoDate < e.end
    })).sort((a,b) => a.id - b.id)
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
    color: event.color || '',
    borderLeft: `3px solid ${event.color || '#007aff'}`
  }
}

const calendarDays = computed(() => daysInMonth.value)

const weekDays = computed(() => {
  const current = currentDate.value
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
  return [createDayObject(currentDate.value, true)]
})

const visibleDays = computed(() => {
  return viewType.value === 'week' ? weekDays.value : singleDay.value
})

const hours = Array.from({ length: 24 }, (_, i) => i)

const goToToday = () => { currentDate.value = new Date() }

const prevPeriod = () => {
  const c = currentDate.value
  if (viewType.value === 'month') {
    currentDate.value = new Date(c.getFullYear(), c.getMonth() - 1, 1)
  } else if (viewType.value === 'week') {
    currentDate.value = new Date(c.getFullYear(), c.getMonth(), c.getDate() - 7)
  } else {
    currentDate.value = new Date(c.getFullYear(), c.getMonth(), c.getDate() - 1)
  }
}
const nextPeriod = () => {
  const c = currentDate.value
  if (viewType.value === 'month') {
    currentDate.value = new Date(c.getFullYear(), c.getMonth() + 1, 1)
  } else if (viewType.value === 'week') {
    currentDate.value = new Date(c.getFullYear(), c.getMonth(), c.getDate() + 7)
  } else {
    currentDate.value = new Date(c.getFullYear(), c.getMonth(), c.getDate() + 1)
  }
}

const openEventModal = (dateStr, hour = null) => {
  let startTime = ''
  let endTime = ''
  if (hour !== null && typeof hour === 'number') {
    startTime = `${String(hour).padStart(2, '0')}:00`
    endTime = `${String(hour + 1).padStart(2, '0')}:00`
  }
  draftEvent.value = { id: null, title: '', start: dateStr, end: dateStr, startTime, endTime, isTodo: false, color: '#007aff' }
  isEditing.value = false
  showModal.value = true
}

const editEvent = (event) => {
  draftEvent.value = { 
    ...event, 
    color: event.color || (event.isTodo ? '#34c759' : '#007aff'),
    startTime: event.startTime || '',
    endTime: event.endTime || ''
  }
  isEditing.value = true
  showModal.value = true
}

const closeModal = () => { showModal.value = false }

const saveEvent = () => {
  if (!draftEvent.value.title) return
  if (isEditing.value) {
    calendarStore.updateEvent(draftEvent.value)
  } else {
    calendarStore.addEvent(draftEvent.value)
  }
  closeModal()
}

const deleteEvent = () => {
  if (draftEvent.value.id) {
    calendarStore.removeEvent(draftEvent.value.id)
  }
  closeModal()
}

</script>

<style scoped>
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
  background: var(--clr-bg-topbar, #fafafa);
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
.mac-btn:hover { background: #f5f5f7; }
.mac-btn.primary { background: #007aff; color: white; border-color: #007aff; }
.mac-btn.primary:hover { background: #0062cc; }

.nav-arrows { display: flex; gap: 4px; }
.icon-btn {
  background: transparent; border: none; border-radius: 6px; padding: 4px;
  cursor: pointer; display: flex; align-items: center; justify-content: center; color: #86868b;
}
.icon-btn:hover { background: rgba(0, 0, 0, 0.05); }

.segmented-control { display: flex; background: rgba(0, 0, 0, 0.05); padding: 2px; border-radius: 8px; }
.segment {
  background: transparent; border: none; padding: 4px 12px; font-size: 13px;
  font-weight: 500; border-radius: 6px; cursor: pointer; color: #1d1d1f;
}
.segment.active { background: #ffffff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }

.calendar-grid-container { flex: 1; display: flex; flex-direction: column; min-height: 0; }
.mock-calendar-body { flex: 1; display: flex; flex-direction: column; }
.placeholder-view { align-items: center; justify-content: center; color: #86868b; display: flex;}

.weekdays-header {
  display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  text-align: right; padding: 8px 8px 4px 8px; font-size: 12px; font-weight: 600; color: #86868b;
}
.days-grid { flex: 1; display: grid; grid-template-columns: repeat(7, 1fr); grid-auto-rows: 1fr; background: #fafafa;}

.day-cell {
  border-right: 1px solid rgba(0, 0, 0, 0.04); border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding: 4px; text-align: right; display: flex; flex-direction: column; cursor: pointer;
  background: #ffffff; 
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

/* 跨天条块 */
.event-bar.multi-start { border-top-right-radius: 0; border-bottom-right-radius: 0; margin-right: -4px; width: calc(100% + 4px); z-index: 1;}
.event-bar.multi-mid { border-radius: 0; margin-left: -4px; margin-right: -4px; width: calc(100% + 8px); padding-left: 8px; z-index: 1;}
.event-bar.multi-end { border-top-left-radius: 0; border-bottom-left-radius: 0; margin-left: -4px; width: calc(100% + 4px); padding-left: 8px; z-index: 1; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100;}
.mac-modal { background: #fff; width: 320px; border-radius: 12px; padding: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
.mac-modal h3 { margin-top: 0; margin-bottom: 16px; font-size: 16px; color: #1d1d1f; }
.mac-modal label { display: block; font-size: 12px; color: #555; margin-bottom: 4px; }
.mac-input { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; margin-bottom: 12px; font-size: 13px;}
.date-row { display: flex; gap: 12px; }
.date-row > div { flex: 1; }
.checkbox-row { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #1d1d1f; font-size: 12px; }
.modal-actions { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.delete-btn-modal { color: #ff3b30; border-color: transparent; padding: 4px 0;}
.delete-btn-modal:hover { background: rgba(255,59,48,0.1); border-color: rgba(255,59,48,0.2); }

/* Week and Day Timeline View */
.week-timeline-body { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #ffffff;}
.week-timeline-header { display: flex; border-bottom: 1px solid rgba(0,0,0,0.08); background: #fafafa; padding-top: 8px; }
.time-axis-placeholder { width: 50px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-right: 1px solid rgba(0,0,0,0.08); }
.week-timeline-day-header { flex: 1; text-align: center; padding: 4px 0 8px; border-right: 1px solid rgba(0,0,0,0.04); cursor: pointer; }
.week-timeline-day-header:last-child { border-right: none; }
.day-name { display: block; font-size: 11px; color: #86868b; text-transform: uppercase; font-weight: 500; margin-bottom: 4px; }
.day-num { display: inline-block; font-size: 18px; font-weight: 400; width: 32px; height: 32px; line-height: 32px; border-radius: 50%; color: #1d1d1f; }
.is-today-text .day-name { color: #007aff; }
.day-num.is-today-bg { background: #007aff; color: white; font-weight: 500; }

.week-all-day-row { display: flex; border-bottom: 1px solid rgba(0,0,0,0.08); min-height: 40px; background: #ffffff; }
.all-day-label { font-size: 11px; color: #86868b; font-weight: 500; }
.week-all-day-cell { flex: 1; border-right: 1px solid rgba(0,0,0,0.04); padding: 4px; display: flex; flex-direction: column; gap: 2px; cursor: pointer; }
.week-all-day-cell:last-child { border-right: none; }

.week-timeline-scroll { flex: 1; overflow-y: auto; position: relative; }
.week-timeline-grid { display: flex; min-height: 1200px; }
.time-axis { width: 50px; flex-shrink: 0; border-right: 1px solid rgba(0,0,0,0.08); background: #ffffff; position: relative;}
.time-slot { height: 50px; position: relative; }
.time-slot span { position: absolute; top: -7px; right: 8px; font-size: 10px; color: #86868b; background: #fff; padding-left: 4px;}
.time-separator { position: absolute; right: 0; top: 0; width: 4px; height: 1px; background: rgba(0,0,0,0.08); }
.week-day-columns { flex: 1; display: flex; background: #ffffff;}
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
</style>
