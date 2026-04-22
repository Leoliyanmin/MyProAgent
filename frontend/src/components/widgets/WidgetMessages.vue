<template>
  <div class="widget-container">
    <div class="panel-header">
      <div class="source-tags">
        <button 
          v-for="src in sources" 
          :key="src.id"
          class="circle-tag" 
          :class="{ active: activeSource === src.id }"
          @click="activeSource = src.id"
        >
          {{ src.name }}
        </button>
      </div>
    </div>
    <div class="panel-body">
      <ul class="message-list">
        <li v-for="msg in filteredMessages" :key="msg.id" class="message-item">
          <div class="msg-meta">
            <span class="msg-time">{{ msg.time }}</span>
            <span v-if="msg.unread" class="unread-dot"></span>
          </div>
          <div class="msg-content">{{ msg.content }}</div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const sources = [
  { id: 'email', name: 'Email' },
  { id: 'blackboard', name: 'BlackBoard' },
  { id: 'github', name: 'GitHub' }
]

const activeSource = ref('blackboard')

const messages = ref([
  { id: 1, source: 'blackboard', time: '10:30 AM', content: 'CS310: Midterm grades have been posted.', unread: true },
  { id: 2, source: 'blackboard', time: 'Yesterday', content: 'CS305: New reading assignment available.', unread: false },
  { id: 3, source: 'github', time: '2 hours ago', content: 'PR merged: Fix inverse kinematics bug in simulation.', unread: true },
  { id: 4, source: 'email', time: '09:00 AM', content: 'Weekly lab meeting rescheduled to Friday.', unread: false }
])

const filteredMessages = computed(() => {
  return messages.value.filter(m => m.source === activeSource.value)
})
</script>

<style scoped>
.widget-container { display: flex; flex-direction: column; height: 100%; }
.panel-header { display: flex; align-items: center; padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.source-tags { display: flex; gap: 8px; }
.circle-tag { background: transparent; border: 1px solid rgba(0,0,0,0.15); border-radius: 16px; padding: 4px 12px; font-size: 11px; font-weight: 500; cursor: pointer; color: #1d1d1f; transition: all 0.2s; }
.circle-tag.active { border-color: #1d1d1f; background: #1d1d1f; color: #ffffff; }
.panel-body { flex: 1; padding: 0; overflow-y: auto; }
.message-list { list-style: none; padding: 0; margin: 0; }
.message-item { padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.04); cursor: pointer; }
.message-item:hover { background: rgba(0,0,0,0.02); }
.msg-meta { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.msg-time { font-size: 11px; color: #86868b; }
.unread-dot { width: 6px; height: 6px; background-color: #007aff; border-radius: 50%; }
.msg-content { font-size: 13px; color: #1d1d1f; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
</style>