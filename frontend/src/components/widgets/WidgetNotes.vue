<template>
  <div class="widget-container">
    <div class="panel-header">
      <h3 class="panel-title">工作笔记</h3>
      <div class="header-actions">
        <span class="status-text" v-if="isSaving">Saving...</span>
        <button class="notes-btn" @click="saveNote">Save</button>
      </div>
    </div>
    <div class="panel-body">
      <textarea 
        v-model="noteContent" 
        class="notes-textarea" 
        placeholder="使用 Markdown 格式记录想法..."
        @keydown.ctrl.s.prevent="saveNote"
        @keydown.meta.s.prevent="saveNote"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const noteContent = ref('')
const isSaving = ref(false)

const saveNote = () => {
  if (!noteContent.value) return
  isSaving.value = true
  // 此处接入 API 存储逻辑或分发事件给热力图更新数据
  setTimeout(() => {
    isSaving.value = false
    console.log('Note saved:', noteContent.value)
  }, 500)
}
</script>

<style scoped>
.widget-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  margin: 0;
  color: #1d1d1f;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-text {
  font-size: 11px;
  color: #86868b;
}

.notes-btn {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fff;
  color: #1d1d1f;
  transition: background 0.15s;
}

.notes-btn:hover {
  background: #f5f5f7;
}

.panel-body {
  flex: 1;
  padding: 12px 16px;
  overflow: hidden;
}

.notes-textarea {
  width: 100%;
  height: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  outline: none;
  resize: none;
  font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #1d1d1f;
  background: transparent;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.notes-textarea:focus {
  border-color: #007aff;
}

.notes-textarea::placeholder {
  color: #c7c7cc;
}
</style>