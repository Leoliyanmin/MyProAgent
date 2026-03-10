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
          @keyup.enter="handleAddTask" 
          type="text" 
          placeholder="添加新任务..." 
          class="mac-input" 
        />
      </div>
      <ul class="todo-list">
        <li v-for="task in store.todos" :key="task.id" class="todo-item" :class="{ 'is-completed': task.completed }">
          <input 
            type="checkbox" 
            :checked="task.completed" 
            @change="store.toggleTodo(task)" 
            class="mac-checkbox" 
          />
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

const handleAddTask = () => {
  if (!newTaskTitle.value.trim()) return
  store.addTodo(newTaskTitle.value)
  newTaskTitle.value = ''
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

.todo-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.todo-item { display: flex; align-items: center; gap: 10px; font-size: 13px; padding: 6px 0; border-radius: 6px; }
.todo-item:hover { background: rgba(0,0,0,0.02); }
.todo-item.is-completed .task-text { text-decoration: line-through; color: #86868b; }
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