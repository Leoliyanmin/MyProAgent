<template>
  <div class="portrait-wrapper">
    <div class="header">
      <h2>自我画像</h2>
      <p>完善你的能力、偏好和目标，让团队与 Agent 更懂你。</p>
    </div>

    <div class="tab-bar">
      <button
        :class="['tab-btn', { active: activeTab === 'ai' }]"
        @click="activeTab = 'ai'"
      >AI 画像分析</button>
      <button
        :class="['tab-btn', { active: activeTab === 'manual' }]"
        @click="activeTab = 'manual'"
      >手动编辑</button>
    </div>

    <!-- AI 画像分析 Tab -->
    <div v-if="activeTab === 'ai'" class="portrait-layout">
      <section class="editor-panel card-shell">
        <h3>AI 分析画像</h3>
        <div v-if="loading.ai" class="loading">加载中...</div>

        <template v-if="!loading.ai && profile">
          <div class="info-section">
            <span class="info-label">MBTI 类型</span>
            <div class="mbti-badge">{{ mbtiType || '分析中...' }}</div>
            <span v-if="mbtiConfidence" class="mbti-confidence">置信度: {{ mbtiConfidence }}</span>
          </div>

          <div class="info-section">
            <span class="info-label">兴趣领域</span>
            <div class="tag-list">
              <span
                v-for="item in interestsList"
                :key="item"
                class="tag-chip active"
              >{{ item }}</span>
              <span v-if="!interestsList.length" class="empty-chip">暂无数据</span>
            </div>
          </div>

          <div class="info-section">
            <span class="info-label">技能标签</span>
            <div class="tag-list">
              <span
                v-for="item in analysisSkills"
                :key="item"
                class="tag-chip active"
              >{{ item }}</span>
              <span v-if="!analysisSkills.length" class="empty-chip">暂无数据</span>
            </div>
          </div>

          <div class="info-section">
            <span class="info-label">工作偏好</span>
            <div class="preference-text">{{ workPreference || '暂无数据' }}</div>
          </div>

          <div class="info-section">
            <span class="info-label">行为模式</span>
            <div class="preference-text">{{ behaviorPattern || '暂无数据' }}</div>
          </div>
        </template>

        <div v-if="error.ai" class="error-banner">{{ error.ai }}</div>
      </section>

      <section class="preview-panel card-shell">
        <h3>MBTI 维度分析</h3>
        <div v-if="loading.ai" class="loading">加载中...</div>

        <div v-if="!loading.ai && mbtiScores" class="dimension-breakdown">
          <div v-for="pair in dimensionPairs" :key="pair.label" class="dimension-pair">
            <div class="dimension-pair-label">{{ pair.label }}</div>
            <div class="dimension-bars">
              <div class="dim-bar-row">
                <span class="dim-name">{{ pair.left.name }}</span>
                <div class="dim-bar-track">
                  <div class="dim-bar-fill" :style="{ width: pair.left.percent + '%' }"></div>
                </div>
                <span class="dim-value">{{ pair.left.percent }}%</span>
              </div>
              <div class="dim-bar-row">
                <span class="dim-name">{{ pair.right.name }}</span>
                <div class="dim-bar-track">
                  <div class="dim-bar-fill right" :style="{ width: pair.right.percent + '%' }"></div>
                </div>
                <span class="dim-value">{{ pair.right.percent }}%</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!loading.ai && mbtiDescription" class="mbti-desc">
          <strong>类型描述</strong>
          <p>{{ mbtiDescription }}</p>
        </div>

        <div class="action-bar">
          <button class="action-btn" @click="fetchProfile" :disabled="loading.ai">刷新分析</button>
          <button class="action-btn secondary" @click="reanalyze" :disabled="loading.ai">重新分析全部</button>
        </div>

        <!-- 交互历史 -->
        <div class="history-section" v-if="!loading.ai">
          <h4>最近交互</h4>
          <div v-if="interactions.length === 0" class="empty-hint">暂无交互记录</div>
          <div
            v-for="item in interactions"
            :key="item.conversation_id"
            class="history-item"
            @click="viewInteraction(item.conversation_id)"
          >
            <div class="history-meta">
              <span class="history-intent">{{ item.intent_category }}</span>
              <span class="history-time">{{ formatTime(item.timestamp) }}</span>
            </div>
            <div class="history-preview">{{ item.user_message_preview }}</div>
          </div>
        </div>
      </section>
    </div>

    <!-- 手动编辑 Tab（保留原有内容） -->
    <div v-if="activeTab === 'manual'" class="portrait-layout">
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
import { computed, reactive, ref, onMounted, onActivated } from 'vue'
import { profileAPI } from '../services/api.js'

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

// tab
const activeTab = ref('ai')

// AI analysis state
const loading = reactive({ ai: false })
const error = reactive({ ai: '' })
const profile = ref(null)
const mbtiScores = ref(null)
const mbtiType = ref('')
const mbtiConfidence = ref('')
const mbtiDescription = ref('')
const interestsList = ref([])
const analysisSkills = ref([])
const workPreference = ref('')
const behaviorPattern = ref('')
const interactions = ref([])

const dimensionPairs = computed(() => {
  const s = mbtiScores.value
  if (!s) return []
  const ei = s.E_I || {}
  const sn = s.S_N || {}
  const tf = s.T_F || {}
  const jp = s.J_P || {}

  const toPct = (v) => Math.round((v || 0) * 100)

  return [
    {
      label: 'E/I · 能量来源',
      left: { name: '外向 (E)', percent: toPct(ei.E) },
      right: { name: '内向 (I)', percent: toPct(ei.I) },
    },
    {
      label: 'S/N · 认知方式',
      left: { name: '实感 (S)', percent: toPct(sn.S) },
      right: { name: '直觉 (N)', percent: toPct(sn.N) },
    },
    {
      label: 'T/F · 决策依据',
      left: { name: '理性 (T)', percent: toPct(tf.T) },
      right: { name: '情感 (F)', percent: toPct(tf.F) },
    },
    {
      label: 'J/P · 生活方式',
      left: { name: '判断 (J)', percent: toPct(jp.J) },
      right: { name: '感知 (P)', percent: toPct(jp.P) },
    },
  ]
})

async function fetchProfile() {
  loading.ai = true
  error.ai = ''
  try {
    const p = await profileAPI.getProfile()
    profile.value = p

    const mbti = p.mbti_inference || {}
    const rawScores = mbti.scores || {}
    if (rawScores.E_I && rawScores.S_N && rawScores.T_F && rawScores.J_P) {
      mbtiScores.value = rawScores
    } else {
      mbtiScores.value = null
    }
    mbtiType.value = mbti.mbti_type || ''
    mbtiConfidence.value = mbti.confidence || ''
    mbtiDescription.value = mbti.description || ''

    interestsList.value = (p.interests_identified || []).map(i => i.topic).slice(0, 10)
    analysisSkills.value = (p.skills_demonstrated || []).map(s => s.skill).slice(0, 10)

    const prefs = p.preferences_inferred || {}
    workPreference.value = `沟通风格: ${prefs.communication_style || 'casual'}, 语言: ${prefs.preferred_language || 'zh'}`

    const patterns = p.study_work_patterns || {}
    const topicStr = patterns.topic_areas?.length ? patterns.topic_areas.join(', ') : ''
    behaviorPattern.value = [
      `工作风格: ${patterns.work_style || 'flexible'}`,
      topicStr ? `关注领域: ${topicStr}` : ''
    ].filter(Boolean).join('；')

    const hist = await profileAPI.getInteractions(5, 0)
    interactions.value = hist.interactions || []
  } catch (e) {
    console.error('[Profile] fetch error:', e)
    error.ai = '加载画像数据失败，请确保已有对话记录'
  } finally {
    loading.ai = false
  }
}

async function reanalyze() {
  loading.ai = true
  error.ai = ''
  try {
    await profileAPI.reanalyze()
    await fetchProfile()
  } catch (e) {
    error.ai = '重新分析失败'
  } finally {
    loading.ai = false
  }
}

async function viewInteraction(conversationId) {
  try {
    const detail = await profileAPI.getInteractionDetail(conversationId)
    console.log('[Profile] Interaction detail:', detail)
    alert(`用户消息: ${(detail.user_input?.raw_message || '').slice(0, 100)}\n\nAgent 回复: ${(detail.agent_output?.raw_response || '').slice(0, 200)}`)
  } catch (e) {
    console.error('[Profile] fetch detail error:', e)
  }
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

onMounted(() => {
  fetchProfile()
})

onActivated(() => {
  fetchProfile()
})
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

.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  background: none;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #0284c7;
  border-bottom-color: #0284c7;
}

.portrait-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  min-height: 0;
}

.card-shell {
  background: var(--clr-bg-card, #ffffff);
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
  color: #6b7280;
}

.preview-tagline {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  margin-bottom: 14px;
}

.preview-block {
  margin-bottom: 12px;
}

.block-title {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.block-content {
  font-size: 13px;
  color: #111827;
  line-height: 1.5;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preview-chip {
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}

.empty-chip {
  color: #9ca3af;
  font-size: 12px;
  font-style: italic;
}

.loading {
  text-align: center;
  color: #9ca3af;
  padding: 40px 0;
  font-size: 14px;
}

.error-banner {
  background: #fef2f2;
  color: #dc2626;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
  margin-top: 8px;
}

.info-section {
  margin-bottom: 16px;
}

.info-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 6px;
}

.mbti-badge {
  display: inline-block;
  background: linear-gradient(135deg, #0f172a, #334155);
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 8px;
  letter-spacing: 2px;
}

.mbti-confidence {
  display: inline-block;
  margin-left: 8px;
  font-size: 12px;
  color: #6b7280;
}

.preference-text {
  font-size: 13px;
  color: #374151;
  line-height: 1.5;
}

.mbti-desc {
  background: #f0f9ff;
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}

.mbti-desc strong {
  font-size: 13px;
  color: #0369a1;
  display: block;
  margin-bottom: 6px;
}

.mbti-desc p {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.action-bar {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.action-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  background: #0284c7;
  color: #ffffff;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #0369a1;
}

.action-btn.secondary {
  background: #f0f9ff;
  color: #0369a1;
  border: 1px solid rgba(14, 165, 233, 0.3);
}

.action-btn.secondary:hover {
  background: #e0f2fe;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-section {
  margin-top: 20px;
}

.history-section h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px;
  color: #1d1d1f;
}

.empty-hint {
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
}

.history-item {
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  margin-bottom: 6px;
  transition: all 0.15s;
}

.history-item:hover {
  background: #f0f9ff;
  border-color: rgba(14, 165, 233, 0.2);
}

.history-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.history-intent {
  font-size: 11px;
  font-weight: 600;
  color: #0284c7;
  background: #e0f2fe;
  padding: 1px 8px;
  border-radius: 4px;
}

.history-time {
  font-size: 11px;
  color: #9ca3af;
}

.history-preview {
  font-size: 12px;
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dimension-breakdown {
  margin-top: 16px;
}

.dimension-breakdown h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px;
  color: #1d1d1f;
}

.dimension-pair {
  margin-bottom: 14px;
}

.dimension-pair-label {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}

.dimension-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dim-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dim-name {
  width: 70px;
  font-size: 12px;
  color: #374151;
  flex-shrink: 0;
}

.dim-bar-track {
  flex: 1;
  height: 10px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.dim-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #0ea5e9, #38bdf8);
  transition: width 0.4s ease;
}

.dim-bar-fill.right {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
}

.dim-value {
  width: 34px;
  font-size: 11px;
  color: #6b7280;
  text-align: right;
  flex-shrink: 0;
}
</style>
