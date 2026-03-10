<template>
  <div class="dashboard-grid">
    <section class="mac-panel heatmap-section">
      <div class="panel-header">
        <h3 class="panel-title">任务完成记录</h3>
      </div>
      <div class="panel-body flex-center">
        <span class="placeholder-text">GitHub Contribution Graph Area</span>
      </div>
    </section>

    <section class="mac-panel notes-section">
      <div class="panel-header">
        <h3 class="panel-title">工作笔记</h3>
        <button class="mac-btn-primary">Save</button>
      </div>
      <div class="panel-body">
        <textarea class="markdown-input" placeholder="使用 Markdown 格式记录想法..."></textarea>
      </div>
    </section>

    <section class="mac-panel todo-section">
      <div class="panel-header border-bottom">
        <h3 class="panel-title">TODO List</h3>
      </div>
      <div class="panel-body todo-list">
        <div class="todo-item"><input type="checkbox" /> 完善前端路由</div>
        <div class="todo-item"><input type="checkbox" /> 接入 FullCalendar</div>
      </div>
    </section>

    <section class="mac-panel message-section">
      <div class="message-toolbar">
        <div class="source-tags">
          <button class="circle-tag">Email</button>
          <button class="circle-tag active">BlackBoard</button>
          <button class="circle-tag">Github</button>
        </div>
        <span class="toolbar-title">消息源</span>
      </div>
      <div class="message-content flex-center">
        <span class="placeholder-text">消息列表，渲染当前选中数据源的消息</span>
      </div>
    </section>
  </div>
</template>

<script setup>
// 当前仅为静态布局，后续可在此处引入 ECharts (热力图) 或 Markdown 解析库
</script>

<style scoped>
/* 核心 Grid 布局 */
.dashboard-grid {
  width: 100%;
  height: 100%;
  display: grid;
  /* 定义两列：左侧占 4 份，右侧占 6 份 */
  grid-template-columns: 4fr 6fr;
  /* 定义两行：上侧固定高度 240px，下侧自适应填满剩余空间 */
  grid-template-rows: 240px 1fr;
  gap: 16px;
  padding: 16px;
  box-sizing: border-box;
}

/* 统一的面板样式 (macOS 风格卡片) */
.mac-panel {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header.border-bottom {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.panel-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.02);
}

.placeholder-text {
  font-size: 12px;
  color: #86868b;
}

/* 笔记区特殊样式 */
.mac-btn-primary {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 4px 16px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.mac-btn-primary:hover {
  background: #f5f5f7;
}

.markdown-input {
  width: 100%;
  height: 100%;
  border: none;
  resize: none;
  outline: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #1d1d1f;
}

/* TODO 区样式 */
.todo-list {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.todo-item {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 消息区特殊样式 (匹配原型图中的圆形 Tag) */
.message-toolbar {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.source-tags {
  display: flex;
  gap: 8px;
}

.circle-tag {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 16px; /* 胶囊/圆形外观 */
  padding: 4px 12px;
  font-size: 12px;
  cursor: pointer;
  color: #1d1d1f;
}

.circle-tag.active {
  border-color: #1d1d1f;
  background: #1d1d1f;
  color: #ffffff;
}

.toolbar-title {
  position: absolute;
  right: 16px;
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
}

.message-content {
  flex: 1;
}
</style>