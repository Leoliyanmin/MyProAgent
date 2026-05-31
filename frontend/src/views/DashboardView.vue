<template>
  <div class="dashboard-engine">
    <div class="dashboard-toolbar">
      <h2 class="view-title">工作台概览</h2>
      <div class="toolbar-actions">
        <select
          class="preset-select"
          :value="activePresetKey"
          @change="handlePresetChange"
        >
          <option value="">布局模板</option>
          <option v-for="p in dashboardStore.namedPresets" :key="p.key" :value="p.key">{{ p.name }}</option>
        </select>
        <button class="mac-btn-secondary" @click="autoArrangeDashboard">
          自动整理
        </button>
        <template v-if="isEditing">
          <button v-if="!showPresetName" class="mac-btn-secondary" @click="startPresetSave">保存为模板</button>
          <template v-else>
            <input v-model="presetName" class="preset-name-input" placeholder="模板名称" @keydown.enter="commitPreset" @keydown.escape="cancelPreset" />
            <button class="mac-btn-primary mac-btn-sm" @click="commitPreset">确认</button>
          </template>
        </template>
        <button class="mac-btn-primary" :class="{ 'is-active': isEditing }" @click="toggleEditMode">
          {{ isEditing ? '保存布局配置' : '自定义布局' }}
        </button>
      </div>
    </div>

    <div class="grid-wrapper">
      <grid-layout v-model:layout="layoutConfig" :col-num="12" :row-height="50" :is-draggable="isEditing"
        :is-resizable="isEditing" :vertical-compact="true" :margin="[16, 16]" :use-css-transforms="true">
        <grid-item v-for="item in layoutConfig" :key="item.i" :x="item.x" :y="item.y" :w="item.w" :h="item.h"
          :i="item.i" :min-w="item.minW" :min-h="item.minH" :max-w="item.maxW" :max-h="item.maxH"
          class="mac-panel grid-item"
          :class="{ 'editing-mode': isEditing, 'heatmap-grid-item': item.type === 'heatmap' }"
          @resized="onItemResized">
          <div class="widget-content">
            <component :is="getComponentByType(item.type)" v-bind="getWidgetProps(item)" />
          </div>

          <div v-if="isEditing" class="drag-overlay">
            <span class="overlay-text">{{ item.type }}</span>
          </div>
        </grid-item>
      </grid-layout>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import VueGridLayout from 'vue3-grid-layout'
import { getHeatmapLayoutPreset, useDashboardStore } from '../stores/dashboard'

const { GridLayout, GridItem } = VueGridLayout

import WidgetTodo from '../components/widgets/WidgetTodo.vue'
import WidgetMessages from '../components/widgets/WidgetMessages.vue'
import WidgetMarkdownEditor from '../components/widgets/WidgetMarkdownEditor.vue'
import ComposeMini from '../components/mini/ComposeMini.vue'
import WidgetHeatmap from '../components/widgets/WidgetHeatmap.vue'
import AgentMini from '../components/mini/AgentMini.vue'

const componentMap = {
  'todo': WidgetTodo,
  'messages': WidgetMessages,
  'markdown': WidgetMarkdownEditor,
  'compose-mini': ComposeMini,
  'heatmap': WidgetHeatmap,
  'agent-mini': AgentMini
}

const getComponentByType = (type) => componentMap[type]

const getWidgetProps = (item) => {
  if (item.type !== 'heatmap') return {}
  return { heatmapVariant: item.heatmapVariant || 'wide' }
}

const dashboardStore = useDashboardStore()
const layoutConfig = dashboardStore.layoutConfig

const isEditing = ref(false)
const showPresetName = ref(false)
const presetName = ref('')
const activePresetKey = ref('')

const toggleEditMode = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) {
    snapHeatmapLayouts()
    dashboardStore.saveLayout()
  }
}

const autoArrangeDashboard = () => {
  snapHeatmapLayouts()
  dashboardStore.autoArrangeLayout()
}

const startPresetSave = () => {
  presetName.value = ''
  showPresetName.value = true
}

const commitPreset = () => {
  const name = presetName.value.trim()
  if (!name) { showPresetName.value = false; return }
  snapHeatmapLayouts()
  dashboardStore.saveCurrentLayoutAsPreset(name)
  activePresetKey.value = '' // reset dropdown
  showPresetName.value = false
}

const cancelPreset = () => {
  showPresetName.value = false
  presetName.value = ''
}

const handlePresetChange = (e) => {
  const key = e.target.value
  if (!key) return
  dashboardStore.applyPreset(key)
  activePresetKey.value = '' // reset to placeholder after applying
}

const applyHeatmapPreset = (item, width = item.w, height = item.h) => {
  if (!item || item.type !== 'heatmap') return

  const preset = getHeatmapLayoutPreset(Number(width) || item.w, Number(height) || item.h)
  item.w = preset.w
  item.h = preset.h
  item.minW = 2
  item.minH = 1
  item.maxW = 12
  item.maxH = 2
  item.heatmapVariant = preset.name
}

const snapHeatmapLayouts = () => {
  layoutConfig.forEach(item => applyHeatmapPreset(item))
}

const onItemResized = (itemId, newHeight, newWidth) => {
  const item = layoutConfig.find(entry => entry.i === itemId)
  if (!item || item.type !== 'heatmap') return

  applyHeatmapPreset(item, newWidth, newHeight)
  dashboardStore.saveLayout()
}

// Ensure markdown widget is present in layout (Pinia auto-unwraps refs)
onMounted(() => {
  const cfg = dashboardStore.layoutConfig
  snapHeatmapLayouts()
  const hasMarkdown = cfg.some(item => item.type === 'markdown')
  if (!hasMarkdown) {
    cfg.push({
      x: 0, y: 5, w: 12, h: 8, i: '5', type: 'markdown', minW: 6, minH: 4
    })
  }
  dashboardStore.saveLayout()
  dashboardStore.syncActivityLog()
})

onUnmounted(() => {
  dashboardStore.cleanupActivitySync()
})
</script>

<style scoped>
.dashboard-engine {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dashboard-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}



.view-title {
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.mac-btn-primary {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.mac-btn-secondary {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
}

.mac-btn-secondary:hover {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.2);
}

.mac-btn-primary.is-active {
  background: #007aff;
  color: #ffffff;
  border-color: #007aff;
}

.preset-select {
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 12px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  outline: none;
  max-width: 130px;
}
.preset-select:focus { border-color: #007aff; }

.preset-name-input {
  border: 1px solid rgba(0,0,0,0.15);
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 12px;
  outline: none;
  width: 110px;
  font-family: inherit;
}
.preset-name-input:focus { border-color: #007aff; }

.mac-btn-sm { font-size: 12px; padding: 5px 10px; }

/* 网格容器需自适应剩余高度并允许内部溢出计算 */
.grid-wrapper {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  margin: -16px;
}

/* 统一面板外观 */
.mac-panel {
  background: var(--clr-bg-card, #ffffff);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-clip: padding-box;
}

.widget-content {
  width: 100%;
  height: 100%;
}

.heatmap-grid-item,
.heatmap-grid-item .widget-content {
  overflow: visible;
}

/* 编辑模式视觉增强 */
.grid-item.editing-mode {
  border: 1.5px dashed #007aff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: grab;
}

.grid-item.editing-mode:active {
  cursor: grabbing;
}

.drag-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(2px);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.overlay-text {
  font-size: 14px;
  font-weight: 600;
  color: #007aff;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* =========================================
 * 终极修复：拖拽手柄样式 (使用 !important 强制覆盖底层库)
 * ========================================= */
:deep(.vue-resizable-handle) {
  width: 16px !important;
  height: 16px !important;
  /* 强制干掉默认的红色/蓝色背景图 */
  background: none !important; 
  border-right: 3px solid rgba(0, 0, 0, 0.15) !important;
  border-bottom: 3px solid rgba(0, 0, 0, 0.15) !important;
  border-radius: 2px !important;
  right: 6px !important;
  bottom: 6px !important;
  opacity: 0;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* 只有在编辑模式下才显示手柄 */
.grid-item.editing-mode :deep(.vue-resizable-handle) {
  opacity: 1;
}

/* 鼠标悬浮或拖动时的极简次级灰反馈 */
.grid-item.editing-mode :deep(.vue-resizable-handle:hover),
.grid-item.editing-mode :deep(.vue-resizable-handle:active) {
  border-right-color: #86868b !important; 
  border-bottom-color: #86868b !important;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15)); 
  transform: scale(1.1); 
  cursor: se-resize !important;
}
:deep(.vue-grid-item.vue-grid-placeholder) {
  /* 替换掉默认的刺眼红色，改为 macOS 风格的柔和灰底 */
  background: rgba(0, 0, 0, 0.04) !important; 
  /* 增加精致的虚线边框指示 */
  border: 1.5px dashed rgba(0, 0, 0, 0.2) !important; 
  /* 保持与你的卡片一样的圆角 */
  border-radius: 12px !important; 
  /* 覆盖默认的透明度，让边框更清晰 */
  opacity: 1 !important; 
  /* 去掉多余的阴影干扰 */
  box-shadow: none !important; 
}
</style>
