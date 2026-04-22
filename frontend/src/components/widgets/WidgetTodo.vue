<template>
  <div class="widget-container">
    <div class="panel-header">
      <h3 class="panel-title">TODO List</h3>
      <span class="task-count">{{ store.pendingTodosCount }} pending</span>
    </div>
    <div class="panel-body">
      <div class="todo-input-group">
        <input 
          v-model="newTaskTitle" 
          @keyup.enter="prepareAddTask" 
          type="text" 
          placeholder="添加新任务... (回车选择时间)" 
          class="mac-input" 
        />
      </div>

      <div v-if="showDatePicker" class="todo-date-picker">
        <div class="date-row">
          <div>
          <label>开始时间: </label>
          <input type="date" v-model="newTaskStart" class="mac-input mini" />
          <div class="time-picker-row">
            <select v-model="newTaskStartHour" class="mac-input mini time-select">
              <option value="">--</option>
              <option v-for="h in hours24" :key="h" :value="h">{{ h }}</option>
            </select>
            <span class="time-sep">:</span>
            <select v-model="newTaskStartMinute" class="mac-input mini time-select">
              <option value="">--</option>
              <option v-for="m in minutes60" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
        </div>
        <div>
          <label>结束时间: </label>
          <input type="date" v-model="newTaskEnd" class="mac-input mini" />
          <div class="time-picker-row">
            <select v-model="newTaskEndHour" class="mac-input mini time-select">
              <option value="">--</option>
              <option v-for="h in hours24" :key="h" :value="h">{{ h }}</option>
            </select>
            <span class="time-sep">:</span>
            <select v-model="newTaskEndMinute" class="mac-input mini time-select">
              <option value="">--</option>
              <option v-for="m in minutes60" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
        </div>
        </div>
        <div class="color-picker-row">
          <label>优先级(分色): </label>
          <div class="priority-options">
            <div 
              v-for="p in priorityOptions" 
              :key="p.level" 
              class="priority-chip"
              :class="{ active: newTaskPriority === p.level }"
              :style="{ backgroundColor: p.color + (newTaskPriority === p.level ? '' : '15'), color: newTaskPriority === p.level ? '#fff' : p.color, borderColor: p.color }"
              @click="setPriority(p)"
            >
              P{{ p.level }}
            </div>
          </div>
        </div>
        <div class="date-actions">
          <button class="mac-btn secondary" @click="showDatePicker = false">取消</button>
          <button class="mac-btn primary" @click="confirmAddTask">确定</button>
        </div>
      </div>

      <ul class="todo-list">
        <li v-for="task in store.sortedTodos" :key="task.id" class="todo-item" :class="{ 'is-completed': task.completed, 'is-expanded': expandedId === task.id }">
          <div class="todo-row">
            <input 
              type="checkbox" 
              :checked="task.completed" 
              @change="store.toggleTodo(task.id)" 
              class="mac-checkbox" 
            />
            <div class="task-priority-indicator" :style="{ backgroundColor: task.color || '#007aff' }">P{{ task.priority !== undefined ? task.priority : 2 }}</div>
            <span class="task-text" style="flex: 1" @click="toggleExpand(task.id)">{{ task.title }}</span>
            <button @click.stop="deleteTodo(task)" class="delete-btn">×</button>
          </div>
          <div v-if="expandedId === task.id" class="task-detail" @click.stop>
            <div class="detail-row">
              <span class="detail-label">优先级</span>
              <span class="detail-value" :style="{ color: task.color || '#007aff' }">{{ priorityLabel(task.priority) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">开始</span>
              <span class="detail-value">{{ formatDate(task.start) }}{{ task.startTime ? ' ' + task.startTime : '' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">结束</span>
              <span class="detail-value">{{ formatDate(task.end || task.start) }}{{ task.endTime ? ' ' + task.endTime : '' }}</span>
            </div>
            <div class="detail-row" v-if="task.description">
              <span class="detail-label">备注</span>
              <span class="detail-value">{{ task.description }}</span>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDashboardStore } from '../../stores/dashboard'
import { useCalendarStore } from '../../stores/calendar'

const store = useDashboardStore()
const calendarStore = useCalendarStore()
const newTaskTitle = ref('')
const expandedId = ref(null)

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return dateStr
}

const priorityLabel = (p) => {
  const labels = { 0: 'P0 紧急且重要', 1: 'P1 重要不紧急', 2: 'P2 紧急不重要', 3: 'P3 不重要不紧急' }
  return labels[p ?? 2] || 'P2 紧急不重要'
}

const showDatePicker = ref(false)
const newTaskStart = ref('')
const newTaskEnd = ref('')
const newTaskStartTime = ref('')
const newTaskEndTime = ref('')
const newTaskPriority = ref(2)
const newTaskColor = ref('#007aff')

const hours24 = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const minutes60 = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))

const newTaskStartHour = computed({
  get: () => (newTaskStartTime.value || '').split(':')[0] || '',
  set: (v) => { const m = (newTaskStartTime.value || '').split(':')[1] || '00'; newTaskStartTime.value = v ? `${v}:${m}` : '' }
})
const newTaskStartMinute = computed({
  get: () => { const p = (newTaskStartTime.value || '').split(':'); return p[1] || '' },
  set: (v) => { const h = (newTaskStartTime.value || '').split(':')[0] || '00'; newTaskStartTime.value = v !== '' ? `${h}:${v}` : '' }
})
const newTaskEndHour = computed({
  get: () => (newTaskEndTime.value || '').split(':')[0] || '',
  set: (v) => { const m = (newTaskEndTime.value || '').split(':')[1] || '00'; newTaskEndTime.value = v ? `${v}:${m}` : '' }
})
const newTaskEndMinute = computed({
  get: () => { const p = (newTaskEndTime.value || '').split(':'); return p[1] || '' },
  set: (v) => { const h = (newTaskEndTime.value || '').split(':')[0] || '00'; newTaskEndTime.value = v !== '' ? `${h}:${v}` : '' }
})

const deleteTodo = (task) => {
  const linkedId = Number(task.linkedScheduleId)
  if (Number.isFinite(linkedId) && linkedId > 0) {
    calendarStore.removeEvent(linkedId)
  } else {
    store.removeTodo(task.id)
  }
}



const priorityOptions = [
  { level: 0, color: '#ff3b30', label: '紧急且重要' },
  { level: 1, color: '#ff9500', label: '重要不紧急' },
  { level: 2, color: '#007aff', label: '紧急不重要' },
  { level: 3, color: '#34c759', label: '不重要不紧急' }
]

const setPriority = (p) => {
  newTaskPriority.value = p.level
  newTaskColor.value = p.color
}

const prepareAddTask = () => {
  if (!newTaskTitle.value.trim()) {
    alert('请输入新任务的名称')
    return
  }
  const today = new Date().toISOString().split('T')[0]
  newTaskStart.value = today
  newTaskEnd.value = today
  newTaskStartTime.value = ''
  newTaskEndTime.value = ''
  newTaskPriority.value = 2
  newTaskColor.value = '#007aff'
  showDatePicker.value = true
}

const confirmAddTask = () => {
  if (!newTaskTitle.value.trim()) {
    alert('请输入新任务的名称')
    return
  }

  if (newTaskStart.value > newTaskEnd.value) {
    alert('开始日期不能晚于结束日期')
    return
  }
  if (newTaskStart.value === newTaskEnd.value && newTaskStartTime.value && newTaskEndTime.value) {
    if (newTaskStartTime.value > newTaskEndTime.value) {
      alert('开始时间不能晚于结束时间')
      return
    }
  }

  store.addTodo({
    title: newTaskTitle.value.trim(),
    start: newTaskStart.value,
    end: newTaskEnd.value,
    startTime: newTaskStartTime.value,
    endTime: newTaskEndTime.value,
    priority: newTaskPriority.value,
    color: newTaskColor.value
  })
  newTaskTitle.value = ''
  showDatePicker.value = false
}
</script>

<style scoped>
.widget-container { display: flex; flex-direction: column; height: 100%; width: 100%; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.panel-title { font-size: 13px; font-weight: 600; margin: 0; color: #1d1d1f; }
.task-count { font-size: 11px; color: #86868b; }
.panel-body { flex: 1; padding: 12px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }

.mac-input { 
  width: 100%; 
  padding: 8px 12px; 
  border: 1px solid rgba(0,0,0,0.15); 
  border-radius: 8px; 
  font-size: 13px; 
  outline: none; 
  box-sizing: border-box; 
  transition: border-color 0.2s;
}
.mac-input:focus { border-color: #007aff; box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2); }
.mac-input.mini { padding: 4px 8px; font-size: 11px; margin-top: 4px; }
.time-picker-row { display: flex; align-items: center; gap: 4px; margin-top: 4px; }
.time-select { flex: 1; }
.time-sep { font-weight: 600; color: #1d1d1f; }

.todo-date-picker {
  background: #fdfdfd;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.date-row { display: flex; gap: 8px; }
.date-row div { flex: 1; font-size: 11px; color: #555; }
.date-row label { font-weight: 500; }
.color-picker-row { display: flex; align-items: flex-start; gap: 8px; font-size: 11px; color: #555; }
.color-picker-row label { font-weight: 500; margin-top: 4px; }
.priority-options { display: flex; gap: 8px; flex-wrap: wrap; }
.priority-chip {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}
.priority-chip:hover { opacity: 0.8; }
.date-actions { display: flex; justify-content: flex-end; gap: 8px; }
.mac-btn {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(0,0,0,0.1);
  background: #fff;
}
.mac-btn.secondary { color: #555; }
.mac-btn.primary { background: #007aff; color: #fff; border-color: #007aff; }
.mac-btn.primary:hover { background: #0062cc; }

.todo-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.todo-item { font-size: 13px; padding: 4px 6px; border-radius: 6px; }
.todo-item:hover { background: rgba(0,0,0,0.02); }
.todo-item.is-expanded { background: rgba(0,0,0,0.03); }
.todo-item.is-completed .task-text { text-decoration: line-through; color: #86868b; }

.todo-row { display: flex; align-items: center; gap: 8px; }

.task-priority-indicator {
  padding: 2px 4px;
  border-radius: 4px;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  min-width: 14px;
  text-align: center;
  flex-shrink: 0;
}
.task-text { flex: 1; color: #1d1d1f; cursor: pointer; }
.task-text:hover { color: #007aff; }

.task-detail {
  padding: 6px 8px 6px 30px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: #86868b;
}
.detail-row { display: flex; gap: 6px; }
.detail-label { min-width: 28px; font-weight: 500; }
.detail-value { color: #555; word-break: break-word; }

.mac-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #007aff;
  cursor: pointer;
  flex-shrink: 0;
}

.delete-btn { 
  opacity: 0; 
  background: none; 
  border: none; 
  color: #ff3b30; 
  cursor: pointer; 
  font-size: 16px; 
  line-height: 1; 
  padding: 0 8px;
  flex-shrink: 0;
}
.todo-item:hover .delete-btn { opacity: 1; }
</style>