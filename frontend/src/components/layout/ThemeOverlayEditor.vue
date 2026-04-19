<template>
  <div class="theme-overlay" aria-label="主题覆盖编辑模式">
    <button
      class="zone zone-sidebar"
      :class="{ active: activeToken === 'bgSidebar' }"
      :style="zoneSidebarStyle"
      @click="selectToken('bgSidebar')"
      type="button"
    >
      侧边栏
    </button>

    <button
      class="zone zone-topbar"
      :class="{ active: activeToken === 'bgTopbar' }"
      :style="zoneTopbarStyle"
      @click="selectToken('bgTopbar')"
      type="button"
    >
      顶栏
    </button>

    <button
      class="zone zone-content"
      :class="{ active: activeToken === 'bgContent' }"
      :style="zoneContentStyle"
      @click="selectToken('bgContent')"
      type="button"
    >
      内容区
    </button>

    <button
      class="zone zone-agent"
      :class="{ active: activeToken === 'bgAgent' }"
      :style="zoneAgentStyle"
      @click="selectToken('bgAgent')"
      type="button"
    >
      Agent 助手
    </button>

    <div
      v-if="activeToken"
      ref="panelRef"
      class="edit-panel"
      :style="panelStyle"
    >
      <div class="panel-header">
        <div class="drag-handle" @mousedown="startDrag($event)">
          <h3 class="panel-main-title">
            <svg class="title-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            主题编辑
          </h3>
          <span class="drag-hint">可拖动</span>
        </div>
        <div class="panel-actions">
          <button class="ov-btn" :disabled="!store.canUndo" @click="store.undo()" title="撤销">撤销</button>
          <button class="ov-btn ov-btn-danger" @click="store.reset()" title="重置所有">重置</button>
          <button
            class="ov-btn ov-btn-save"
            @pointerdown.stop
            @mousedown.stop
            @click.stop.prevent="saveTheme"
            title="保存主题"
          >
            {{ saveButtonText }}
          </button>
          <button class="ov-btn" @click="emit('exit')" title="退出编辑">退出</button>
        </div>
      </div>

      <div class="save-state" aria-live="polite">{{ saveStatusText }}</div>

      <div v-if="saveInlineVisible" class="save-inline" role="status" aria-live="polite">
        {{ saveFeedbackText }}
      </div>

      <h4 class="panel-title">{{ TOKEN_META[activeToken].label }}</h4>
      <p class="panel-desc">{{ TOKEN_META[activeToken].desc }}</p>

      <template v-if="TOKEN_META[activeToken].type === 'color'">
        <label class="field-label">调色盘</label>
        <div class="picker-row">
          <input
            class="native-picker"
            type="color"
            :value="store.tokens[activeToken]"
            @input="onColorInput"
          />
          <input
            class="hex-input"
            type="text"
            :value="store.tokens[activeToken]"
            @change="onHexChange"
            spellcheck="false"
          />
        </div>
      </template>

      <template v-if="canUploadImage(activeToken)">
        <label class="field-label">插入图片</label>
        <div class="upload-row">
          <button class="ov-btn upload-btn" type="button" @click="openImagePicker">选择图片</button>
          <button
            v-if="store.tokens[getImageKey(activeToken)]"
            class="ov-btn upload-btn"
            type="button"
            @click="clearImage"
          >
            清除图片
          </button>
        </div>
        <p class="upload-hint">
          {{ store.tokens[getImageKey(activeToken)] ? '已插入背景图片，保存后会保留。' : '支持 PNG / JPG / WEBP / GIF。' }}
        </p>
      </template>

      <input
        ref="fileInput"
        class="image-input"
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        style="display:none"
        @change="onFileChange"
      />

      <div class="quick-tokens">
        <button
          v-for="key in quickKeys"
          :key="key"
          class="quick-token"
          :class="{ selected: activeToken === key }"
          @click="selectToken(key)"
          type="button"
        >
          <span class="swatch" :style="getSwatchStyle(key)"></span>
          {{ TOKEN_META[key].label }}
        </button>
      </div>
    </div>

    <div v-if="saveToastVisible" class="save-toast" role="status" aria-live="polite">
      {{ saveFeedbackText }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useThemeStore } from '../../stores/theme.js'

const emit = defineEmits(['exit'])
const store = useThemeStore()
const activeToken = ref('bgContent')
const panelRef = ref(null)
const saveToastVisible = ref(false)
const saveInlineVisible = ref(false)
const saveButtonText = ref('保存')
const saveStatusText = ref('当前状态：未保存')
const saveFeedbackText = ref('主题已保存')
const lastSavedSnapshot = ref('')
const lastSavedAtText = ref('')
const fileInput = ref(null)

const layoutMetrics = ref({
  sidebarWidth: 240,
  topbarHeight: 52,
  agentWidth: 300
})

const panelPos = ref({
  top: 86,
  left: 0
})

const dragState = ref({
  offsetX: 0,
  offsetY: 0
})

let saveToastTimer = null
let saveInlineTimer = null
let saveButtonTimer = null

const serializeTokens = () => JSON.stringify({ ...store.tokens })

const readSavedSnapshot = () => {
  try {
    const saved = localStorage.getItem('proagent_theme')
    return saved || ''
  } catch (error) {
    console.warn('[ThemeOverlay] Failed to read saved snapshot:', error)
    return ''
  }
}

const updateSaveStatusText = () => {
  const currentSnapshot = serializeTokens()
  const isDirty = currentSnapshot !== lastSavedSnapshot.value

  if (isDirty) {
    saveStatusText.value = '当前状态：未保存'
    return
  }

  if (lastSavedAtText.value) {
    saveStatusText.value = `当前状态：已保存 (${lastSavedAtText.value})`
    return
  }

  saveStatusText.value = '当前状态：已保存'
}

watch(
  () => serializeTokens(),
  () => {
    updateSaveStatusText()
  }
)

const TOKEN_META = {
  bgSidebar: { label: '侧边栏背景', desc: '左侧导航区域背景色', type: 'color', canUploadImage: true },
  bgTopbar: { label: '顶栏背景', desc: '顶部标签栏背景色', type: 'color', canUploadImage: true },
  bgContent: { label: '内容区背景', desc: '主内容区域背景色', type: 'color', canUploadImage: true },
  bgAgent: { label: 'Agent 助手背景', desc: '右侧 Agent 侧边栏背景色', type: 'color', canUploadImage: true }
}

const quickKeys = [
  'bgSidebar',
  'bgTopbar',
  'bgContent',
  'bgAgent'
]

const panelStyle = computed(() => ({
  top: `${panelPos.value.top}px`,
  left: `${panelPos.value.left}px`
}))

const zoneSidebarStyle = computed(() => ({
  top: '0px',
  left: '0px',
  width: `${layoutMetrics.value.sidebarWidth}px`,
  bottom: '0px',
  ...getZonePaintStyle('bgSidebar')
}))

const zoneTopbarStyle = computed(() => ({
  top: '0px',
  left: `${layoutMetrics.value.sidebarWidth}px`,
  right: `${layoutMetrics.value.agentWidth}px`,
  height: `${layoutMetrics.value.topbarHeight}px`,
  ...getZonePaintStyle('bgTopbar')
}))

const zoneContentStyle = computed(() => ({
  top: `${layoutMetrics.value.topbarHeight}px`,
  left: `${layoutMetrics.value.sidebarWidth}px`,
  right: `${layoutMetrics.value.agentWidth}px`,
  bottom: '0px',
  ...getZonePaintStyle('bgContent')
}))

const zoneAgentStyle = computed(() => {
  if (layoutMetrics.value.agentWidth <= 0) {
    return { display: 'none' }
  }

  return {
    top: '0px',
    right: '0px',
    width: `${layoutMetrics.value.agentWidth}px`,
    bottom: '0px',
    ...getZonePaintStyle('bgAgent')
  }
})

const selectToken = (key) => {
  activeToken.value = key
}

const getImageKey = (key) => `${key}Image`

const canUploadImage = (key) => Boolean(TOKEN_META[key]?.canUploadImage)

const getZonePaintStyle = (key) => {
  const imageValue = store.tokens[getImageKey(key)]
  const style = {
    backgroundColor: store.tokens[key]
  }

  if (imageValue) {
    style.backgroundImage = `url("${imageValue}")`
    style.backgroundSize = 'cover'
    style.backgroundPosition = 'center'
    style.backgroundRepeat = 'no-repeat'
  }

  return style
}

const getViewportBounds = () => {
  const el = panelRef.value
  const width = el?.offsetWidth ?? 320
  const height = el?.offsetHeight ?? 360
  return {
    minLeft: 0,
    maxLeft: Math.max(0, window.innerWidth - width),
    minTop: 0,
    maxTop: Math.max(0, window.innerHeight - height)
  }
}

const clampPoint = (point, bounds) => ({
  left: Math.min(bounds.maxLeft, Math.max(bounds.minLeft, point.left)),
  top: Math.min(bounds.maxTop, Math.max(bounds.minTop, point.top))
})

const startDrag = (event) => {
  if (event.button !== 0) return
  const currentPos = panelPos.value
  dragState.value = {
    offsetX: event.clientX - currentPos.left,
    offsetY: event.clientY - currentPos.top
  }
  window.addEventListener('mousemove', onDragMove)
  window.addEventListener('mouseup', stopDrag)
}

const onDragMove = (event) => {
  const nextPoint = {
    left: event.clientX - dragState.value.offsetX,
    top: event.clientY - dragState.value.offsetY
  }
  const bounds = getViewportBounds()
  const clamped = clampPoint(nextPoint, bounds)
  panelPos.value = clamped
}

const stopDrag = () => {
  dragState.value = { offsetX: 0, offsetY: 0 }
  window.removeEventListener('mousemove', onDragMove)
  window.removeEventListener('mouseup', stopDrag)
}

const updateLayoutMetrics = () => {
  const sidebarEl = document.querySelector('.left-sidebar')
  const topbarEl = document.querySelector('.macos-topbar')
  const agentEl = document.querySelector('.right-sidebar')

  const sidebarWidth = Math.round(sidebarEl?.getBoundingClientRect().width ?? 240)
  const topbarHeight = Math.round(topbarEl?.getBoundingClientRect().height ?? 52)
  const agentWidthRaw = Math.round(agentEl?.getBoundingClientRect().width ?? 0)

  layoutMetrics.value = {
    sidebarWidth,
    topbarHeight,
    agentWidth: agentWidthRaw > 4 ? agentWidthRaw : 0
  }
}

const keepFloatingWindowsInViewport = () => {
  const panelBounds = getViewportBounds()
  panelPos.value = clampPoint(panelPos.value, panelBounds)
}

const onViewportResize = () => {
  updateLayoutMetrics()
  keepFloatingWindowsInViewport()
}

const onColorInput = (event) => {
  store.setToken(activeToken.value, event.target.value)
}

const onHexChange = (event) => {
  const raw = event.target.value.trim()
  const hex = raw.startsWith('#') ? raw : `#${raw}`
  if (/^#[0-9a-fA-F]{6}$/.test(hex)) {
    store.setToken(activeToken.value, hex)
  }
}

const onRadiusInput = (event) => {
  store.setToken(activeToken.value, Number(event.target.value))
}

const openImagePicker = () => {
  fileInput.value?.click()
}

const onFileChange = (event) => {
  const file = event.target.files?.[0]
  if (!file || !canUploadImage(activeToken.value)) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      let width = img.width
      let height = img.height
      
      // 限制最大宽高，避免图片体积过大导致 localStorage 爆满 (>5MB)
      const MAX_SIZE = 1920
      if (width > MAX_SIZE || height > MAX_SIZE) {
        if (width > height) {
          height = Math.round(height * (MAX_SIZE / width))
          width = MAX_SIZE
        } else {
          width = Math.round(width * (MAX_SIZE / height))
          height = MAX_SIZE
        }
      }
      
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)
      
      // 压缩为 webp 格式（或者 jpeg），质量 0.85
      const dataUrl = canvas.toDataURL('image/webp', 0.85)
      
      store.setToken(getImageKey(activeToken.value), dataUrl)
    }
    img.src = e.target.result
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

const clearImage = () => {
  if (!canUploadImage(activeToken.value)) return
  store.setToken(getImageKey(activeToken.value), '')
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const getSwatchStyle = (key) => {
  if (TOKEN_META[key].type === 'radius') {
    return {
      background: '#e5e7eb',
      borderRadius: `${store.tokens[key]}px`
    }
  }

  return {
    background: store.tokens[key]
  }
}

const saveTheme = async () => {
  store.saveToStorage()

  const nowText = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  lastSavedSnapshot.value = serializeTokens()
  lastSavedAtText.value = nowText
  updateSaveStatusText()
  saveFeedbackText.value = `主题已保存 (${nowText})`

  if (saveToastTimer) {
    clearTimeout(saveToastTimer)
  }
  if (saveInlineTimer) {
    clearTimeout(saveInlineTimer)
  }
  if (saveButtonTimer) {
    clearTimeout(saveButtonTimer)
  }

  // Force message re-mount so repeated saves always show feedback.
  saveInlineVisible.value = false
  saveToastVisible.value = false
  await nextTick()

  saveInlineVisible.value = true
  saveButtonText.value = '已保存 ✓'
  saveToastVisible.value = true

  saveInlineTimer = setTimeout(() => {
    saveInlineVisible.value = false
  }, 2400)

  saveButtonTimer = setTimeout(() => {
    saveButtonText.value = '保存'
  }, 2200)

  saveToastTimer = setTimeout(() => {
    saveToastVisible.value = false
  }, 2400)

  console.log('[ThemeOverlay] Saved theme to localStorage', { ...store.tokens })
}

onMounted(async () => {
  await nextTick()
  updateLayoutMetrics()

  const savedSnapshot = readSavedSnapshot()
  lastSavedSnapshot.value = savedSnapshot || serializeTokens()
  updateSaveStatusText()

  // Place panel near the right side on first render.
  const panelWidth = panelRef.value?.offsetWidth ?? 280
  const initialLeft = Math.max(8, window.innerWidth - panelWidth - 14)
  panelPos.value = {
    ...panelPos.value,
    left: initialLeft
  }

  keepFloatingWindowsInViewport()
  window.addEventListener('resize', onViewportResize)
})

onBeforeUnmount(() => {
  stopDrag()
  window.removeEventListener('resize', onViewportResize)
  if (saveToastTimer) {
    clearTimeout(saveToastTimer)
  }
  if (saveInlineTimer) {
    clearTimeout(saveInlineTimer)
  }
  if (saveButtonTimer) {
    clearTimeout(saveButtonTimer)
  }
})
</script>

<style scoped>
.theme-overlay {
  position: fixed;
  inset: 0;
  z-index: 70;
  pointer-events: none;
}

.ov-btn {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 6px;
  background: #ffffff;
  color: #111827;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.ov-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.ov-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ov-btn-save {
  background: #16a34a;
  border-color: #16a34a;
  color: #ffffff;
}

.ov-btn-save:hover {
  background: #15803d;
}

.ov-btn-danger {
  color: #dc2626;
  border-color: #dc2626;
}

.ov-btn-danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

.zone {
  pointer-events: auto;
  position: fixed;
  z-index: 90;
  border: 2px dashed rgba(0, 122, 255, 0.5);
  background: rgba(0, 122, 255, 0.08);
  color: #0f3d80;
  font-size: 12px;
  font-weight: 700;
  border-radius: 8px;
  cursor: pointer;
}

.zone:hover {
  background: rgba(0, 122, 255, 0.16);
}

.zone.active {
  border-color: #007aff;
  background: rgba(0, 122, 255, 0.22);
}

.zone-topbar {
  justify-content: flex-start;
  text-align: left;
  padding-left: 14px;
}

.edit-panel {
  pointer-events: auto;
  position: fixed;
  z-index: 130;
  width: 320px;
  max-height: 80vh;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(8px);
  padding: 10px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
  overflow-y: auto;
}

.panel-header {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  cursor: grab;
  user-select: none;
}

.drag-handle:active {
  cursor: grabbing;
}

.panel-main-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #111827;
  display: flex;
  align-items: center;
  gap: 6px;
}

.title-icon {
  width: 16px;
  height: 16px;
  color: #6b7280;
  flex-shrink: 0;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.save-state {
  margin-top: 2px;
  margin-bottom: 4px;
  font-size: 11px;
  color: #4b5563;
  font-weight: 600;
}

.save-inline {
  margin-top: 2px;
  margin-bottom: 6px;
  border: 1px solid rgba(22, 163, 74, 0.35);
  background: rgba(22, 163, 74, 0.12);
  color: #166534;
  border-radius: 7px;
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 600;
}

.panel-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
}

.drag-hint {
  font-size: 10px;
  color: #6b7280;
}

.panel-desc {
  margin: 2px 0 8px;
  font-size: 11px;
  color: #6b7280;
}

.field-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 4px;
  margin-top: 8px;
}

.field-label:first-of-type {
  margin-top: 0;
}

.picker-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.native-picker {
  width: 40px;
  height: 32px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 6px;
  background: #ffffff;
  padding: 0;
}

.hex-input {
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 11px;
  font-family: Menlo, Monaco, Consolas, monospace;
}

.radius-input {
  width: 100%;
  margin-bottom: 8px;
}

.upload-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.upload-btn {
  padding: 4px 8px;
}

.image-input {
  display: none;
}

.upload-hint {
  margin: 0 0 8px;
  font-size: 10px;
  color: #6b7280;
  line-height: 1.4;
}

.quick-tokens {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.quick-token {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 4px 6px;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 2px;
  font-size: 10px;
  color: #111827;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-token:hover {
  background: rgba(0, 0, 0, 0.02);
}

.quick-token.selected {
  border-color: #007aff;
  background: rgba(0, 122, 255, 0.1);
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.save-toast {
  pointer-events: none;
  position: fixed;
  z-index: 140;
  left: 50%;
  bottom: 18px;
  transform: translateX(-50%);
  background: rgba(22, 163, 74, 0.95);
  color: #ffffff;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

@media (max-width: 980px) {
  .edit-panel {
    width: 280px;
  }
}
</style>
