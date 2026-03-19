<template>
  <div class="theme-editor">

    <!-- ── 底部操作栏 ── -->
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

        <div class="schematic" :style="{ background: store.tokens.bgApp }">

          <!-- 侧边栏 zone -->
          <div
            class="sch-sidebar zone"
            :class="zoneClasses('bgSidebar')"
            :style="{ background: store.tokens.bgSidebar }"
            @click="pickZone('bgSidebar')"
          >
            <div class="sch-logo"></div>
            <div class="sch-navitem" :style="{ background: store.tokens.accent }"></div>
            <div class="sch-navitem sch-navitem--dim"></div>
            <div class="sch-navitem sch-navitem--dim"></div>
            <div class="sch-spacer"></div>
            <div class="sch-avatar" :style="{ background: store.tokens.textMuted }"></div>
          </div>

          <!-- 右侧主列 -->
          <div class="sch-main">
            <!-- 顶栏 zone -->
            <div
              class="sch-topbar zone"
              :class="zoneClasses('bgTopbar')"
              :style="{ background: store.tokens.bgTopbar }"
              @click="pickZone('bgTopbar')"
            >
              <div class="sch-segment" :style="{ background: store.tokens.accent }"></div>
              <div class="sch-segment sch-segment--ghost"></div>
            </div>

            <!-- 内容区 zone -->
            <div
              class="sch-content zone"
              :class="zoneClasses('bgContent')"
              :style="{ background: store.tokens.bgContent }"
              @click="pickZone('bgContent')"
            >
              <!-- 卡片 zone（两张） -->
              <div
                class="sch-card zone"
                :class="zoneClasses('bgCard')"
                :style="{ background: store.tokens.bgCard, borderColor: store.tokens.borderColor, borderRadius: store.tokens.cardRadius + 'px' }"
                @click.stop="pickZone('bgCard')"
              >
                <div class="sch-line" :style="{ background: store.tokens.textPrimary }"></div>
                <div class="sch-line sch-line--sm" :style="{ background: store.tokens.textMuted }"></div>
                <div class="sch-line sch-line--sm" :style="{ background: store.tokens.textMuted }"></div>
              </div>
              <div
                class="sch-card zone"
                :class="zoneClasses('bgCard')"
                :style="{ background: store.tokens.bgCard, borderColor: store.tokens.borderColor, borderRadius: store.tokens.cardRadius + 'px' }"
                @click.stop="pickZone('bgCard')"
              >
                <div class="sch-accent-bar" :style="{ background: store.tokens.accent }"></div>
                <div class="sch-line" :style="{ background: store.tokens.textPrimary }"></div>
              </div>
            </div>
          </div>

        </div>

        <!-- 示意图下方：不在布局中的 token 色块 -->
        <p class="col-label" style="margin-top: 12px;">其他配色 Token</p>
        <div class="extra-tokens">
          <div
            v-for="key in EXTRA_KEYS"
            :key="key"
            class="extra-token zone"
            :class="zoneClasses(key)"
            @click="pickZone(key)"
          >
            <div
              class="extra-swatch"
              :style="META[key].type === 'color'
                ? { background: store.tokens[key] }
                : { background: '#e5e7eb' }"
            ></div>
            <span class="extra-label">{{ META[key].label }}</span>
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
            <div class="upload-btn" @click="$refs.fileInput.click()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              上传图片
            </div>
            <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/webp" style="display:none" @change="onFileChange" />
            <p v-if="uploadedName" class="upload-hint">已选：{{ uploadedName }}</p>
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
  accent:      { label: '主色调 / Accent', desc: '按钮、高亮、选中态等关键元素颜色', type: 'color',  canUpload: false },
  bgApp:       { label: '应用外层背景',    desc: '整个应用最底层的背景色',           type: 'color',  canUpload: true  },
  bgSidebar:   { label: '侧边栏背景',      desc: '左侧导航栏背景色',                 type: 'color',  canUpload: false },
  bgTopbar:    { label: '顶栏背景',        desc: '顶部页签栏背景色',                 type: 'color',  canUpload: false },
  bgContent:   { label: '内容区背景',      desc: '中间主体内容区域背景色',           type: 'color',  canUpload: true  },
  bgCard:      { label: '卡片背景',        desc: '各类卡片、面板的背景色',           type: 'color',  canUpload: false },
  textPrimary: { label: '主文本色',        desc: '标题、正文等主要文字颜色',         type: 'color',  canUpload: false },
  textMuted:   { label: '次要文本色',      desc: '描述、说明等较淡文字颜色',         type: 'color',  canUpload: false },
  borderColor: { label: '边框色',          desc: '线框、分割线、输入框边框颜色',     type: 'color',  canUpload: false },
  cardRadius:  { label: '卡片圆角',        desc: '卡片、面板的圆角半径（px）',       type: 'radius', canUpload: false },
}

// 在示意图里直接可见的 zone key
const EXTRA_KEYS = ['accent', 'bgApp', 'textPrimary', 'textMuted', 'borderColor', 'cardRadius']

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
  uploadedName.value = file.name
  // TODO: POST /assets/upload — integrate real upload endpoint
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
  background: #fff;
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
  background: #fafafa;
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
.sch-line { height: 5px; border-radius: 3px; width: 80%; transition: background 0.2s; }
.sch-line--sm { height: 4px; width: 55%; opacity: 0.6; }

/* ── Zone interaction ── */
.zone { cursor: default; }
.zone.zone--hoverable           { cursor: pointer; }
.zone.zone--hoverable:hover     { outline: 2px solid rgba(0,122,255,0.5); outline-offset: 1px; }
.zone.zone--active              { outline: 2.5px solid #007aff; outline-offset: 1px; }

/* ── Extra tokens row ── */
.extra-tokens {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.extra-token {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid rgba(0,0,0,0.1);
  border-radius: 8px;
  min-width: 60px;
  transition: border-color 0.15s, background 0.15s;
}
.extra-token.zone--hoverable:hover { border-color: rgba(0,122,255,0.5); background: rgba(0,122,255,0.04); }
.extra-token.zone--active          { border-color: #007aff; background: rgba(0,122,255,0.06); }
.extra-swatch { width: 26px; height: 26px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.12); }
.extra-label  { font-size: 10px; color: #4b5563; text-align: center; line-height: 1.3; }

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
