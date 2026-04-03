<template>
  <div class="partner-match-wrapper">
    <div class="header">
      <h2>搭子匹配预留界面</h2>
      <p>此处为六号接口预留地，用于寻找志同道合的学习或工作搭子。</p>
    </div>

    <div class="match-skeleton">
      <div class="filter-bar">
        <button disabled class="filter-btn">所有领域</button>
        <button disabled class="filter-btn">学习搭子</button>
        <button disabled class="filter-btn">项目开发</button>
        <button disabled class="filter-btn">考试考研</button>
      </div>

      <div class="match-grid">
        <div v-for="i in 6" :key="i" class="user-card skeleton-box">
          <div class="avatar-skeleton placeholder-pulse"></div>
          <div class="info-skeleton">
            <div class="line-short placeholder-pulse"></div>
            <div class="line-long placeholder-pulse"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 未来的六号接口数据请求逻辑将放在这里
</script>

<style scoped>
.partner-match-wrapper {
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

.match-skeleton {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.filter-btn {
  padding: 6px 14px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fafafa;
  color: #999;
  cursor: not-allowed;
  font-size: 13px;
}

.match-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.user-card {
  padding: 16px;
  border-radius: 12px;
  background: #fdfdfd;
  border: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-skeleton {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #eaeaea;
}

.info-skeleton {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.line-short {
  height: 14px;
  width: 40%;
  background: #eaeaea;
  border-radius: 4px;
}

.line-long {
  height: 12px;
  width: 80%;
  background: #eaeaea;
  border-radius: 4px;
}

.placeholder-pulse {
  animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 0.3; }
  100% { opacity: 0.6; }
}
</style>