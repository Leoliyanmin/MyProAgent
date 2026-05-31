<template>
  <div class="dashboard-engine">
    <div class="dashboard-toolbar">
      <h2 class="view-title">工作台概览</h2>
      <div class="toolbar-actions">
        <!-- Custom preset dropdown -->
        <div class="preset-dropdown" ref="presetDropdownRef">
          <button class="preset-trigger" @click="showPresetMenu = !showPresetMenu">
            <span class="preset-trigger-text">{{ dashboardStore.activePresetName }}</span>
            <svg class="preset-trigger-arrow" :class="{ open: showPresetMenu }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <div v-if="showPresetMenu" class="preset-menu">
            <div
              v-for="p in dashboardStore.namedPresets"
              :key="p.key"
              class="preset-menu-item"
              :class="{ active: p.key === dashboardStore.activePresetKey }"
              @click="selectPreset(p.key)"
            >
              <span class="preset-menu-name">{{ p.name }}</span>
              <button
                class="preset-delete-btn"
                :class="{ disabled: dashboardStore.namedPresets.length <= 1 }"
                @click.stop="handleDeletePreset(p.key)"
                :title="dashboardStore.namedPresets.length <= 1 ? '至少保留一个模板' : '删除模板'"
              >×</button>
            </div>
            <div class="preset-menu-add" @click="handleAddPreset">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              <span>新建模板</span>
            </div>
          </div>
        </div>
        <template v-if="showNewPresetInput">
          <input v-model="newPresetName" class="preset-name-input" placeholder="模板名称" @keydown.enter="commitNewPreset" @keydown.escape="cancelNewPreset" ref="presetNameInputRef" />
          <button class="mac-btn-primary mac-btn-sm" @click="commitNewPreset">确认</button>
        </template>
        <button class="mac-btn-secondary" @click="autoArrangeDashboard">
          自动整理
        </button>
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
            <button class="widget-remove-btn" @click.stop="removeWidget(item)" title="移除此组件">×</button>
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
const showPresetMenu = ref(false)
const showNewPresetInput = ref(false)
const newPresetName = ref('')
const presetDropdownRef = ref(null)

const toggleEditMode = () => {
  isEditing.value = !isEditing.value
  if (isEditing.value) {
    snapHeatmapLayouts()
  } else {
    snapHeatmapLayouts()
    dashboardStore.saveCurrentLayoutAsPreset(dashboardStore.activePresetName)
    dashboardStore.saveLayout()
  }
}

const autoArrangeDashboard = () => {
  snapHeatmapLayouts()
  dashboardStore.autoArrangeLayout()
}

const selectPreset = (key) => {
  dashboardStore.applyPreset(key)
  showPresetMenu.value = false
}

const handleDeletePreset = (key) => {
  if (dashboardStore.namedPresets.length <= 1) return
  dashboardStore.deletePreset(key)
}

const handleAddPreset = () => {
  showNewPresetInput.value = true
  newPresetName.value = ''
}

const commitNewPreset = () => {
  const name = newPresetName.value.trim()
  if (!name) { showNewPresetInput.value = false; return }
  dashboardStore.createNewPreset(name)
  showNewPresetInput.value = false
}

const cancelNewPreset = () => {
  showNewPresetInput.value = false
}

const TYPE_TO_MINI = {
  todo: 'todo', messages: 'inbox', markdown: 'note',
  heatmap: 'heatmap', 'compose-mini': 'compose', 'agent-mini': 'agent',
}

const removeWidget = (item) => {
  const idx = layoutConfig.findIndex(it => it.i === item.i)
  if (idx === -1) return
  layoutConfig.splice(idx, 1)
  const miniType = TYPE_TO_MINI[item.type]
  if (miniType) dashboardStore.miniWidgets.delete(miniType)
  dashboardStore.saveLayout()
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
  dashboardStore.ensureDefaultPreset()
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

.preset-dropdown { position: relative; }

.preset-trigger {
  display: flex; align-items: center; gap: 4px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 12px;
  color: #374151;
  background: #fff;
  cursor: pointer;
  outline: none;
  font-family: inherit;
  font-weight: 500;
  min-width: 90px;
}
.preset-trigger:hover { border-color: rgba(0,0,0,0.25); }
.preset-trigger-text { white-space: nowrap; max-width: 90px; overflow: hidden; text-overflow: ellipsis; }
.preset-trigger-arrow { flex-shrink: 0; color: rgba(0,0,0,0.3); transition: transform 0.15s; }
.preset-trigger-arrow.open { transform: rotate(180deg); }

.preset-menu {
  position: absolute; top: 100%; left: 0; margin-top: 4px;
  background: #fff; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  min-width: 150px; z-index: 100; overflow: hidden;
}
.preset-menu-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; font-size: 13px; cursor: pointer;
  transition: background 0.1s;
}
.preset-menu-item:hover { background: rgba(0,0,0,0.03); }
.preset-menu-item.active { background: rgba(0,122,255,0.06); font-weight: 600; color: #007aff; }
.preset-menu-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.preset-delete-btn {
  background: none; border: none; font-size: 16px; color: rgba(0,0,0,0.2);
  cursor: pointer; padding: 0 4px; line-height: 1; flex-shrink: 0;
  border-radius: 3px; transition: all 0.1s;
}
.preset-menu-item:hover .preset-delete-btn { color: rgba(0,0,0,0.4); }
.preset-delete-btn:hover { color: #ff3b30 !important; background: rgba(255,59,48,0.06); }
.preset-delete-btn.disabled { color: rgba(0,0,0,0.1); cursor: not-allowed; }
.preset-delete-btn.disabled:hover { color: rgba(0,0,0,0.1) !important; background: none; }

.preset-menu-add {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 12px; font-size: 12px; color: #007aff;
  border-top: 1px solid rgba(0,0,0,0.05);
  cursor: pointer; transition: background 0.1s;
}
.preset-menu-add:hover { background: rgba(0,122,255,0.04); }

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

.widget-remove-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 59, 48, 0.85);
  color: #fff;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  pointer-events: auto;
  z-index: 20;
}
.widget-remove-btn:hover {
  background: #ff3b30;
  transform: scale(1.1);
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
