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
            <div class="preference-text">{{ displayWorkPreference || '暂无数据' }}</div>
            <div v-if="behaviorProfileStore.hasBehaviorData" class="profile-source-hint">基于最近 30 天使用行为生成</div>
          </div>

          <div class="info-section">
            <span class="info-label">行为模式</span>
            <div class="preference-text">{{ displayBehaviorPattern || '暂无数据' }}</div>
          </div>

          <div class="info-section" v-if="Object.keys(displayPersonalityIndicators).length">
            <span class="info-label">{{ behaviorProfileStore.hasBehaviorData ? '使用倾向' : '个性指标' }}</span>
            <div class="indicator-row" v-for="(val, key) in displayPersonalityIndicators" :key="key">
              <span class="indicator-name">{{ indicatorLabel(key) }}</span>
              <div class="indicator-track">
                <div class="indicator-fill" :style="{ width: (val * 100) + '%' }"></div>
              </div>
              <span class="indicator-val">{{ Math.round(val * 100) }}%</span>
            </div>
          </div>

          <!-- 活跃热力 -->
          <div class="info-section">
            <div class="heatmap-tabs">
              <button class="hm-tab" :class="{ active: heatmapView === 'today' }" @click="heatmapView = 'today'">今日</button>
              <button class="hm-tab" :class="{ active: heatmapView === 'week' }" @click="heatmapView = 'week'">本周</button>
              <button class="hm-tab" :class="{ active: heatmapView === 'month' }" @click="heatmapView = 'month'">本月</button>
            </div>
            <div v-if="heatmapView === 'today'" class="hourly-bars-compact">
              <div
                v-for="(count, h) in dashboardStore.todayHourly"
                :key="h"
                class="hourly-bar-compact"
                :class="hourlyBarClass(count)"
                :style="{ height: hourlyBarPct(count) + '%' }"
                :aria-label="hourlyTooltipText(h, count)"
                @mouseenter="showHeatmapTooltip($event, hourlyTooltipText(h, count))"
                @mousemove="moveHeatmapTooltip($event)"
                @mouseleave="hideHeatmapTooltip"
              ></div>
            </div>
            <div v-if="heatmapView === 'week'" class="week-heat-grid">
              <div
                v-for="day in dashboardStore.weeklyHeatmap"
                :key="day.date"
                class="week-heat-cell"
                :class="weekCellClass(day.total)"
                :aria-label="dayTooltipText(day)"
                @mouseenter="showHeatmapTooltip($event, dayTooltipText(day))"
                @mousemove="moveHeatmapTooltip($event)"
                @mouseleave="hideHeatmapTooltip"
              >
                <span class="week-cell-day">{{ day.dayLabel }}</span>
              </div>
            </div>
            <div v-if="heatmapView === 'month'" class="month-heat-grid">
              <div
                v-for="day in dashboardStore.monthlyHeatmap"
                :key="day.date"
                class="month-heat-cell"
                :class="monthCellClass(day.total)"
                :aria-label="dayTooltipText(day)"
                @mouseenter="showHeatmapTooltip($event, dayTooltipText(day))"
                @mousemove="moveHeatmapTooltip($event)"
                @mouseleave="hideHeatmapTooltip"
              ></div>
            </div>
            <div v-if="heatmapTooltip.visible" class="profile-heatmap-tooltip" :style="heatmapTooltipStyle">
              {{ heatmapTooltip.text }}
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
import { computed, ref, reactive, onMounted, onActivated, onUnmounted, watch } from 'vue'
import { profileAPI } from '../services/api.js'
import { useBehaviorProfileStore } from '../stores/behaviorProfile.js'
import { useDashboardStore } from '../stores/dashboard.js'

const HEATMAP_VIEW_KEY = 'proagent_portrait_heatmap_view'

const loadHeatmapView = () => {
  try { return localStorage.getItem(HEATMAP_VIEW_KEY) || 'today' } catch { return 'today' }
}
const saveHeatmapView = (view) => {
  try { localStorage.setItem(HEATMAP_VIEW_KEY, view) } catch {}
}

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
const dashboardStore = useDashboardStore()
const behaviorProfileStore = useBehaviorProfileStore()
const heatmapView = ref(loadHeatmapView())
const heatmapTooltip = reactive({ visible: false, text: '', x: 0, y: 0 })

const displayWorkPreference = computed(() => {
  if (behaviorProfileStore.hasBehaviorData) {
    return behaviorProfileStore.profile.workPreferenceText
  }
  return workPreference.value
})

const displayBehaviorPattern = computed(() => {
  if (behaviorProfileStore.hasBehaviorData) {
    return behaviorProfileStore.profile.behaviorPatternText
  }
  return behaviorPattern.value
})

const displayPersonalityIndicators = computed(() => {
  if (behaviorProfileStore.hasBehaviorData) {
    return behaviorProfileStore.profile.indicators
  }
  return personalityIndicators.value
})

const maxHourly = computed(() => Math.max(1, ...dashboardStore.todayHourly))
const hourlyBarPct = (count) => Math.max(count > 0 ? 6 : 2, (count / maxHourly.value) * 100)
const hourlyBarClass = (count) => count > 0 ? 'active' : ''
const formatHour = (hour) => `${String(hour).padStart(2, '0')}:00`
const hourlyTooltipText = (hour, count) => `${formatHour(hour)}-${formatHour((hour + 1) % 24)} · ${count} 次活动`
const dayTooltipText = (day) => `${day.short || day.date} · ${day.total} 次活动`
const heatmapTooltipStyle = computed(() => ({
  left: `${heatmapTooltip.x}px`,
  top: `${heatmapTooltip.y}px`
}))

const placeHeatmapTooltip = (event) => {
  const sectionRect = event.currentTarget.closest('.info-section')?.getBoundingClientRect()
  if (!sectionRect) return
  const relativeX = event.clientX - sectionRect.left
  const relativeY = event.clientY - sectionRect.top
  heatmapTooltip.x = Math.min(Math.max(relativeX, 76), Math.max(76, sectionRect.width - 76))
  heatmapTooltip.y = Math.max(30, relativeY - 8)
}

const showHeatmapTooltip = (event, text) => {
  heatmapTooltip.text = text
  heatmapTooltip.visible = true
  placeHeatmapTooltip(event)
}

const moveHeatmapTooltip = (event) => {
  if (!heatmapTooltip.visible) return
  placeHeatmapTooltip(event)
}

const hideHeatmapTooltip = () => {
  heatmapTooltip.visible = false
}

const maxWeekly = computed(() => Math.max(1, ...dashboardStore.weeklyHeatmap.map(d => d.total)))
const weekCellClass = (total) => {
  if (total === 0) return 'l0'
  const pct = total / maxWeekly.value
  if (pct <= 0.25) return 'l1'
  if (pct <= 0.5) return 'l2'
  if (pct <= 0.75) return 'l3'
  return 'l4'
}

const maxMonthly = computed(() => Math.max(1, ...dashboardStore.monthlyHeatmap.map(d => d.total)))

watch(heatmapView, saveHeatmapView)
const monthCellClass = (total) => {
  if (total === 0) return 'l0'
  const pct = total / maxMonthly.value
  if (pct <= 0.25) return 'l1'
  if (pct <= 0.5) return 'l2'
  if (pct <= 0.75) return 'l3'
  return 'l4'
}

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
    visual_sensitive: '视觉反馈',
    organization_driven: '组织驱动',
    automation_preference: '自动化倾向',
    iterative: '迭代优化',
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
  position: relative;
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

.profile-source-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #8e8e93;
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

/* 热力 tab 切换 */
.heatmap-tabs { display: flex; gap: 2px; background: rgba(0,0,0,0.04); padding: 3px; border-radius: 7px; margin-bottom: 8px; }
.hm-tab { flex: 1; border: none; border-radius: 5px; padding: 4px 0; font-size: 11px; cursor: pointer; background: transparent; color: rgba(0,0,0,0.4); font-weight: 500; transition: all 0.15s; }
.hm-tab:hover { color: rgba(0,0,0,0.6); }
.hm-tab.active { background: #fff; color: #1d1d1f; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

/* 今日每小时柱状图 */
.hourly-bars-compact { display: flex; align-items: flex-end; gap: 1px; height: 40px; margin-top: 4px; }
.hourly-bar-compact { flex: 1; border-radius: 2px 2px 0 0; background: rgba(0,0,0,0.04); transition: height 0.3s, box-shadow 0.12s ease, transform 0.12s ease; min-width: 0; cursor: default; }
.hourly-bar-compact.active { background: #30a14e; }
.hourly-bar-compact:hover { box-shadow: 0 0 0 2px rgba(31, 35, 40, 0.12); transform: scaleY(1.04); }

/* 周热力 */
.week-heat-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 4px; }
.week-heat-cell { aspect-ratio: 1; border-radius: 6px; background: rgba(0,0,0,0.04); display: flex; align-items: center; justify-content: center; font-size: 10px; color: rgba(0,0,0,0.3); cursor: default; transition: box-shadow 0.12s ease, transform 0.12s ease; }
.week-heat-cell:hover { box-shadow: 0 0 0 2px rgba(31, 35, 40, 0.12); transform: scale(1.02); }
.week-heat-cell.l1 { background: #9be9a8; color: rgba(0,0,0,0.4); }
.week-heat-cell.l2 { background: #40c463; color: rgba(255,255,255,0.7); }
.week-heat-cell.l3 { background: #30a14e; color: #fff; }
.week-heat-cell.l4 { background: #216e39; color: #fff; }

/* 月热力 */
.month-heat-grid { display: flex; flex-wrap: wrap; gap: 2px; margin-top: 4px; }
.month-heat-cell { width: 14px; height: 14px; border-radius: 2px; background: rgba(0,0,0,0.04); cursor: default; transition: box-shadow 0.12s ease, transform 0.12s ease; }
.month-heat-cell:hover { box-shadow: 0 0 0 2px rgba(31, 35, 40, 0.12); transform: scale(1.05); }
.month-heat-cell.l1 { background: #9be9a8; }
.month-heat-cell.l2 { background: #40c463; }
.month-heat-cell.l3 { background: #30a14e; }
.month-heat-cell.l4 { background: #216e39; }

.profile-heatmap-tooltip {
  position: absolute;
  transform: translate(-50%, -100%);
  max-width: min(180px, calc(100% - 12px));
  padding: 6px 9px;
  border-radius: 7px;
  background: rgba(31, 35, 40, 0.92);
  color: #fff;
  font-size: 11px;
  line-height: 1.25;
  white-space: nowrap;
  pointer-events: none;
  z-index: 8;
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
}
</style>
