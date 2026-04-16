<template>
  <div class="portrait-wrapper">
    <div class="header">
      <h2>自我画像</h2>
      <p>完善你的能力、偏好和目标，让团队与 Agent 更懂你。</p>
    </div>

    <div class="portrait-layout">
      <section class="editor-panel card-shell">
        <h3>画像编辑</h3>

        <label class="field">
          <span>一句话介绍</span>
          <input
            v-model="form.tagline"
            type="text"
            placeholder="例如：跨前后端的效率控，擅长把想法落地"
          />
        </label>

        <label class="field">
          <span>当前重点目标</span>
          <textarea
            v-model="form.goal"
            rows="3"
            placeholder="例如：在 4 周内完成项目 MVP 并上线内测"
          ></textarea>
        </label>

        <label class="field">
          <span>工作偏好</span>
          <select v-model="form.workStyle">
            <option value="深度专注">深度专注</option>
            <option value="协作推进">协作推进</option>
            <option value="快速试错">快速试错</option>
          </select>
        </label>

        <div class="field">
          <span>能力标签</span>
          <div class="tag-list">
            <button
              v-for="skill in skillOptions"
              :key="skill"
              type="button"
              class="tag-chip"
              :class="{ active: form.skills.includes(skill) }"
              @click="toggleSkill(skill)"
            >
              {{ skill }}
            </button>
          </div>
        </div>

        <div class="progress-row">
          <span>画像完整度</span>
          <span>{{ completion }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${completion}%` }"></div>
        </div>
      </section>

      <section class="preview-panel card-shell">
        <h3>展示预览</h3>

        <div class="preview-card">
          <div class="preview-top">
            <div class="avatar">YM</div>
            <div class="identity">
              <strong>Yanmin</strong>
              <small>{{ form.workStyle }}</small>
            </div>
          </div>

          <p class="preview-tagline">{{ form.tagline || '请填写一句话介绍，突出你的特点。' }}</p>

          <div class="preview-block">
            <div class="block-title">目标</div>
            <div class="block-content">{{ form.goal || '请填写当前重点目标。' }}</div>
          </div>

          <div class="preview-block">
            <div class="block-title">能力标签</div>
            <div class="preview-tags">
              <span v-for="skill in selectedSkills" :key="skill" class="preview-chip">{{ skill }}</span>
              <span v-if="!selectedSkills.length" class="empty-chip">尚未选择</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'

const skillOptions = ['Vue', 'Node.js', 'UI 设计', '数据分析', '产品思维', '自动化']

const form = reactive({
  tagline: '',
  goal: '',
  workStyle: '深度专注',
  skills: ['Vue', 'UI 设计']
})

const selectedSkills = computed(() => form.skills)

const completion = computed(() => {
  const fields = [
    Boolean(form.tagline.trim()),
    Boolean(form.goal.trim()),
    Boolean(form.workStyle),
    form.skills.length > 0
  ]

  const done = fields.filter(Boolean).length
  return Math.round((done / fields.length) * 100)
})

const toggleSkill = (skill) => {
  const exists = form.skills.includes(skill)
  if (exists) {
    form.skills = form.skills.filter((item) => item !== skill)
  } else {
    form.skills.push(skill)
  }
}
</script>

<style scoped>
.portrait-wrapper {
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.header {
  margin-bottom: 18px;
}

.header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1d1d1f;
}

.header p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.portrait-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  min-height: 0;
}

.card-shell {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  box-shadow: 0 6px 20px rgba(17, 24, 39, 0.05);
  padding: 18px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-shell h3 {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 600;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

.field span {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.field input,
.field textarea,
.field select {
  border: 1px solid rgba(17, 24, 39, 0.15);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  color: #111827;
  outline: none;
  background: #fcfcfd;
}

.field input:focus,
.field textarea:focus,
.field select:focus {
  border-color: #0ea5e9;
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  border: 1px solid rgba(14, 165, 233, 0.3);
  background: #f0f9ff;
  color: #0369a1;
  border-radius: 999px;
  padding: 6px 11px;
  font-size: 12px;
  cursor: pointer;
}

.tag-chip.active {
  background: #0284c7;
  border-color: #0284c7;
  color: #ffffff;
}

.progress-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.progress-track {
  height: 8px;
  border-radius: 999px;
  background: #e5e7eb;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #0ea5e9, #22c55e);
  transition: width 0.25s ease;
}

.preview-panel {
  overflow: auto;
}

.preview-card {
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 12px;
  padding: 14px;
  background: #f8fafc;
}

.preview-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a, #334155);
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
}

.identity {
  display: flex;
  flex-direction: column;
}

.identity strong {
  font-size: 14px;
}

.identity small {
  font-size: 12px;
  color: #64748b;
}

.preview-tagline {
  margin: 0 0 12px;
  color: #0f172a;
  font-size: 13px;
  line-height: 1.5;
}

.preview-block {
  margin-bottom: 12px;
}

.block-title {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.block-content {
  font-size: 13px;
  color: #1e293b;
  line-height: 1.5;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preview-chip {
  font-size: 11px;
  background: #e0f2fe;
  color: #0c4a6e;
  border-radius: 999px;
  padding: 4px 9px;
}

.empty-chip {
  font-size: 11px;
  color: #6b7280;
}

@media (max-width: 980px) {
  .portrait-wrapper {
    padding: 16px;
  }

  .portrait-layout {
    grid-template-columns: 1fr;
  }
}
</style>
