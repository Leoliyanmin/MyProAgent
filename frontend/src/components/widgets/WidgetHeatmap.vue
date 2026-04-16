<template>
  <div class="widget-container">
    <div class="panel-header">
      <h3 class="panel-title">任务完成记录</h3>
      <div class="heatmap-legend">
        <span class="legend-text">Less</span>
        <ul class="legend-colors">
          <li style="background: #ebedf0"></li>
          <li style="background: #9be9a8"></li>
          <li style="background: #40c463"></li>
          <li style="background: #30a14e"></li>
          <li style="background: #216e39"></li>
        </ul>
        <span class="legend-text">More</span>
      </div>
    </div>
    <div class="panel-body chart-wrapper">
      <div ref="heatmapChartRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'
import { useDashboardStore } from '../../stores/dashboard'

const store = useDashboardStore()
// 使用 shallowRef 提升 ECharts 性能
const heatmapChartRef = shallowRef(null)
let chartInstance = null
let resizeObserver = null

onMounted(() => {
  chartInstance = echarts.init(heatmapChartRef.value)
  
  const baseOption = {
    tooltip: { position: 'top', formatter: '{c} contributions on {b}' },
    visualMap: {
      min: 0, max: 10, type: 'piecewise', orient: 'horizontal', left: 'center', top: 0, show: false,
      inRange: { color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'] }
    },
    calendar: {
      top: 30, left: 30, right: 10, bottom: 10, // 调整了 Top 边距防止被切断
      range: '2026',
      cellSize: ['auto', 14], splitLine: { show: false },
      itemStyle: { borderWidth: 3, borderColor: '#fff' },
      yearLabel: { show: false },
      dayLabel: { nameMap: 'ZH', fontSize: 10, color: '#86868b' },
      monthLabel: { nameMap: 'ZH', fontSize: 10, color: '#86868b' }
    },
    series: { type: 'heatmap', coordinateSystem: 'calendar', data: store.heatmapData }
  }
  
  chartInstance.setOption(baseOption)

  // 核心修复：监听 DOM 元素的真实尺寸变化，而不是 window 缩放
  resizeObserver = new ResizeObserver(() => {
    if (chartInstance) chartInstance.resize()
  })
  if (heatmapChartRef.value) resizeObserver.observe(heatmapChartRef.value)
})

watch(
  () => store.heatmapData,
  (newData) => {
    if (chartInstance) chartInstance.setOption({ series: { data: newData } })
  },
  { deep: true }
)

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
/* 必须保留这部分 CSS，否则组件没有结构 */
.widget-container { display: flex; flex-direction: column; height: 100%; width: 100%; }
.panel-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid rgba(0,0,0,0.06); }
.panel-title { font-size: 13px; font-weight: 600; margin: 0; }
.heatmap-legend { display: flex; align-items: center; gap: 4px; }
.legend-text { font-size: 10px; color: #86868b; }
.legend-colors { display: flex; gap: 2px; list-style: none; padding: 0; margin: 0; }
.legend-colors li { width: 10px; height: 10px; border-radius: 2px; }

/* 核心修复：强制撑满布局 */
.chart-wrapper {
  flex: 1;
  position: relative; /* 建立定位上下文 */
  min-height: 0; /* 防止 Flex 子项溢出 */
  padding: 16px;
}
.chart-container {
  position: absolute;
  top: 16px; left: 16px; right: 16px; bottom: 16px;
}
</style>