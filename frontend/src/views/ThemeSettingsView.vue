<template>
  <div class="theme-editor">

    <!-- ── 顶部部操作栏 ── -->
    <header class="te-header">
      <div>
        <h1 class="te-title">主题设置</h1>
        <p class="te-subtitle">{{ isEditing ? '编辑模式：点击色块选择区域，再用调色盘修改颜色' : '查看当前主题配色，点击「进入编辑」开始自定义' }}</p>
      </div>
      <div class="te-actions">
        <button class="te-btn" :class="{ 'te-btn--active': isEditing }" @click="toggleEditMode">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 20h9"/>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/>
          </svg>
          {{ isEditing ? '退出编辑' : '进入编辑' }}
        </button>
        <template v-if="isEditing">
          <button class="te-btn" :disabled="!store.canUndo" @click="store.undo()">↩ 撤销</button>
          <button class="te-btn" :disabled="!store.canRedo" @click="store.redo()">↪ 重做</button>
          <button class="te-btn te-btn--danger" @click="store.reset()">重置默认</button>
          <button class="te-btn te-btn--save" @click="saveTheme">保存主题</button>
        </template>
      </div>
    </header>

    <!-- ── 主工作区（左：预览 / 右：属性面板）── -->
    <div class="te-workspace">

      <!-- 左侧：布局示意图 -->
      <div class="te-preview-col">
        <p class="col-label">布局预览</p>

        <div class="schematic" :style="{ backgroundColor: store.tokens.bgApp, backgroundImage: store.tokens.bgAppImage ? `url(${store.tokens.bgAppImage})` : 'none', backgroundSize: 'cover' }">

          <!-- 侧边栏 zone -->
          <div
            class="sch-sidebar zone"
            :class="zoneClasses('bgSidebar')"
            :style="{ backgroundColor: store.tokens.bgSidebar, backgroundImage: store.tokens.bgSidebarImage ? `url(${store.tokens.bgSidebarImage})` : 'none', backgroundSize: 'cover' }"
            @click="pickZone('bgSidebar')"
          >
            <div class="sch-logo"></div>
            <div class="sch-navitem"></div>
            <div class="sch-navitem sch-navitem--dim"></div>
            <div class="sch-navitem sch-navitem--dim"></div>
            <div class="sch-spacer"></div>
            <div class="sch-avatar"></div>
          </div>

          <!-- 中间主列 -->
          <div class="sch-main">
            <!-- 顶栏 zone -->
            <div
              class="sch-topbar zone"
              :class="zoneClasses('bgTopbar')"
              :style="{ backgroundColor: store.tokens.bgTopbar, backgroundImage: store.tokens.bgTopbarImage ? `url(${store.tokens.bgTopbarImage})` : 'none', backgroundSize: 'cover' }"
              @click="pickZone('bgTopbar')"
            >
              <div class="sch-segment"></div>
              <div class="sch-segment sch-segment--ghost"></div>
            </div>

            <!-- 内容区 zone -->
            <div
              class="sch-content zone"
              :class="zoneClasses('bgContent')"
              :style="{ backgroundColor: store.tokens.bgContent, backgroundImage: store.tokens.bgContentImage ? `url(${store.tokens.bgContentImage})` : 'none', backgroundSize: 'cover' }"
              @click="pickZone('bgContent')"
            >
              <!-- 简化的内容占位 -->
              <div class="sch-content-placeholder"></div>
              <div class="sch-content-placeholder"></div>
            </div>
          </div>

          <!-- Agent 侧边栏 zone -->
          <div
            class="sch-agent zone"
            :class="zoneClasses('bgAgent')"
            :style="{ backgroundColor: store.tokens.bgAgent, backgroundImage: store.tokens.bgAgentImage ? `url(${store.tokens.bgAgentImage})` : 'none', backgroundSize: 'cover' }"
            @click="pickZone('bgAgent')"
          >
            <div class="sch-agent-header"></div>
            <div class="sch-agent-body">
              <div class="sch-agent-line"></div>
              <div class="sch-agent-line sch-agent-line--short"></div>
            </div>
          </div>

        </div>

        <!-- 实时效果预览 -->
        <p class="col-label" style="margin-top: 16px;">实时效果预览</p>
        <div class="live-preview-container">
          <div
            class="live-preview"
            :style="{
              backgroundColor: store.tokens.bgApp,
              fontFamily: '-apple-system, BlinkMacSystemFont, SF Pro Text, sans-serif'
            }"
          >
            <!-- 模拟顶部栏 -->
            <div
              class="preview-header"
              :style="{
                backgroundColor: store.tokens.bgTopbar
              }"
            ></div>

            <!-- 模拟侧边栏 -->
            <div
              class="preview-sidebar"
              :style="{
                backgroundColor: store.tokens.bgSidebar
              }"
            ></div>

            <!-- 模拟内容区 -->
            <div
              class="preview-content"
              :style="{ backgroundColor: store.tokens.bgContent }"
            ></div>

            <!-- 模拟 Agent 侧边栏 -->
            <div
              class="preview-agent"
              :style="{
                backgroundColor: store.tokens.bgAgent
              }"
            ></div>
          </div>
        </div>

      </div>

      <!-- 右侧：属性面板 -->
      <div class="te-panel-col">
        <p class="col-label">属性面板</p>

        <!-- 编辑模式 · 未选中 -->
        <div v-if="isEditing && !activeZone" class="panel-empty">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 1 1 3.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
          </svg>
          <p>点击左侧预览中的任意区域开始编辑</p>
        </div>

        <!-- 编辑模式 · 已选中 -->
        <div v-else-if="isEditing && activeZone" class="panel-editor">
          <h3 class="panel-zone-title">{{ META[activeZone].label }}</h3>
          <p class="panel-zone-desc">{{ META[activeZone].desc }}</p>

          <!-- 颜色类型 -->
          <template v-if="META[activeZone].type === 'color'">
            <p class="field-label">调色盘</p>
            <div class="color-editor-row">
              <!-- 大色块 + 点击打开系统调色盘 -->
              <label class="color-picker-wrap">
                <div class="color-big-swatch" :style="{ background: store.tokens[activeZone] }"></div>
                <input
                  type="color"
                  class="hidden-color-input"
                  :value="store.tokens[activeZone]"
                  @input="e => store.setToken(activeZone, e.target.value)"
                />
              </label>
              <span class="color-picker-hint">点击色块<br>打开系统调色盘</span>
            </div>

            <p class="field-label" style="margin-top: 12px;">Hex 值</p>
            <div class="hex-row">
              <input
                class="hex-input"
                type="text"
                :value="store.tokens[activeZone]"
                @change="e => onHexChange(e.target.value)"
                placeholder="#007aff"
                spellcheck="false"
              />
              <div class="current-swatch" :style="{ background: store.tokens[activeZone] }"></div>
            </div>
          </template>

          <!-- 圆角类型 -->
          <template v-if="META[activeZone].type === 'radius'">
            <p class="field-label">圆角大小：{{ store.tokens[activeZone] }}px</p>
            <input
              type="range"
              class="radius-slider"
              min="0" max="24" step="1"
              :value="store.tokens[activeZone]"
              @input="e => store.setToken(activeZone, Number(e.target.value))"
            />
            <div
              class="radius-preview"
              :style="{ borderRadius: store.tokens[activeZone] + 'px' }"
            ></div>
          </template>

          <!-- 支持上传背景图的区域 -->
          <template v-if="META[activeZone].canUpload">
            <p class="field-label" style="margin-top: 14px;">背景图片（可选）</p>
            <div style="display:flex; gap:8px;">
              <div class="upload-btn" @click="$refs.fileInput.click()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                上传图片
              </div>
              <div v-if="store.tokens[activeZone + 'Image']" class="upload-btn" style="color:#dc2626; border-color:#dc2626;" @click="clearImage">
                清除图片
              </div>
            </div>
            <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp,image/gif" style="display:none" @change="onFileChange" />
            <p v-if="store.tokens[activeZone + 'Image']" class="upload-hint">已插入背景图片，保存后生效。</p>
          </template>
        </div>

        <!-- 查看模式：配色汇总 -->
        <div v-else class="panel-summary">
          <ul class="token-list">
            <li v-for="(meta, key) in META" :key="key" class="token-row">
              <div
                class="token-swatch"
                :style="meta.type === 'color'
                  ? { background: store.tokens[key] }
                  : { background: '#e5e7eb' }"
              ></div>
              <div>
                <p class="token-label">{{ meta.label }}</p>
                <p class="token-val">{{ store.tokens[key] }}{{ meta.type === 'radius' ? 'px' : '' }}</p>
              </div>
            </li>
          </ul>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useThemeStore } from '../stores/theme.js'

const store = useThemeStore()

const META = {
  bgSidebar:   { label: '侧边栏背景',      desc: '左侧导航栏背景色',                 type: 'color',  canUpload: false },
  bgTopbar:    { label: '顶栏背景',        desc: '顶部页签栏背景色',                 type: 'color',  canUpload: false },
  bgContent:   { label: '内容区背景',      desc: '中间主体内容区域背景色',           type: 'color',  canUpload: true  },
  bgAgent:     { label: 'Agent背景',       desc: 'AI助手侧边栏背景色',               type: 'color',  canUpload: false },
}

const isEditing  = ref(false)
const activeZone = ref(null)
const uploadedName = ref('')
const fileInput  = ref(null)

const zoneClasses = (key) => ({
  'zone--hoverable': isEditing.value,
  'zone--active':    activeZone.value === key,
})

const pickZone = (key) => {
  if (!isEditing.value) return
  activeZone.value = activeZone.value === key ? null : key
}

const toggleEditMode = () => {
  isEditing.value = !isEditing.value
  if (!isEditing.value) activeZone.value = null
}

const onHexChange = (value) => {
  const hex = value.startsWith('#') ? value : '#' + value
  if (/^#[0-9a-fA-F]{6}$/.test(hex)) {
    store.setToken(activeZone.value, hex)
  }
}

const onFileChange = (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    store.setToken(activeZone.value + 'Image', String(reader.result || ''))
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

const clearImage = () => {
  store.setToken(activeZone.value + 'Image', '')
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const saveTheme = () => {
  // TODO: POST /theme/draft — persist to backend
  const payload = { ...store.tokens }
  console.log('[Theme] draft saved:', payload)
  isEditing.value  = false
  activeZone.value = null
}
</script>

<style scoped>
/* ── Shell ── */
.theme-editor {
  width: 100%;
  height: 100%;
  background: var(--clr-bg-card, #ffffff);
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

/* ── Header ── */
.te-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0,0,0,0.08);
  flex-shrink: 0;
  background: var(--clr-bg-topbar, #fafafa);
  flex-wrap: wrap;
  gap: 10px;
}

.te-title   { margin: 0; font-size: 18px; font-weight: 700; color: #111827; }
.te-subtitle { margin: 3px 0 0; font-size: 12px; color: #6b7280; }

.te-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.te-btn {
  border: 1px solid rgba(0,0,0,0.15);
  background: #fff;
  border-radius: 7px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background 0.15s, color 0.15s;
}
.te-btn:hover:not(:disabled) { background: #f5f5f7; }
.te-btn:disabled { opacity: 0.38; cursor: not-allowed; }
.te-btn--active { background: #007aff; color: #fff; border-color: #007aff; }
.te-btn--active:hover { background: #0069d9; }
.te-btn--danger { border-color: #dc2626; color: #dc2626; }
.te-btn--danger:hover { background: #fef2f2; }
.te-btn--save   { background: #16a34a; color: #fff; border-color: #16a34a; }
.te-btn--save:hover { background: #15803d; }

/* ── Workspace ── */
.te-workspace {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 300px;
  overflow: hidden;
  min-height: 0;
}

.te-preview-col {
  padding: 16px;
  overflow-y: auto;
  border-right: 1px solid rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.te-panel-col {
  padding: 16px;
  overflow-y: auto;
}

.col-label {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(0,0,0,0.38);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ── Schematic app preview ── */
.schematic {
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.1);
  display: flex;
  height: 240px;
  overflow: hidden;
  transition: background 0.2s;
}

.sch-sidebar {
  width: 64px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 6px;
  gap: 6px;
  transition: background 0.2s;
}
.sch-logo { width: 22px; height: 22px; border-radius: 5px; background: rgba(0,0,0,0.12); margin-bottom: 4px; }
.sch-navitem { height: 7px; border-radius: 4px; width: 100%; transition: background 0.2s; }
.sch-navitem--dim { background: rgba(0,0,0,0.1) !important; }
.sch-spacer { flex: 1; }
.sch-avatar { width: 18px; height: 18px; border-radius: 50%; align-self: center; flex-shrink: 0; transition: background 0.2s; }

.sch-agent {
  width: 48px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 6px;
  gap: 6px;
  transition: background 0.2s;
  border-left: 1px solid rgba(0,0,0,0.07);
}
.sch-agent-header { height: 8px; border-radius: 4px; width: 100%; transition: background 0.2s; }
.sch-agent-body { flex: 1; display: flex; flex-direction: column; gap: 4px; padding-top: 4px; }
.sch-agent-line { height: 4px; border-radius: 2px; width: 100%; transition: background 0.2s; }
.sch-agent-line--short { width: 60%; }

.sch-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.sch-topbar {
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 8px;
  gap: 5px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
  transition: background 0.2s;
}
.sch-segment { height: 14px; width: 46px; border-radius: 4px; opacity: 0.85; transition: background 0.2s; }
.sch-segment--ghost { background: rgba(0,0,0,0.08) !important; }

.sch-content {
  flex: 1;
  padding: 6px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  align-content: start;
  transition: background 0.2s;
}

.sch-card {
  padding: 7px;
  border: 1px solid;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background 0.2s, border-radius 0.2s;
}
.sch-accent-bar { height: 3px; border-radius: 2px; width: 38%; transition: background 0.2s; }

/* 卡片内文字样式 */
.sch-card-title {
  font-size: 11px;
  font-weight: 600;
  transition: color 0.2s;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.sch-card-title:hover {
  background: rgba(0,0,0,0.05);
}

.sch-card-desc {
  font-size: 9px;
  transition: color 0.2s;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.sch-card-desc:hover {
  background: rgba(0,0,0,0.05);
}

/* 边框指示器 */
.border-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  cursor: pointer;
  opacity: 0.8;
  transition: transform 0.15s;
}

.border-indicator:hover {
  transform: scale(1.2);
}

/* 圆角指示器 */
.radius-indicator {
  position: absolute;
  bottom: 4px;
  right: 4px;
  font-size: 8px;
  padding: 2px 5px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
  transition: transform 0.15s;
}

.radius-indicator:hover {
  transform: scale(1.1);
}

/* 操作按钮 */
.action-btn {
  font-size: 9px;
  padding: 4px 10px;
  border-radius: 4px;
  color: #fff;
  text-align: center;
  cursor: pointer;
  transition: opacity 0.2s;
  margin-top: auto;
}

.action-btn:hover {
  opacity: 0.9;
}

.sch-card {
  position: relative;
}

.sch-line { height: 5px; border-radius: 3px; width: 80%; transition: background 0.2s; }
.sch-line--sm { height: 4px; width: 55%; opacity: 0.6; }

/* ── Zone interaction ── */
.zone { cursor: default; }
.zone.zone--hoverable           { cursor: pointer; }
.zone.zone--hoverable:hover     { outline: 2px solid rgba(0,122,255,0.5); outline-offset: 1px; }
.zone.zone--active              { outline: 2.5px solid #007aff; outline-offset: 1px; }

/* 内容区占位 */
.sch-content-placeholder {
  background: rgba(0,0,0,0.05);
  border-radius: 4px;
  min-height: 40px;
}

/* ── Live Preview ── */
.live-preview-container {
  background: #fff;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 12px;
  padding: 12px;
  overflow: hidden;
}

.live-preview {
  display: grid;
  grid-template-columns: 70px 1fr 50px;
  grid-template-rows: 40px 1fr;
  height: 280px;
  border-radius: 8px;
  overflow: hidden;
  font-size: 11px;
}

.preview-header {
  grid-column: 1 / -1;
  grid-row: 1;
}

.preview-sidebar {
  grid-row: 2;
  grid-column: 1;
}

.preview-content {
  grid-row: 2;
  grid-column: 2;
}

.preview-agent {
  grid-row: 2;
  grid-column: 3;
}

/* ── Panel states ── */
.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 160px;
  text-align: center;
  color: #6b7280;
  gap: 10px;
  font-size: 13px;
}

.panel-editor  { display: flex; flex-direction: column; gap: 8px; }
.panel-zone-title { margin: 0; font-size: 16px; font-weight: 700; color: #111827; }
.panel-zone-desc  { margin: 0; font-size: 13px; color: #6b7280; }
.field-label  { font-size: 12px; color: #4b5563; font-weight: 500; margin: 0; }

/* ── Color picker ── */
.color-editor-row { display: flex; align-items: center; gap: 14px; }
.color-picker-wrap {
  position: relative;
  display: inline-block;
  cursor: pointer;
}
.color-big-swatch {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: 2px solid rgba(0,0,0,0.1);
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  pointer-events: none;
  transition: transform 0.15s;
}
.color-picker-wrap:hover .color-big-swatch { transform: scale(1.04); }
.hidden-color-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
  border: none;
  padding: 0;
}
.color-picker-hint { font-size: 11px; color: #6b7280; line-height: 1.5; }

.hex-row { display: flex; gap: 8px; align-items: center; }
.hex-input {
  flex: 1;
  border: 1px solid rgba(0,0,0,0.15);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  font-family: 'SF Mono', 'Menlo', monospace;
  color: #111827;
}
.hex-input:focus { outline: none; border-color: #007aff; box-shadow: 0 0 0 3px rgba(0,122,255,0.15); }
.current-swatch { width: 28px; height: 28px; border-radius: 6px; border: 1px solid rgba(0,0,0,0.1); flex-shrink: 0; }

/* ── Radius slider ── */
.radius-slider { width: 100%; cursor: pointer; accent-color: #007aff; }
.radius-preview {
  width: 100%;
  height: 32px;
  border: 2px solid rgba(0,0,0,0.15);
  background: rgba(0,122,255,0.07);
  transition: border-radius 0.15s;
}

/* ── Upload ── */
.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border: 1.5px dashed rgba(0,0,0,0.2);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #4b5563;
  transition: all 0.15s;
}
.upload-btn:hover { border-color: #007aff; color: #007aff; background: rgba(0,122,255,0.04); }
.upload-hint { font-size: 12px; color: #16a34a; margin: 0; }

/* ── Summary token list ── */
.token-list { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 8px; }
.token-row  { display: flex; align-items: center; gap: 10px; }
.token-swatch { width: 20px; height: 20px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.1); flex-shrink: 0; }
.token-label  { margin: 0; font-size: 13px; font-weight: 500; color: #1d1d1f; }
.token-val    { margin: 0; font-size: 12px; color: #6b7280; font-family: 'SF Mono', 'Menlo', monospace; }
</style>
