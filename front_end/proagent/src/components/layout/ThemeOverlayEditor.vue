<template>
  <div class="theme-overlay" aria-label="主题覆盖编辑模式">
    <div class="overlay-toolbar">
      <div class="toolbar-title-wrap">
        <h3 class="toolbar-title">外观编辑模式</h3>
        <p class="toolbar-subtitle">直接点击界面区域进行配色编辑，效果实时预览</p>
      </div>
      <div class="toolbar-actions">
        <button class="ov-btn" :disabled="!store.canUndo" @click="store.undo()">撤销</button>
        <button class="ov-btn" :disabled="!store.canRedo" @click="store.redo()">重做</button>
        <button class="ov-btn ov-btn-danger" @click="store.reset()">重置</button>
        <button class="ov-btn ov-btn-save" @click="saveTheme">保存</button>
        <button class="ov-btn" @click="emit('exit')">退出编辑</button>
      </div>
    </div>

    <button
      class="zone zone-sidebar"
      :class="{ active: activeToken === 'bgSidebar' }"
      @click="selectToken('bgSidebar')"
      type="button"
    >
      侧边栏
    </button>

    <button
      class="zone zone-topbar"
      :class="{ active: activeToken === 'bgTopbar' }"
      @click="selectToken('bgTopbar')"
      type="button"
    >
      顶栏
    </button>

    <button
      class="zone zone-content"
      :class="{ active: activeToken === 'bgContent' }"
      @click="selectToken('bgContent')"
      type="button"
    >
      内容区
    </button>

    <div class="edit-panel" v-if="activeToken">
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

      <template v-else>
        <label class="field-label">圆角 {{ store.tokens[activeToken] }}px</label>
        <input
          class="radius-input"
          type="range"
          min="0"
          max="24"
          step="1"
          :value="store.tokens[activeToken]"
          @input="onRadiusInput"
        />
      </template>

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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useThemeStore } from '../../stores/theme.js'

const emit = defineEmits(['exit'])
const store = useThemeStore()
const activeToken = ref('bgContent')

const TOKEN_META = {
  bgSidebar: { label: '侧边栏背景', desc: '左侧导航区域背景色', type: 'color' },
  bgTopbar: { label: '顶栏背景', desc: '顶部标签栏背景色', type: 'color' },
  bgContent: { label: '内容区背景', desc: '主内容区域背景色', type: 'color' },
  bgCard: { label: '卡片背景', desc: '卡片容器背景色', type: 'color' },
  accent: { label: '主色调', desc: '按钮和高亮颜色', type: 'color' },
  textPrimary: { label: '主文本', desc: '标题与正文主文本色', type: 'color' },
  textMuted: { label: '次文本', desc: '说明和辅助文案颜色', type: 'color' },
  borderColor: { label: '边框色', desc: '边框和分隔线颜色', type: 'color' },
  cardRadius: { label: '卡片圆角', desc: '卡片圆角半径', type: 'radius' }
}

const quickKeys = [
  'bgSidebar',
  'bgTopbar',
  'bgContent',
  'bgCard',
  'accent',
  'textPrimary',
  'textMuted',
  'borderColor',
  'cardRadius'
]

const selectToken = (key) => {
  activeToken.value = key
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

const saveTheme = () => {
  console.log('[ThemeOverlay] save draft', { ...store.tokens })
}
</script>

<style scoped>
.theme-overlay {
  position: fixed;
  inset: 0;
  z-index: 70;
  pointer-events: none;
}

.overlay-toolbar {
  pointer-events: auto;
  position: fixed;
  top: 12px;
  left: 252px;
  right: 12px;
  min-height: 56px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  gap: 8px;
}

.toolbar-title {
  margin: 0;
  font-size: 15px;
  color: #111827;
}

.toolbar-subtitle {
  margin: 2px 0 0;
  font-size: 12px;
  color: #6b7280;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.ov-btn {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 7px;
  background: #ffffff;
  color: #111827;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  cursor: pointer;
}

.ov-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ov-btn-save {
  background: #16a34a;
  border-color: #16a34a;
  color: #ffffff;
}

.ov-btn-danger {
  color: #dc2626;
  border-color: #dc2626;
}

.zone {
  pointer-events: auto;
  position: fixed;
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

.zone-sidebar {
  top: 76px;
  left: 0;
  width: 240px;
  bottom: 0;
}

.zone-topbar {
  top: 76px;
  left: 240px;
  right: 0;
  height: 52px;
}

.zone-content {
  top: 128px;
  left: 240px;
  right: 0;
  bottom: 0;
}

.edit-panel {
  pointer-events: auto;
  position: fixed;
  top: 86px;
  right: 14px;
  width: 300px;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(8px);
  padding: 12px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
}

.panel-title {
  margin: 0;
  font-size: 14px;
  color: #111827;
}

.panel-desc {
  margin: 4px 0 10px;
  font-size: 12px;
  color: #6b7280;
}

.field-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 6px;
}

.picker-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.native-picker {
  width: 46px;
  height: 36px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 8px;
  background: #ffffff;
  padding: 0;
}

.hex-input {
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  font-family: Menlo, Monaco, Consolas, monospace;
}

.radius-input {
  width: 100%;
}

.quick-tokens {
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  max-height: 250px;
  overflow-y: auto;
}

.quick-token {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 6px 8px;
  background: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #111827;
  cursor: pointer;
}

.quick-token.selected {
  border-color: #007aff;
  background: rgba(0, 122, 255, 0.08);
}

.swatch {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 1px solid rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

@media (max-width: 980px) {
  .overlay-toolbar {
    left: 8px;
  }

  .zone-sidebar {
    width: 200px;
  }

  .zone-topbar,
  .zone-content {
    left: 200px;
  }

  .edit-panel {
    width: 260px;
  }
}
</style>
