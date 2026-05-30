<template>
  <div class="widget-panel" :class="`variant-${heatmapVariant}`">
    <div ref="bodyRef" class="heatmap-body">
      <div v-if="useSparkline" class="sparkline-wrap">
        <svg class="sparkline" viewBox="0 0 240 48" preserveAspectRatio="none" aria-hidden="true">
          <path class="sparkline-area" :d="areaPath"></path>
          <path class="sparkline-line" :d="linePath"></path>
        </svg>
        <div class="sparkline-hit-zones">
          <div
            v-for="hour in hourCells"
            :key="`spark-${hour.hour}`"
            class="sparkline-hit-zone"
            :aria-label="hour.title"
            @mouseenter="showTooltip($event, hour)"
            @mousemove="moveTooltip($event)"
            @mouseleave="hideTooltip"
          ></div>
        </div>
      </div>
      <div v-else class="cell-grid">
        <div
          v-for="hour in hourCells"
          :key="hour.hour"
          class="cell"
          :class="cellClass(hour.count)"
          :aria-label="hour.title"
          @mouseenter="showTooltip($event, hour)"
          @mousemove="moveTooltip($event)"
          @mouseleave="hideTooltip"
        ></div>
      </div>
      <div v-if="tooltip.visible" class="heatmap-tooltip" :style="tooltipStyle">
        {{ tooltip.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useDashboardStore } from '../../stores/dashboard.js'

const props = defineProps({
  heatmapVariant: {
    type: String,
    default: 'wide'
  }
})

const store = useDashboardStore()

const peak = computed(() => Math.max(1, ...store.todayHourly))
const tooltip = reactive({ visible: false, text: '', x: 0, y: 0 })
const bodyRef = ref(null)
const size = reactive({ width: 0, height: 0 })
let resizeObserver = null

const formatHour = (hour) => `${String(hour).padStart(2, '0')}:00`

const hourCells = computed(() => {
  return store.todayHourly.map((count, hour) => {
    const endHour = (hour + 1) % 24
    return {
      hour,
      count,
      title: `${formatHour(hour)}-${formatHour(endHour)} · ${count} 次活动`
    }
  })
})

const tooltipStyle = computed(() => ({
  left: `${tooltip.x}px`,
  top: `${tooltip.y}px`
}))

const useSparkline = computed(() => {
  return ['wide', 'full', 'banner', 'sparkline'].includes(props.heatmapVariant) ||
    (size.width >= 720 && size.width / Math.max(size.height, 1) >= 7)
})

const sparkPoints = computed(() => {
  const width = 232
  const top = 8
  const bottom = 40
  return store.todayHourly.map((count, index) => {
    const x = 4 + (index / 23) * width
    const pct = count / peak.value
    const y = bottom - Math.max(count > 0 ? 0.16 : 0, pct) * (bottom - top)
    return [Number(x.toFixed(2)), Number(y.toFixed(2))]
  })
})

const linePath = computed(() => {
  return sparkPoints.value
    .map(([x, y], index) => `${index === 0 ? 'M' : 'L'} ${x} ${y}`)
    .join(' ')
})

const areaPath = computed(() => {
  const points = sparkPoints.value
  if (points.length === 0) return ''
  const line = points.map(([x, y], index) => `${index === 0 ? 'M' : 'L'} ${x} ${y}`).join(' ')
  return `${line} L 236 42 L 4 42 Z`
})

const placeTooltip = (event) => {
  const bodyRect = event.currentTarget.closest('.heatmap-body')?.getBoundingClientRect()
  if (!bodyRect) return
  const relativeX = event.clientX - bodyRect.left
  const relativeY = event.clientY - bodyRect.top
  tooltip.x = Math.min(Math.max(relativeX, 76), Math.max(76, bodyRect.width - 76))
  tooltip.y = Math.max(24, relativeY - 8)
}

const showTooltip = (event, hour) => {
  tooltip.text = hour.title
  tooltip.visible = true
  placeTooltip(event)
}

const moveTooltip = (event) => {
  if (!tooltip.visible) return
  placeTooltip(event)
}

const hideTooltip = () => {
  tooltip.visible = false
}

const cellClass = (count) => {
  if (count === 0) return 'l0'
  const pct = count / peak.value
  if (pct <= 0.2) return 'l1'
  if (pct <= 0.4) return 'l2'
  if (pct <= 0.6) return 'l3'
  return 'l4'
}

onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    const rect = entry.contentRect
    size.width = rect.width
    size.height = rect.height
  })
  if (bodyRef.value) {
    resizeObserver.observe(bodyRef.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
})
</script>

<style scoped>
.widget-panel {
  height: 100%;
  width: 100%;
  overflow: visible;
}
.heatmap-body {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  padding: 6px;
  overflow: visible;
}

.cell-grid {
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  display: grid;
  align-items: center;
  justify-items: center;
  align-content: center;
  justify-content: center;
  gap: 3px;
}

.sparkline-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(155, 233, 168, 0.16), rgba(235, 237, 240, 0.24));
}

.sparkline {
  display: block;
  width: 100%;
  height: 100%;
}

.sparkline-area {
  fill: rgba(64, 196, 99, 0.2);
}

.sparkline-line {
  fill: none;
  stroke: #30a14e;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}

.sparkline-hit-zones {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(24, minmax(0, 1fr));
}

.sparkline-hit-zone {
  min-width: 0;
  cursor: default;
}

.sparkline-hit-zone:hover {
  background: rgba(31, 35, 40, 0.04);
}

.variant-compact .cell-grid {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.variant-wide .cell-grid {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.variant-tall .cell-grid {
  grid-template-columns: repeat(8, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(0, 1fr));
}

.variant-full .cell-grid {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.variant-banner .cell-grid {
  grid-template-columns: repeat(24, minmax(0, 1fr));
  grid-template-rows: minmax(0, 1fr);
}

.cell {
  width: 100%;
  height: auto;
  max-width: 20px;
  max-height: 20px;
  aspect-ratio: 1 / 1;
  min-width: 0;
  min-height: 0;
  border-radius: 3px;
  cursor: default;
  border: 1px solid rgba(27, 31, 36, 0.08);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.45);
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.heatmap-tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  max-width: min(160px, calc(100% - 12px));
  padding: 5px 8px;
  border-radius: 6px;
  background: rgba(31, 35, 40, 0.92);
  color: #ffffff;
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
  pointer-events: none;
  z-index: 5;
  box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}
.cell:hover {
  transform: scale(1.04);
  box-shadow: 0 0 0 2px rgba(31, 35, 40, 0.12), inset 0 0 0 1px rgba(255,255,255,0.55);
  z-index: 1;
}
.cell.l0 { background: #ebedf0; }
.cell.l1 { background: #9be9a8; border-color: transparent; }
.cell.l2 { background: #40c463; border-color: transparent; }
.cell.l3 { background: #30a14e; border-color: transparent; }
.cell.l4 { background: #216e39; border-color: transparent; }
</style>
