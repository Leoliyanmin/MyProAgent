<template>
  <div class="file-manager-wrapper">
    <div class="header">
      <h2>文件系统暂未接入</h2>
      <p>为后续桌面端通过 native api（如 Electron、Tauri 等）访问本地资源与提供智能的文件管理留出占位区域。</p>
    </div>

    <!-- 简单的占位界面骨架，表明已为将来设计好结构 -->
    <div class="file-explorer-skeleton">
      <div class="toolbar">
        <button disabled class="tool-btn">新建文件夹</button>
        <button disabled class="tool-btn">导入文件</button>
        <button disabled class="tool-btn">扫描磁盘</button>
        <div class="spacer"></div>
        <input type="text" placeholder="搜索文件..." disabled class="search-input" />
      </div>

      <div class="content-area">
        <div class="file-tree">
          <div class="tree-item skeleton-text line-short"></div>
          <div class="tree-item skeleton-text line-long"></div>
          <div class="tree-item skeleton-text line-med"></div>
          <div class="tree-item skeleton-text line-short"></div>
        </div>
        <div class="file-grid">
          <div class="file-card skeleton-box"></div>
          <div class="file-card skeleton-box"></div>
          <div class="file-card skeleton-box"></div>
          <div class="file-card skeleton-box"></div>
          <div class="file-card skeleton-box"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 未来在这里可以调用 backend api (Rust / Node.js) 来获取电脑上的文件列表、读取内容、处理 AI 操作
</script>

<style scoped>
.file-manager-wrapper {
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1d1d1f;
}

.header p {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}

.file-explorer-skeleton {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.toolbar {
  height: 56px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  background: #fdfdfd;
}

.tool-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fafafa;
  color: #999;
  cursor: not-allowed;
  font-size: 13px;
}

.spacer {
  flex: 1;
}

.search-input {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fafafa;
  width: 200px;
  cursor: not-allowed;
}

.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.file-tree {
  width: 250px;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  padding: 16px;
  background: #fafafa;
}

.tree-item {
  height: 20px;
  background: #eaeaea;
  border-radius: 4px;
  margin-bottom: 12px;
}

.tree-item.line-short { width: 50%; }
.tree-item.line-med { width: 70%; }
.tree-item.line-long { width: 90%; }

.file-grid {
  flex: 1;
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 20px;
  align-content: start;
}

.file-card {
  height: 120px;
  background: #eaeaea;
  border-radius: 8px;
  animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 0.3; }
  100% { opacity: 0.6; }
}
</style>
