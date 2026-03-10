<template>
  <div class="calendar-wrapper">
    <div class="calendar-toolbar">
      <div class="toolbar-left">
        <button class="mac-btn">今天</button>
        <div class="nav-arrows">
          <button class="icon-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>
          </button>
          <button class="icon-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </button>
        </div>
      </div>

      <div class="toolbar-center">
        <h2 class="current-date">2026年 3月</h2>
      </div>

      <div class="toolbar-right">
        <div class="segmented-control">
          <button class="segment">日</button>
          <button class="segment">周</button>
          <button class="segment active">月</button>
          <button class="segment">年</button>
        </div>
      </div>
    </div>

    <div class="calendar-grid-container">
      <div class="mock-calendar-body">
        <div class="weekdays-header">
          <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
        </div>
        <div class="days-grid">
          <div v-for="i in 35" :key="i" class="day-cell">
            <span class="date-num" :class="{ 'is-today': i === 10 }">{{ i <= 31 ? i : i - 31 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 视图外层容器，复用 App.vue 中的 content-wrapper 逻辑 */
.calendar-wrapper {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 控制栏布局 */
.calendar-toolbar {
  height: 56px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fafafa;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.toolbar-right {
  justify-content: flex-end;
}

.toolbar-center {
  flex: 1;
  text-align: center;
}

.current-date {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

/* macOS 风格基础按钮 */
.mac-btn {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.mac-btn:hover { background: #f5f5f7; }

.nav-arrows {
  display: flex;
  gap: 4px;
}

.icon-btn {
  background: transparent;
  border: none;
  border-radius: 6px;
  padding: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #86868b;
}

.icon-btn:hover { background: rgba(0, 0, 0, 0.05); }

/* 分段控制器 (复用样式) */
.segmented-control {
  display: flex;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px;
  border-radius: 8px;
}

.segment {
  background: transparent;
  border: none;
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  border-radius: 6px;
  cursor: pointer;
}

.segment.active {
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 日历主体 CSS Grid 模拟 */
.calendar-grid-container {
  flex: 1;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.mock-calendar-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.weekdays-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  text-align: right;
  padding: 8px 8px 4px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
}

.days-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(5, 1fr);
}

.day-cell {
  border-right: 1px solid rgba(0, 0, 0, 0.04);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding: 8px;
  text-align: right;
}

.date-num {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.date-num.is-today {
  background-color: #fc3c44; /* macOS Calendar today red */
  color: #ffffff;
  font-weight: 600;
}
</style>