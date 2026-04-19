<template>
  <div class="dashboard-engine">
    <div class="dashboard-toolbar">
      <h2 class="view-title">工作台概览</h2>
      <button class="mac-btn-primary" :class="{ 'is-active': isEditing }" @click="toggleEditMode">
        {{ isEditing ? '保存布局配置' : '自定义布局' }}
      </button>
    </div>

    <div class="grid-wrapper">
      <grid-layout v-model:layout="layoutConfig" :col-num="12" :row-height="50" :is-draggable="isEditing"
        :is-resizable="isEditing" :vertical-compact="true" :margin="[16, 16]" :use-css-transforms="true">
        <grid-item v-for="item in layoutConfig" :key="item.i" :x="item.x" :y="item.y" :w="item.w" :h="item.h"
          :i="item.i" :min-w="item.minW" :min-h="item.minH" class="mac-panel grid-item"
          :class="{ 'editing-mode': isEditing }">
          <div class="widget-content">
            <component :is="getComponentByType(item.type)" />
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
import { ref } from 'vue'
import VueGridLayout from 'vue3-grid-layout'

// 显式解构核心组件
const { GridLayout, GridItem } = VueGridLayout

// 1. 真实导入你刚才创建的小组件
import WidgetTodo from '../components/widgets/WidgetTodo.vue'
import WidgetMessages from '../components/widgets/WidgetMessages.vue'

// 2. 更新类型映射字典，指向真实的导入对象
const componentMap = {
  'todo': WidgetTodo,
  'messages': WidgetMessages
}

const getComponentByType = (type) => componentMap[type]

// 3. 核心状态：布局数据结构
// 在 DashboardView.vue 的 <script setup> 中修改 layoutConfig
const layoutConfig = ref([
  { x: 0, y: 0, w: 6, h: 5, i: '3', type: 'todo', minW: 3, minH: 4 },    // TODO 允许稍微窄一点
  { x: 6, y: 0, w: 6, h: 5, i: '4', type: 'messages', minW: 4, minH: 3 } // 消息列表
])
// 4. 编辑模式控制
const isEditing = ref(false)
const toggleEditMode = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) {
    console.log('Saved layout schema:', layoutConfig.value)
  }
}
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

.mac-btn-primary.is-active {
  background: #007aff;
  color: #ffffff;
  border-color: #007aff;
}

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

