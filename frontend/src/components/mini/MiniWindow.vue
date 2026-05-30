<template>
  <Teleport to="body">
    <div
      ref="windowRef"
      class="mini-window"
      :style="windowStyle"
    >
      <!-- Drag handle header -->
      <div class="mini-header">
        <div class="drag-handle" @mousedown="startDrag">
          <slot name="title">{{ title }}</slot>
        </div>
        <button class="mini-close" @click="$emit('close')" title="关闭">✕</button>
      </div>

      <!-- Content -->
      <div class="mini-body">
        <slot />
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  width: { type: Number, default: 380 },
  height: { type: Number, default: 420 },
  positionKey: { type: String, required: true },
})

defineEmits(['close'])

const windowRef = ref(null)
const panelPos = ref({ left: 100, top: 100 })
const dragState = ref({ offsetX: 0, offsetY: 0 })

const loadPosition = () => {
  try {
    const saved = localStorage.getItem(`miniwin_pos_${props.positionKey}`)
    if (saved) {
      panelPos.value = JSON.parse(saved)
    } else {
      panelPos.value = {
        left: Math.max(20, (window.innerWidth - props.width) / 2),
        top: Math.max(20, (window.innerHeight - props.height) / 2),
      }
    }
  } catch { /* use default */ }
}

const savePosition = () => {
  try {
    localStorage.setItem(`miniwin_pos_${props.positionKey}`, JSON.stringify(panelPos.value))
  } catch { /* ignore */ }
}

const getBounds = () => ({
  minLeft: 0,
  maxLeft: Math.max(0, window.innerWidth - props.width),
  minTop: 0,
  maxTop: Math.max(0, window.innerHeight - props.height),
})

const clamp = (p, b) => ({
  left: Math.min(b.maxLeft, Math.max(b.minLeft, p.left)),
  top: Math.min(b.maxTop, Math.max(b.minTop, p.top)),
})

const startDrag = (e) => {
  if (e.button !== 0) return
  dragState.value = {
    offsetX: e.clientX - panelPos.value.left,
    offsetY: e.clientY - panelPos.value.top,
  }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  const next = { left: e.clientX - dragState.value.offsetX, top: e.clientY - dragState.value.offsetY }
  panelPos.value = clamp(next, getBounds())
}

const stopDrag = () => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  savePosition()
}

const onKeyDown = (e) => {
  if (e.key === 'Escape') {
    // parent handles close order; just emit
  }
}

const windowStyle = computed(() => ({
  width: `${props.width}px`,
  height: `${props.height}px`,
  left: `${panelPos.value.left}px`,
  top: `${panelPos.value.top}px`,
}))

onMounted(() => {
  loadPosition()
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style scoped>
.mini-window {
  position: fixed;
  z-index: 120;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.14);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mini-header {
  display: flex;
  align-items: center;
  padding: 0 12px;
  height: 40px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.drag-handle {
  flex: 1;
  display: flex;
  align-items: center;
  cursor: grab;
  user-select: none;
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
}

.drag-handle:active {
  cursor: grabbing;
}

.mini-close {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.mini-close:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #1d1d1f;
}

.mini-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
</style>
