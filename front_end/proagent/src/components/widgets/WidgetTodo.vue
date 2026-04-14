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
            <label>开始: </label>
            <input type="date" v-model="newTaskStart" class="mac-input mini" />
          </div>
          <div>
            <label>结束: </label>
            <input type="date" v-model="newTaskEnd" class="mac-input mini" />
          </div>
        </div>
        <div class="color-picker-row">
          <label>颜色: </label>
          <div class="color-options">
            <span v-for="c in colorOptions" :key="c" class="color-dot" :style="{ backgroundColor: c }" :class="{ active: newTaskColor === c }" @click="newTaskColor = c"></span>
          </div>
        </div>
        <div class="date-actions">
          <button class="mac-btn secondary" @click="showDatePicker = false">取消</button>
          <button class="mac-btn primary" @click="confirmAddTask">确定</button>
        </div>
      </div>

      <ul class="todo-list">
        <li v-for="task in store.todos" :key="task.id" class="todo-item" :class="{ 'is-completed': task.completed }">
          <input 
            type="checkbox" 
            :checked="task.completed" 
            @change="store.toggleTodo(task.id)" 
            class="mac-checkbox" 
          />
          <div class="task-color-indicator" :style="{ backgroundColor: task.color || '#007aff' }"></div>
          <span class="task-text">{{ task.title }}</span>
          <button @click="store.removeTodo(task.id)" class="delete-btn">×</button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDashboardStore } from '../../stores/dashboard'

// 初始化 Store
const store = useDashboardStore()
const newTaskTitle = ref('')

const showDatePicker = ref(false)
const newTaskStart = ref('')
const newTaskEnd = ref('')
const newTaskColor = ref('#007aff')

const colorOptions = ['#007aff', '#34c759', '#ff9500', '#ff3b30', '#af52de']

const prepareAddTask = () => {
  if (!newTaskTitle.value.trim()) return
  const today = new Date().toISOString().split('T')[0]
  newTaskStart.value = today
  newTaskEnd.value = today
  newTaskColor.value = '#007aff'
  showDatePicker.value = true
}

const confirmAddTask = () => {
  if (!newTaskTitle.value.trim()) return
  store.addTodo({
    title: newTaskTitle.value.trim(),
    start: newTaskStart.value,
    end: newTaskEnd.value,
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

/* 恢复输入框的 macOS 样式 */
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
.color-picker-row { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #555; }
.color-picker-row label { font-weight: 500; }
.color-options { display: flex; gap: 6px; }
.color-dot { width: 14px; height: 14px; border-radius: 50%; cursor: pointer; border: 2px solid transparent; }
.color-dot.active { border-color: #1d1d1f; box-shadow: inset 0 0 0 1px #fff; }
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

.todo-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.todo-item { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 6px 0; border-radius: 6px; }
.todo-item:hover { background: rgba(0,0,0,0.02); }
.todo-item.is-completed .task-text { text-decoration: line-through; color: #86868b; }
.task-color-indicator { width: 8px; height: 8px; border-radius: 50%; opacity: 0.8; }
.task-text { flex: 1; color: #1d1d1f; }

/* 恢复 Checkbox 样式 */
.mac-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #007aff;
  cursor: pointer;
}

.delete-btn { opacity: 0; background: none; border: none; color: #ff3b30; cursor: pointer; font-size: 16px; line-height: 1; padding: 0 8px; }
.todo-item:hover .delete-btn { opacity: 1; }
</style>