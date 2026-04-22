<template>
  <div v-if="!dismissed" class="delete-confirm-card">
    <div class="dc-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
      </svg>
      <span class="dc-title">删除确认</span>
    </div>

    <p class="dc-desc">以下文件将被删除，此操作不可撤销：</p>

    <ul class="dc-file-list">
      <li v-for="(file, i) in files" :key="i" class="dc-file-item">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <span>{{ file }}</span>
      </li>
    </ul>

    <div class="dc-actions">
      <button class="dc-confirm-btn" @click="onConfirm" :disabled="confirmed">
        <template v-if="confirmed">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          已删除
        </template>
        <template v-else>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          确认删除
        </template>
      </button>
      <button class="dc-cancel-btn" @click="onDismiss" :disabled="confirmed">
        取消
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { agentAPI } from '../../services/api.js'
import { useFileManagerStore } from '../../stores/fileManager.js'

const props = defineProps({
  files: { type: Array, required: true },
  workingDirectory: { type: String, default: '' },
  initiallyDismissed: { type: Boolean, default: false }
})

const emit = defineEmits(['confirm', 'dismiss'])

const fmStore = useFileManagerStore()
const dismissed = ref(false)
const confirmed = ref(false)

const onConfirm = async () => {
  confirmed.value = true
  for (const file of props.files) {
    try {
      await agentAPI.deleteFileByPath(file, props.workingDirectory || null)
    } catch (err) {
      console.error(`Failed to delete ${file}:`, err)
    }
  }
  if (fmStore.isDirectorySet) {
    await fmStore.listFiles()
  }
  emit('confirm', props.files)
}

const onDismiss = () => {
  dismissed.value = true
  emit('dismiss')
}
</script>

<style scoped>
.delete-confirm-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 59, 48, 0.25);
  border-radius: 10px;
  padding: 10px;
  margin: 4px 0;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
}

.dc-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  color: #ff3b30;
}

.dc-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #ff3b30;
}

.dc-desc {
  font-size: 12px;
  color: #1d1d1f;
  margin: 0 0 6px;
  line-height: 1.4;
}

.dc-file-list {
  list-style: none;
  padding: 0;
  margin: 0 0 8px;
  background: rgba(255, 59, 48, 0.04);
  border-radius: 6px;
  padding: 6px 8px;
}

.dc-file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #1d1d1f;
  padding: 3px 0;
  font-family: ui-monospace, monospace;
}

.dc-file-item svg {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
}

.dc-actions {
  display: flex;
  gap: 6px;
}

.dc-confirm-btn, .dc-cancel-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.dc-confirm-btn {
  background: rgba(255, 59, 48, 0.9);
  color: white;
}

.dc-confirm-btn:hover:not(:disabled) {
  background: rgba(255, 59, 48, 1);
}

.dc-confirm-btn:disabled {
  background: rgba(255, 59, 48, 0.5);
  cursor: default;
}

.dc-cancel-btn {
  background: rgba(0, 0, 0, 0.05);
  color: #6b7280;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.dc-cancel-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
  color: #1d1d1f;
}

.dc-cancel-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>