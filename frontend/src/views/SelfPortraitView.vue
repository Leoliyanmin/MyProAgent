<template>
  <div class="portrait-wrapper">
    <div class="header">
      <h2>自我画像</h2>
      <p>和AI聊聊，也许会有新收获。</p>
    </div>

    <div class="portrait-layout">
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

          <div class="info-section" v-if="Object.keys(personalityIndicators).length">
            <span class="info-label">个性指标</span>
            <div class="indicator-row" v-for="(val, key) in personalityIndicators" :key="key">
              <span class="indicator-name">{{ indicatorLabel(key) }}</span>
              <div class="indicator-track">
                <div class="indicator-fill" :style="{ width: (val * 100) + '%' }"></div>
              </div>
              <span class="indicator-val">{{ Math.round(val * 100) }}%</span>
            </div>
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

        <!-- 活跃时间热力图 -->
        <div class="heatmap-section" v-if="activeHours.length">
          <h4>活跃时段</h4>
          <div class="heatmap-grid">
            <div
              v-for="h in 24" :key="h"
              class="heatmap-cell"
              :class="{ active: activeHours.includes(h - 1) }"
              :title="`${h - 1}:00 - ${h}:00`"
            >{{ h - 1 }}</div>
          </div>
          <div class="heatmap-legend">
            <span class="legend-label">凌晨</span>
            <span class="legend-label">上午</span>
            <span class="legend-label">下午</span>
            <span class="legend-label">晚上</span>
          </div>
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
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, onActivated, onUnmounted } from 'vue'
import { profileAPI } from '../services/api.js'

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
const activeHours = ref([])
const personalityIndicators = ref({})

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
    activeHours.value = patterns.active_hours || []
    personalityIndicators.value = p.personality_indicators || {}

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

function indicatorLabel(key) {
  const labels = {
    detail_oriented: '注重细节',
    proactive: '积极主动',
    collaborative: '协作倾向',
  }
  return labels[key] || key
}

onMounted(() => {
  fetchProfile()
  window.addEventListener('interaction-logged', fetchProfile)
})

onUnmounted(() => {
  window.removeEventListener('interaction-logged', fetchProfile)
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

.portrait-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  min-height: 0;
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

.preview-panel {
  overflow: auto;
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

/* 个性指标条 */
.indicator-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.indicator-name {
  width: 65px;
  font-size: 11px;
  color: #6b7280;
  flex-shrink: 0;
}

.indicator-track {
  flex: 1;
  height: 8px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.indicator-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  transition: width 0.4s ease;
}

.indicator-val {
  width: 34px;
  font-size: 10px;
  color: #6b7280;
  text-align: right;
  flex-shrink: 0;
}

/* 活跃时间热力图 */
.heatmap-section {
  margin-top: 20px;
}

.heatmap-section h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px;
  color: #1d1d1f;
}

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(24, 1fr);
  gap: 2px;
}

.heatmap-cell {
  aspect-ratio: 1;
  border-radius: 3px;
  background: #f3f4f6;
  font-size: 8px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.heatmap-cell.active {
  background: linear-gradient(135deg, #0ea5e9, #38bdf8);
  color: #fff;
  font-weight: 600;
}

.heatmap-legend {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}

.legend-label {
  font-size: 10px;
  color: #9ca3af;
}
</style>
