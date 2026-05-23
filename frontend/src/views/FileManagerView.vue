<template>
  <div class="file-manager">
    <!-- Top bar: directory input + actions -->
    <div class="fm-header">
      <div class="fm-dir-row">
        <div class="fm-dir-input-wrap">
          <svg class="fm-dir-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <input
            v-model="dirInput"
            class="fm-dir-input"
            placeholder="输入工作目录，如 /Users/yanmin/Documents"
            @keydown.enter="!$event.isComposing && handleSetDirectory()"
          />
        </div>
        <button class="fm-btn" @click="handleSetDirectory" :disabled="fmStore.isLoading">
          设置目录
        </button>
        <button class="fm-btn" @click="handleRefresh" :disabled="!fmStore.isDirectorySet || fmStore.isLoading" title="刷新">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
      </div>

      <div v-if="fmStore.isDirectorySet && fmStore.breadcrumbs.length" class="fm-breadcrumb">
        <button
          v-for="(crumb, i) in fmStore.breadcrumbs"
          :key="crumb.relativePath"
          class="fm-crumb"
          :class="{ active: i === fmStore.breadcrumbs.length - 1 }"
          @click="fmStore.navigateToFolder(crumb.relativePath)"
        >
          <span v-if="i > 0" class="fm-crumb-sep">/</span>
          {{ crumb.name }}
        </button>
      </div>

      <p v-if="fmStore.error" class="fm-error">{{ fmStore.error }}</p>
    </div>

    <!-- Action bar -->
    <div v-if="fmStore.isDirectorySet" class="fm-action-bar">
      <button class="fm-btn-sm" @click="startCreate('file')" :disabled="fmStore.isLoading">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建文件
      </button>
      <button class="fm-btn-sm" @click="startCreate('folder')" :disabled="fmStore.isLoading">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建文件夹
      </button>
      <button v-if="fmStore.currentRelativePath" class="fm-btn-sm fm-btn-secondary" @click="fmStore.navigateUp()" :disabled="fmStore.isLoading">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><polyline points="12 19 5 12 12 5"/></svg>
        返回上级
      </button>
    </div>

    <!-- Inline create input -->
    <div v-if="creating" class="fm-create-row">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <template v-if="createType === 'folder'"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></template>
        <template v-else><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></template>
      </svg>
      <input
        ref="createInputRef"
        v-model="createName"
        class="fm-create-input"
        :placeholder="createType === 'folder' ? '文件夹名称' : '文件名称'"
        @keydown.enter="!$event.isComposing && confirmCreate()"
        @keydown.escape="cancelCreate"
      />
      <button class="fm-btn-sm" @click="confirmCreate" :disabled="!createName.trim()">确认</button>
      <button class="fm-btn-sm fm-btn-ghost" @click="cancelCreate">取消</button>
    </div>

    <!-- Main content: list + preview -->
    <div class="fm-body" :class="{ 'fm-body-previewing': fmStore.previewFile }">
      <!-- File list -->
      <div class="fm-list-container">
        <div v-if="!fmStore.isDirectorySet" class="fm-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <p>请先设置工作目录</p>
        </div>

        <div v-else-if="fmStore.isLoading && fmStore.entries.length === 0" class="fm-empty">
          <div class="fm-spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="fmStore.entries.length > 0" class="fm-list">
          <div class="fm-list-header">
            <span class="fm-col-name">名称</span>
            <span class="fm-col-size">大小</span>
            <span class="fm-col-date">修改时间</span>
            <span class="fm-col-actions">操作</span>
          </div>

          <div
            v-for="entry in fmStore.entries"
            :key="entry.relative_path"
            class="fm-entry"
            :class="{
              'fm-entry-dir': entry.is_directory,
              'fm-entry-active': fmStore.previewFile && fmStore.previewFile.name === entry.name && !entry.is_directory
            }"
          >
            <template v-if="renamingEntry === entry.name">
              <div class="fm-entry-name fm-rename-row">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <template v-if="entry.is_directory"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></template>
                  <template v-else><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></template>
                </svg>
                <input
                  ref="renameInputRef"
                  v-model="renameValue"
                  class="fm-rename-input"
                  @keydown.enter="!$event.isComposing && confirmRename(entry)"
                  @keydown.escape="cancelRename"
                />
                <button class="fm-btn-sm" @click="confirmRename(entry)" :disabled="!renameValue.trim()">确认</button>
                <button class="fm-btn-sm fm-btn-ghost" @click="cancelRename">取消</button>
              </div>
            </template>

            <template v-else>
              <div
                class="fm-entry-name"
                :class="{ clickable: true }"
                @click="entry.is_directory ? fmStore.navigateToFolder(entry.relative_path) : fmStore.openPreview(entry)"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <template v-if="entry.is_directory"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></template>
                  <template v-else><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></template>
                </svg>
                <span class="fm-filename">{{ entry.is_directory ? entry.name : entry.name.replace(/\.md$/, '') }}</span>
              </div>
              <span class="fm-col-size">{{ entry.is_directory ? '—' : formatSize(entry.size) }}</span>
              <span class="fm-col-date">{{ formatDate(entry.modified_at) }}</span>
              <div class="fm-col-actions">
                <button class="fm-btn-icon" @click="startRename(entry)" title="重命名">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 16.5 3 18l1.5-4.5L17 3z"/></svg>
                </button>
                <button
                  v-if="pendingDelete !== entry.name"
                  class="fm-btn-icon fm-btn-danger"
                  @click="handleDelete(entry)"
                  title="删除"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
                <button
                  v-else
                  class="fm-btn-icon fm-btn-danger-active"
                  @click="handleDelete(entry)"
                  title="再次点击确认删除"
                >
                  确认?
                </button>
              </div>
            </template>
          </div>
        </div>

        <div v-else-if="fmStore.isDirectorySet && !fmStore.isLoading && fmStore.entries.length === 0" class="fm-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.3"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          <p>此目录为空</p>
        </div>
      </div>

      <!-- Preview panel -->
      <transition name="fm-preview-slide">
        <div v-if="fmStore.previewFile" class="fm-preview">
          <div class="fm-preview-header">
            <div class="fm-preview-title">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <span>{{ fmStore.previewFile.name.replace(/\.md$/, '') }}</span>
            </div>
            <div class="fm-preview-actions">
              <template v-if="!isEditing">
                <button class="fm-btn-icon" @click="startEditing" title="编辑">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 16.5 3 18l1.5-4.5L17 3z"/></svg>
                </button>
              </template>
              <template v-else>
                <button class="fm-btn-icon fm-save-icon" @click="saveEditing" :disabled="isSaving" title="保存">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                </button>
                <button class="fm-btn-icon" @click="cancelEditing" title="取消编辑">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </template>
              <button class="fm-btn-icon" @click="fmStore.closePreview()" title="关闭">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="fm-preview-body">
            <div v-if="fmStore.previewLoading" class="fm-preview-loading">
              <div class="fm-spinner"></div>
            </div>
            <template v-else-if="isEditing">
              <textarea
                v-model="editContent"
                class="fm-edit-area"
                spellcheck="false"
              ></textarea>
            </template>
            <div v-else class="fm-preview-content markdown-body" v-html="renderedContent"></div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useFileManagerStore } from '../stores/fileManager.js'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
  headerIds: false,
  mangle: false
})

const fmStore = useFileManagerStore()

const dirInput = ref(fmStore.workingDirectory)
const creating = ref(false)
const createType = ref('file')
const createName = ref('')
const createInputRef = ref(null)
const renamingEntry = ref(null)
const renameValue = ref('')
const renameInputRef = ref(null)
const pendingDelete = ref(null)
const isEditing = ref(false)
const editContent = ref('')
const isSaving = ref(false)

const renderedContent = computed(() => {
  if (!fmStore.previewContent) return ''
  try {
    return marked.parse(fmStore.previewContent)
  } catch {
    return fmStore.previewContent
  }
})

const handleSetDirectory = async () => {
  await fmStore.setDirectory(dirInput.value)
}

const handleRefresh = async () => {
  await fmStore.listFiles()
}

const formatSize = (bytes) => {
  if (bytes === null || bytes === undefined) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const formatDate = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const startCreate = (type) => {
  creating.value = true
  createType.value = type
  createName.value = ''
  nextTick(() => {
    createInputRef.value?.focus()
  })
}

const confirmCreate = async () => {
  let name = createName.value.trim()
  if (!name) return
  try {
    if (createType.value === 'folder') {
      await fmStore.createFolder(name)
    } else {
      if (!name.endsWith('.md')) name = name + '.md'
      await fmStore.createFile(name)
    }
    creating.value = false
    createName.value = ''
  } catch (err) {
    alert(err.message || '创建失败')
  }
}

const cancelCreate = () => {
  creating.value = false
  createName.value = ''
}

const startRename = (entry) => {
  renamingEntry.value = entry.name
  renameValue.value = entry.is_directory ? entry.name : entry.name.replace(/\.md$/, '')
  nextTick(() => {
    renameInputRef.value?.[0]?.focus()
  })
}

const confirmRename = async (entry) => {
  let newName = renameValue.value.trim()
  if (!entry.is_directory && !newName.endsWith('.md')) {
    newName = newName + '.md'
  }
  if (!newName || newName === entry.name) {
    cancelRename()
    return
  }
  try {
    await fmStore.renameFile(entry.name, newName)
    cancelRename()
  } catch (err) {
    alert(err.message || '重命名失败')
  }
}

const cancelRename = () => {
  renamingEntry.value = null
  renameValue.value = ''
}

const handleDelete = (entry) => {
  if (pendingDelete.value === entry.name) {
    confirmDelete(entry)
  } else {
    pendingDelete.value = entry.name
    setTimeout(() => {
      if (pendingDelete.value === entry.name) {
        pendingDelete.value = null
      }
    }, 3000)
  }
}

const confirmDelete = async (entry) => {
  pendingDelete.value = null
  try {
    await fmStore.deleteFile(entry.name)
  } catch (err) {
    alert(err.message || '删除失败')
  }
}

const startEditing = () => {
  editContent.value = fmStore.previewContent
  isEditing.value = true
}

const cancelEditing = () => {
  isEditing.value = false
  editContent.value = ''
}

const saveEditing = async () => {
  if (!fmStore.previewFile || isSaving.value) return
  isSaving.value = true
  try {
    await fmStore.updateFile(fmStore.previewFile.name, editContent.value)
    isEditing.value = false
  } catch (err) {
    alert(err.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  fmStore.init()
})
</script>

<style scoped>
.file-manager {
  padding: 20px;
  min-height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.fm-header {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  padding: 16px 18px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.fm-dir-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.fm-dir-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  padding: 0 10px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: border-color 0.2s;
}

.fm-dir-input-wrap:focus-within {
  border-color: #007aff;
}

.fm-dir-icon {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
}

.fm-dir-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  color: #1d1d1f;
  padding: 8px 0;
  outline: none;
}

.fm-dir-input::placeholder {
  color: rgba(0, 0, 0, 0.3);
}

.fm-btn {
  padding: 7px 14px;
  background: #ffffff;
  border: 1px solid #000000;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  color: #000;
  transition: background 0.2s;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.fm-btn:hover:not(:disabled) { background: #f5f5f5; }
.fm-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.fm-btn-sm {
  padding: 4px 10px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  color: #1d1d1f;
  transition: background 0.2s;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.fm-btn-sm:hover:not(:disabled) { background: #f5f5f5; }
.fm-btn-sm:disabled { opacity: 0.4; cursor: not-allowed; }

.fm-btn-secondary {
  border-color: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.6);
}

.fm-btn-ghost {
  background: transparent;
  border: 1px solid transparent;
  color: rgba(0, 0, 0, 0.5);
}

.fm-btn-ghost:hover {
  background: rgba(0, 0, 0, 0.04);
}

.fm-btn-icon {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.35);
  transition: all 0.15s;
}

.fm-btn-icon:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.7);
}

.fm-btn-danger:hover {
  background: rgba(255, 59, 48, 0.08);
  color: #ff3b30;
}

.fm-btn-danger-active {
  background: rgba(255, 59, 48, 0.12);
  color: #ff3b30;
  font-size: 11px;
  font-weight: 600;
  padding: 0 6px;
  width: auto;
  border-radius: 4px;
}

.fm-btn-danger-active:hover {
  background: rgba(255, 59, 48, 0.2);
}

.fm-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0;
  margin-top: 10px;
  flex-wrap: wrap;
}

.fm-crumb {
  background: none;
  border: none;
  padding: 2px 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  transition: color 0.15s;
}

.fm-crumb:hover { color: #007aff; }

.fm-crumb.active {
  color: #1d1d1f;
  font-weight: 600;
  cursor: default;
}

.fm-crumb-sep {
  color: rgba(0, 0, 0, 0.2);
  margin: 0 1px;
}

.fm-error {
  margin: 8px 0 0;
  color: #ff3b30;
  font-size: 12px;
  font-weight: 500;
}

.fm-action-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  padding: 0 4px;
  flex-shrink: 0;
}

.fm-create-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  padding: 8px 14px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.fm-create-row > svg {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.4);
}

.fm-create-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 13px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  color: #1d1d1f;
  outline: none;
  padding: 4px 0;
}

.fm-create-input::placeholder {
  color: rgba(0, 0, 0, 0.3);
}

/* Body: split layout */
.fm-body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
}

.fm-list-container {
  flex: 1;
  min-width: 0;
}

.fm-list {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.fm-list-header {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: rgba(0, 0, 0, 0.02);
}

.fm-list-header span {
  font-size: 11px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.fm-entry {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  transition: background 0.12s;
}

.fm-entry:last-child {
  border-bottom: none;
}

.fm-entry:hover {
  background: rgba(0, 0, 0, 0.025);
}

.fm-entry-active {
  background: rgba(0, 122, 255, 0.06);
}

.fm-col-name {
  flex: 1;
  min-width: 0;
}

.fm-col-size {
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.fm-col-date {
  width: 130px;
  text-align: right;
  flex-shrink: 0;
}

.fm-col-actions {
  width: 60px;
  text-align: right;
  flex-shrink: 0;
  display: flex;
  gap: 2px;
  justify-content: flex-end;
  opacity: 0;
  transition: opacity 0.15s;
}

.fm-entry:hover .fm-col-actions {
  opacity: 1;
}

.fm-entry-name {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  cursor: pointer;
}

.fm-entry-name:hover .fm-filename {
  color: #007aff;
}

.fm-entry-name svg {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
}

.fm-entry-dir .fm-entry-name svg {
  color: #007aff;
}

.fm-filename {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.15s;
}

.fm-col-size,
.fm-col-date {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.4);
}

.fm-rename-row {
  gap: 8px;
}

.fm-rename-input {
  flex: 1;
  border: none;
  border-bottom: 1.5px solid #007aff;
  background: transparent;
  font-size: 13px;
  font-family: inherit;
  color: #1d1d1f;
  outline: none;
  padding: 2px 0;
}

.fm-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(0, 0, 0, 0.3);
  gap: 8px;
}

.fm-empty p {
  font-size: 13px;
  margin: 0;
}

.fm-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  border-left-color: #007aff;
  border-radius: 50%;
  animation: fm-spin 0.8s linear infinite;
}

@keyframes fm-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Preview panel */
.fm-preview {
  width: 420px;
  flex-shrink: 0;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fm-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
}

.fm-preview-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.fm-save-icon {
  color: #34c759;
}

.fm-save-icon:hover {
  background: rgba(52, 199, 89, 0.1);
  color: #248a3d;
}

.fm-preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  min-width: 0;
  overflow: hidden;
}

.fm-preview-title svg {
  flex-shrink: 0;
  color: #007aff;
}

.fm-preview-title span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fm-preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 0;
}

.fm-preview-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.fm-preview-content {
  font-size: 13px;
  line-height: 1.6;
  color: #1d1d1f;
}

.fm-preview-content :deep(h1) { font-size: 18px; font-weight: 700; margin: 0 0 12px; }
.fm-preview-content :deep(h2) { font-size: 16px; font-weight: 600; margin: 0 0 10px; }
.fm-preview-content :deep(h3) { font-size: 14px; font-weight: 600; margin: 0 0 8px; }
.fm-preview-content :deep(p) { margin: 0 0 8px; }
.fm-preview-content :deep(ul), .fm-preview-content :deep(ol) { margin: 0 0 8px; padding-left: 20px; }
.fm-preview-content :deep(li) { margin: 2px 0; }
.fm-preview-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 5px;
  border-radius: 4px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
}
.fm-preview-content :deep(pre) {
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 0 0 12px;
}
.fm-preview-content :deep(pre code) {
  background: none;
  padding: 0;
}
.fm-preview-content :deep(blockquote) {
  border-left: 3px solid #007aff;
  margin: 0 0 8px;
  padding: 4px 12px;
  color: rgba(0, 0, 0, 0.6);
}
.fm-preview-content :deep(a) {
  color: #007aff;
  text-decoration: none;
}

.fm-edit-area {
  width: 100%;
  height: 100%;
  border: none;
  background: transparent;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #1d1d1f;
  resize: none;
  outline: none;
  padding: 0;
}

/* Preview slide transition */
.fm-preview-slide-enter-active {
  transition: all 0.2s ease-out;
}
.fm-preview-slide-leave-active {
  transition: all 0.15s ease-in;
}
.fm-preview-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.fm-preview-slide-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

@media (max-width: 768px) {
  .fm-col-size { display: none; }
  .fm-col-date { display: none; }
  .fm-list-header .fm-col-size,
  .fm-list-header .fm-col-date { display: none; }

  .fm-preview {
    position: fixed;
    inset: 0;
    width: 100%;
    border-radius: 0;
    z-index: 100;
  }
}
</style>