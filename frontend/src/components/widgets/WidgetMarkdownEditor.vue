<template>
  <div class="widget-container">
    <div class="panel-header">
      <div class="header-left">
        <button class="header-icon-btn" @click="sidebarCollapsed = !sidebarCollapsed" :title="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <h3 class="panel-title">Markdown 笔记</h3>
      </div>
      <div class="header-actions">
        <span class="status-text" :class="{ hidden: !statusMessage }">{{ statusMessage || '\u00A0' }}</span>
        <button class="header-action-btn" @click="handleNewFolder" :disabled="isCreating" title="新建文件夹">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
          新建文件夹
        </button>
        <button class="header-action-btn" @click="handleNewNote" :disabled="isCreating" title="新建笔记">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          新建笔记
        </button>
        <button
          class="header-action-btn save-btn"
          :class="{ hidden: !currentFile }"
          :disabled="isSaving || !currentFile"
          @click="handleManualSave"
          title="保存 (Ctrl+S)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          {{ saveFeedback === 'saved' ? '已保存' : '保存' }}
        </button>
        <div class="settings-wrapper" ref="settingsRef">
          <button class="header-icon-btn" @click="showSettings = !showSettings" title="设置">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </button>
          <div v-if="showSettings" class="settings-dropdown">
            <div class="settings-option" @click="toggleSaveMode">
              <span>自动保存</span>
              <span class="settings-toggle" :class="{ active: saveMode === 'auto' }">{{ saveMode === 'auto' ? '开' : '关' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!fileManagerStore.isDirectorySet" class="panel-body placeholder-state">
      <div class="placeholder-content">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#86868b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <p class="placeholder-text">请先在文件管理器中设置工作目录</p>
      </div>
    </div>

    <div v-else class="editor-layout">
      <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-content">
          <div class="sidebar-section">
            <div class="breadcrumb" v-if="fileManagerStore.breadcrumbs.length > 1">
              <button
                v-for="(crumb, idx) in fileManagerStore.breadcrumbs"
                :key="idx"
                class="breadcrumb-item"
                @click="fileManagerStore.navigateToFolder(crumb.relativePath)"
              >{{ crumb.name }}<span v-if="idx < fileManagerStore.breadcrumbs.length - 1" class="breadcrumb-sep">/</span></button>
            </div>
            <div v-else class="breadcrumb">
              <span class="breadcrumb-item active">根目录</span>
            </div>
          </div>

          <div class="file-list" v-if="!sidebarCollapsed">
            <div
              v-for="entry in sidebarEntries"
              :key="entry.name"
              class="file-item"
              :class="{ 
                active: currentFile && currentFile.name === entry.name, 
                'is-directory': entry.is_directory,
                'pending-delete': pendingDeleteEntry === entry
              }"
              @click="handleEntryClick(entry)"
              @dblclick="handleDoubleClick(entry)"
            >
              <span class="file-icon">
                <svg v-if="entry.is_directory" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </span>
              <span v-if="renamingEntry === entry" class="rename-input-wrapper">
                <input
                  ref="renameInput"
                  class="rename-input"
                  v-model="renameValue"
                  @keyup.enter="confirmRename(entry)"
                  @keyup.escape="cancelRename"
                  @blur="confirmRename(entry)"
                />
              </span>
              <span v-else class="file-name">{{ entry.is_directory ? entry.name : entry.name.replace(/\.md$/, '') }}</span>
              <div class="file-actions">
                <button class="file-action-btn" @click.stop="startRename(entry)" title="重命名">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 16.5 3 18l1.5-4.5L17 3z"/></svg>
                </button>
                <button class="file-action-btn file-action-delete" @click.stop="handleDelete(entry)" :title="pendingDeleteEntry === entry ? '确认删除' : '删除'">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </div>

            <div v-if="sidebarEntries.length === 0" class="empty-folder">
              空文件夹
            </div>
          </div>
        </div>
      </div>

      <div class="editor-area">
        <div class="editor-topbar">
          <div v-if="currentFile && editingTitle" class="title-edit-row">
            <input
              ref="titleInputRef"
              class="title-edit-input"
              v-model="titleValue"
              @keyup.enter="confirmTitleEdit"
              @keyup.escape="cancelTitleEdit"
              @blur="confirmTitleEdit"
            />
          </div>
          <span
            v-else
            class="current-file-name"
            :class="{ editable: !!currentFile }"
            @click="currentFile && startTitleEdit()"
            :title="currentFile ? '点击编辑文件名' : ''"
          >{{ currentFile ? currentFile.name.replace(/\.md$/, '') : '选择文件' }}</span>
          <div v-if="currentFile" class="mode-tabs">
            <button class="mode-tab" :class="{ active: editorMode === 'edit' }" @click="editorMode = 'edit'">Edit</button>
            <button class="mode-tab" :class="{ active: editorMode === 'preview' }" @click="editorMode = 'preview'">Preview</button>
          </div>
        </div>

        <div v-if="!currentFile" class="editor-placeholder">
          <p>从侧边栏选择一个 Markdown 文件开始编辑</p>
        </div>

        <div v-else-if="editorMode === 'edit'" class="editor-edit">
          <textarea
            ref="editorTextarea"
            class="editor-textarea"
            v-model="editContent"
            @input="handleInput"
            placeholder="开始编写 Markdown..."
          ></textarea>
        </div>

        <div v-else class="editor-preview" v-html="renderedMarkdown"></div>
      </div>

      <button v-if="sidebarCollapsed" class="sidebar-add-btn" @click="handleNewNote" title="新建笔记">+</button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useFileManagerStore } from '../../stores/fileManager.js'
import { marked } from 'marked'

const fileManagerStore = useFileManagerStore()

const sidebarCollapsed = ref(false)
const currentFile = ref(null)
const editContent = ref('')
const editorMode = ref('edit')
const saveMode = ref('auto')
const showSettings = ref(false)
const settingsRef = ref(null)
const editorTextarea = ref(null)
const renameInput = ref(null)

const renamingEntry = ref(null)
const renameValue = ref('')
const isSaving = ref(false)
const isCreating = ref(false)
const statusMessage = ref('')
const saveFeedback = ref(null)  // 'saved' | null

// New state for inline title editing and folder creation
const editingTitle = ref(false)
const titleValue = ref('')
const titleInputRef = ref(null)
const pendingDeleteEntry = ref(null)  // replaces confirm()

// For inline "new folder" default name
let folderCounter = 0

let saveTimer = null

const sidebarEntries = computed(() => {
  const dirs = fileManagerStore.directories || []
  const files = fileManagerStore.files || []
  return [...dirs, ...files]
})

const renderedMarkdown = computed(() => {
  if (!editContent.value) return '<p class="preview-empty">暂无内容</p>'
  return marked(editContent.value)
})

function handleEntryClick(entry) {
  if (entry.is_directory) {
    const targetPath = fileManagerStore.currentRelativePath
      ? fileManagerStore.currentRelativePath + '/' + entry.name
      : entry.name
    fileManagerStore.navigateToFolder(targetPath).catch(e => {
      showStatus('导航失败: ' + e.message, 'error')
    })
  } else if (!entry.name.endsWith('.md')) {
    currentFile.value = null
    editContent.value = ''
    showStatus('此文件类型不支持编辑，请在文件管理中查看', 'notice')
  } else {
    loadFile(entry)
  }
}

async function loadFile(entry) {
  currentFile.value = entry
  editorMode.value = 'edit'
  try {
    await fileManagerStore.openPreview(entry)
    editContent.value = fileManagerStore.previewContent || ''
  } catch (e) {
    showStatus('加载失败: ' + e.message, 'error')
  }
}

function handleInput() {
  if (saveMode.value === 'auto' && currentFile.value) {
    clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      handleManualSave()
    }, 500)
  }
}

async function handleManualSave() {
  if (!currentFile.value || isSaving.value) return
  isSaving.value = true
  try {
    await fileManagerStore.updateFile(currentFile.value.name, editContent.value)
    saveFeedback.value = 'saved'
    setTimeout(() => { saveFeedback.value = null }, 2000)
  } catch (e) {
    showStatus('保存失败: ' + e.message, 'error')
  } finally {
    isSaving.value = false
  }
}

async function handleNewFolder() {
  // Generate default folder name
  const existingDirs = fileManagerStore.directories || []
  const existingNames = new Set(existingDirs.map(d => d.name))
  let num = 1
  while (existingNames.has(`未命名文件夹 ${num}`)) num++
  const defaultName = `未命名文件夹 ${num}`

  isCreating.value = true
  showStatus('创建中...')
  try {
    await fileManagerStore.createFolder(defaultName)
    clearStatus()
  } catch (e) {
    showStatus('创建文件夹失败: ' + e.message, 'error')
  } finally {
    isCreating.value = false
  }
}

async function handleNewNote() {
  const existingMdFiles = (fileManagerStore.files || []).filter(f => f.name.endsWith('.md'))
  let num = 1
  const existingNames = new Set(existingMdFiles.map(f => f.name))
  while (existingNames.has(`未命名文档 ${num}.md`)) num++
  const defaultName = `未命名文档 ${num}.md`

  isCreating.value = true
  showStatus('创建中...')
  try {
    await fileManagerStore.createFile(defaultName)
    // After creation, find the entry and load it
    await nextTick()
    const entry = fileManagerStore.files.find(f => f.name === defaultName)
    if (entry) {
      await loadFile(entry)
    }
    clearStatus()
  } catch (e) {
    showStatus('创建笔记失败: ' + e.message, 'error')
  } finally {
    isCreating.value = false
  }
}

function handleDoubleClick(entry) {
  if (entry.is_directory) return
  startRename(entry)
}

function startRename(entry) {
  renamingEntry.value = entry
  renameValue.value = entry.is_directory ? entry.name : entry.name.replace(/\.md$/, '')
  nextTick(() => {
    const inputs = document.querySelectorAll('.rename-input')
    if (inputs.length > 0) inputs[0].focus()
  })
}

async function confirmRename(entry) {
  let newName = renameValue.value.trim()
  if (!entry.is_directory && !newName.endsWith('.md')) {
    newName = newName + '.md'
  }
  if (!newName || newName === entry.name) {
    cancelRename()
    return
  }
  try {
    await fileManagerStore.renameFile(entry.name, newName)
    if (currentFile.value && currentFile.value.name === entry.name) {
      currentFile.value = { ...currentFile.value, name: newName }
    }
  } catch (e) {
    console.error('重命名失败:', e)
  }
  renamingEntry.value = null
  renameValue.value = ''
}

function cancelRename() {
  renamingEntry.value = null
  renameValue.value = ''
}

async function handleDelete(entry) {
  if (pendingDeleteEntry.value === entry) {
    // Second click: actually delete
    pendingDeleteEntry.value = null
    try {
      await fileManagerStore.deleteFile(entry.name)
      if (currentFile.value && currentFile.value.name === entry.name) {
        currentFile.value = null
        editContent.value = ''
      }
    } catch (e) {
      showStatus('删除失败: ' + e.message, 'error')
    }
  } else {
    // First click: mark for deletion
    pendingDeleteEntry.value = entry
    setTimeout(() => {
      if (pendingDeleteEntry.value === entry) {
        pendingDeleteEntry.value = null
      }
    }, 3000)
  }
}

function startTitleEdit() {
  if (!currentFile.value) return
  editingTitle.value = true
  titleValue.value = currentFile.value.name.replace(/\.md$/, '')
  nextTick(() => {
    titleInputRef.value?.focus()
  })
}

async function confirmTitleEdit() {
  if (!titleValue.value.trim() || !currentFile.value) {
    cancelTitleEdit()
    return
  }
  let newName = titleValue.value.trim()
  // Force .md extension
  if (!newName.endsWith('.md')) {
    newName = newName + '.md'
  }
  const oldName = currentFile.value.name
  if (newName === oldName) {
    cancelTitleEdit()
    return
  }
  // Check for duplicates
  const existingNames = new Set(fileManagerStore.files.map(f => f.name))
  if (existingNames.has(newName)) {
    showStatus('文件名已存在', 'error')
    return
  }
  try {
    await fileManagerStore.renameFile(oldName, newName)
    currentFile.value = { ...currentFile.value, name: newName }
    showStatus('已重命名', 'success')
    setTimeout(clearStatus, 2000)
  } catch (e) {
    showStatus('重命名失败: ' + e.message, 'error')
  }
  editingTitle.value = false
}

function cancelTitleEdit() {
  editingTitle.value = false
  titleValue.value = ''
}

function handleClickOutside(e) {
  if (showSettings.value && settingsRef.value && !settingsRef.value.contains(e.target)) {
    showSettings.value = false
  }
}

function handleKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 's') {
    e.preventDefault()
    handleManualSave()
  }
  if (e.key === 'Escape') {
    showSettings.value = false
  }
}

function showStatus(msg, type = '') {
  statusMessage.value = msg
}

function clearStatus() {
  statusMessage.value = ''
}

function toggleSaveMode() {
  saveMode.value = saveMode.value === 'auto' ? 'manual' : 'auto'
  showSettings.value = false
}

watch(() => fileManagerStore.previewContent, (newVal) => {
  if (currentFile.value && currentFile.value.name === fileManagerStore.previewFile?.name) {
    editContent.value = newVal || ''
  }
})

watch(() => fileManagerStore.isDirectorySet, async (val) => {
  if (val) {
    try {
      await fileManagerStore.init()
    } catch (e) {
      showStatus('加载文件列表失败: ' + e.message, 'error')
    }
  }
})

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
  if (fileManagerStore.isDirectorySet) {
    try {
      await fileManagerStore.init()
    } catch (e) {
      showStatus('加载文件列表失败: ' + e.message, 'error')
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(saveTimer)
})
</script>

<style scoped>
.widget-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
  gap: 8px;
  min-height: 40px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
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
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  padding: 4px 10px;
  font-size: 11px;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fff;
  color: #1d1d1f;
  transition: all 0.2s;
  white-space: nowrap;
}

.header-action-btn:hover {
  background: #f5f5f7;
}

.header-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.header-action-btn.save-btn {
  background: #007aff;
  color: #fff;
  border-color: #0056cc;
}

.header-action-btn.save-btn:hover {
  background: #0062cc;
}

.header-action-btn.save-btn.hidden {
  visibility: hidden;
  pointer-events: none;
}

.header-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: #86868b;
  transition: all 0.2s;
}

.header-icon-btn:hover {
  background: #f5f5f7;
  color: #1d1d1f;
}

.status-text {
  flex-shrink: 0;
  font-size: 11px;
  color: #86868b;
  margin-left: 4px;
  white-space: nowrap;
}

.status-text.hidden {
  visibility: hidden;
}

.settings-wrapper {
  flex-shrink: 0;
  position: relative;
}

.settings-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-width: 160px;
  padding: 4px 0;
}

.settings-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 12px;
  color: #1d1d1f;
  cursor: pointer;
  transition: background 0.15s;
}

.settings-option:hover {
  background: #f5f5f7;
}

.settings-toggle {
  font-size: 11px;
  font-weight: 600;
  color: #86868b;
  padding: 2px 8px;
  border-radius: 4px;
  background: #f0f0f0;
}

.settings-toggle.active {
  color: #fff;
  background: #007aff;
}

.placeholder-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.placeholder-text {
  font-size: 13px;
  color: #86868b;
  margin: 0;
}

.editor-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.sidebar {
  width: 200px;
  min-width: 200px;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.2s, min-width 0.2s;
}

.sidebar.collapsed {
  width: 0;
  min-width: 0;
  border-right: none;
  overflow: hidden;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.sidebar-section {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 2px;
}

.breadcrumb-item {
  background: none;
  border: none;
  color: #007aff;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: background 0.15s;
}

.breadcrumb-item:hover {
  background: rgba(0, 122, 255, 0.08);
}

.breadcrumb-item.active {
  color: #1d1d1f;
  cursor: default;
}

.breadcrumb-item.active:hover {
  background: none;
}

.breadcrumb-sep {
  color: #86868b;
  font-size: 10px;
  margin: 0 1px;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  font-size: 12px;
  color: #1d1d1f;
  cursor: pointer;
  transition: background 0.15s;
  user-select: none;
}

.file-item:hover {
  background: rgba(0, 0, 0, 0.03);
}

.file-item.active {
  background: rgba(0, 122, 255, 0.08);
  color: #007aff;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.35);
}

.file-item.is-directory .file-icon {
  color: #007aff;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rename-input-wrapper {
  flex: 1;
  min-width: 0;
}

.rename-input {
  width: 100%;
  padding: 1px 4px;
  font-size: 12px;
  border: 1px solid #007aff;
  border-radius: 3px;
  outline: none;
  box-sizing: border-box;
  background: #fff;
}

.empty-folder {
  padding: 16px 10px;
  font-size: 11px;
  color: #86868b;
  text-align: center;
}

.editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.editor-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.current-file-name {
  font-size: 12px;
  font-weight: 500;
  color: #1d1d1f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-tabs {
  display: flex;
  gap: 0;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  overflow: hidden;
}

.mode-tab {
  padding: 3px 12px;
  font-size: 11px;
  font-weight: 500;
  border: none;
  background: #fff;
  color: #86868b;
  cursor: pointer;
  transition: all 0.15s;
}

.mode-tab:first-child {
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

.mode-tab.active {
  background: #007aff;
  color: #fff;
}

.mode-tab:hover:not(.active) {
  background: #f5f5f7;
}

.editor-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.editor-placeholder p {
  font-size: 13px;
  color: #86868b;
  margin: 0;
}

.editor-edit {
  flex: 1;
  overflow: hidden;
  display: flex;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  padding: 12px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #1d1d1f;
  background: #fafafa;
  box-sizing: border-box;
}

.editor-textarea::placeholder {
  color: #c7c7cc;
}

.editor-preview {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.7;
  color: #1d1d1f;
}

.editor-preview :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 16px 0 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.editor-preview :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 14px 0 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.editor-preview :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 12px 0 4px;
}

.editor-preview :deep(p) {
  margin: 0 0 10px;
}

.editor-preview :deep(ul),
.editor-preview :deep(ol) {
  padding-left: 20px;
  margin: 0 0 10px;
}

.editor-preview :deep(li) {
  margin: 2px 0;
}

.editor-preview :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
}

.editor-preview :deep(pre) {
  background: #1d1d1f;
  color: #f5f5f7;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0 0 10px;
}

.editor-preview :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  font-size: 12px;
}

.editor-preview :deep(blockquote) {
  border-left: 3px solid #007aff;
  margin: 0 0 10px;
  padding: 4px 12px;
  color: #86868b;
  background: rgba(0, 122, 255, 0.04);
  border-radius: 0 6px 6px 0;
}

.editor-preview :deep(a) {
  color: #007aff;
  text-decoration: none;
}

.editor-preview :deep(a:hover) {
  text-decoration: underline;
}

.editor-preview :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0 0 10px;
}

.editor-preview :deep(th),
.editor-preview :deep(td) {
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 6px 10px;
  font-size: 13px;
}

.editor-preview :deep(th) {
  background: #f5f5f7;
  font-weight: 600;
}

.editor-preview :deep(img) {
  max-width: 100%;
  border-radius: 6px;
}

.editor-preview :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  margin: 16px 0;
}

.preview-empty {
  color: #86868b;
  font-style: italic;
}

.sidebar-add-btn {
  position: absolute;
  bottom: 12px;
  left: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #007aff;
  color: #fff;
  border: none;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3);
  transition: all 0.2s;
  z-index: 10;
}

.sidebar-add-btn:hover {
  background: #0062cc;
  transform: scale(1.05);
}

/* Title editing */
.title-edit-row {
  flex: 1;
  min-width: 0;
}

.title-edit-input {
  width: 100%;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid #007aff;
  border-radius: 4px;
  outline: none;
  font-family: inherit;
  color: #1d1d1f;
  background: #fff;
  box-sizing: border-box;
}

.current-file-name.editable {
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background 0.15s;
}

.current-file-name.editable:hover {
  background: rgba(0, 122, 255, 0.08);
}

/* Hover action buttons */
.file-actions {
  display: flex;
  gap: 2px;
  margin-left: auto;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.file-item:hover .file-actions {
  opacity: 1;
}

.file-action-btn {
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.3);
  transition: all 0.15s;
  padding: 0;
}

.file-action-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.6);
}

.file-action-delete:hover {
  background: rgba(255, 59, 48, 0.12);
  color: #ff3b30;
}

/* Pending delete state */
.file-item.pending-delete {
  background: rgba(255, 59, 48, 0.08);
  color: #ff3b30;
}

.file-item.pending-delete:hover {
  background: rgba(255, 59, 48, 0.15);
}
</style>