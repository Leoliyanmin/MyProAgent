<template>
  <div v-if="!dismissed" class="theme-suggestion-card">
    <div class="suggestion-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
      </svg>
      <span class="suggestion-title">主题建议</span>
    </div>

    <!-- Layout preview matching ThemeSettingsView schematic -->
    <div class="schematic" :style="{ backgroundColor: tokens.bgApp || '#f5f5f7' }">
      <div
        class="sch-sidebar zone-preview"
        :style="{ backgroundColor: tokens.bgSidebar || '#ebebeb' }"
      >
        <div class="sch-logo" :style="{ backgroundColor: tokens.accent || '#007aff' }"></div>
        <div class="sch-navitem" :style="{ backgroundColor: tokens.borderColor || '#e5e7eb' }"></div>
        <div class="sch-navitem sch-navitem--dim" :style="{ backgroundColor: tokens.borderColor || '#e5e7eb' }"></div>
        <div class="sch-navitem sch-navitem--dim" :style="{ backgroundColor: tokens.borderColor || '#e5e7eb' }"></div>
        <div class="sch-spacer"></div>
        <div class="sch-avatar" :style="{ backgroundColor: tokens.accent || '#007aff' }"></div>
        <span class="zone-label">侧边栏</span>
      </div>

      <div class="sch-main">
        <div
          class="sch-topbar zone-preview"
          :style="{ backgroundColor: tokens.bgTopbar || '#ebebeb' }"
        >
          <div class="sch-segment" :style="{ backgroundColor: tokens.accent || '#007aff' }"></div>
          <div class="sch-segment sch-segment--ghost" :style="{ backgroundColor: tokens.borderColor || '#e5e7eb' }"></div>
          <span class="zone-label">顶栏</span>
        </div>

        <div
          class="sch-content zone-preview"
          :style="{ backgroundColor: tokens.bgContent || '#f5f5f7' }"
        >
          <div
            class="sch-card"
            :style="{ backgroundColor: tokens.bgCard || '#ffffff', borderRadius: (tokens.cardRadius || 12) + 'px' }"
          >
            <div class="sch-accent-bar" :style="{ backgroundColor: tokens.accent || '#007aff' }"></div>
            <div class="sch-card-title" :style="{ color: tokens.textPrimary || '#1d1d1f' }">标题</div>
            <div class="sch-card-desc" :style="{ color: tokens.textMuted || '#6b7280' }">描述内容</div>
          </div>
          <div
            class="sch-card"
            :style="{ backgroundColor: tokens.bgCard || '#ffffff', borderRadius: (tokens.cardRadius || 12) + 'px' }"
          >
            <div class="sch-accent-bar" :style="{ backgroundColor: tokens.accent || '#007aff' }"></div>
            <div class="sch-card-title" :style="{ color: tokens.textPrimary || '#1d1d1f' }">标题</div>
          </div>
          <span class="zone-label">内容区</span>
        </div>
      </div>

      <div
        class="sch-agent zone-preview"
        :style="{ backgroundColor: tokens.bgAgent || '#ebebeb' }"
      >
        <div class="sch-agent-header" :style="{ backgroundColor: tokens.borderColor || '#e5e7eb' }"></div>
        <div class="sch-agent-body">
          <div class="sch-agent-line" :style="{ backgroundColor: tokens.textMuted || '#6b7280', opacity: 0.5 }"></div>
          <div class="sch-agent-line sch-agent-line--short" :style="{ backgroundColor: tokens.textMuted || '#6b7280', opacity: 0.3 }"></div>
        </div>
        <span class="zone-label">Agent</span>
      </div>
    </div>

    <div class="suggestion-actions">
      <button class="accept-btn" @click="$emit('accept', tokens)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        应用主题
      </button>
      <button class="reject-btn" @click="dismissed = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
        忽略
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  tokens: { type: Object, required: true }
})

defineEmits(['accept'])

const dismissed = ref(false)
</script>

<style scoped>
.theme-suggestion-card {
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 10px;
  padding: 10px;
  margin: 4px 0;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  color: #6b7280;
}

.suggestion-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #6b7280;
}

/* Schematic preview — matches ThemeSettingsView layout */
.schematic {
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.08);
  display: flex;
  height: 130px;
  overflow: hidden;
}

.zone-preview {
  position: relative;
}

.zone-label {
  position: absolute;
  bottom: 3px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 8px;
  color: rgba(0,0,0,0.35);
  pointer-events: none;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.sch-sidebar {
  width: 44px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 5px;
  gap: 5px;
}

.sch-logo { width: 14px; height: 14px; border-radius: 3px; }
.sch-navitem { height: 6px; border-radius: 3px; width: 100%; }
.sch-navitem--dim { opacity: 0.5; }
.sch-spacer { flex: 1; }
.sch-avatar { width: 12px; height: 12px; border-radius: 50%; align-self: center; }

.sch-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.sch-topbar {
  height: 22px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 6px;
  gap: 5px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}

.sch-segment { height: 12px; width: 28px; border-radius: 3px; }
.sch-segment--ghost { opacity: 0.35; }

.sch-content {
  flex: 1;
  padding: 5px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sch-card {
  padding: 5px 6px;
  border: 1px solid rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sch-accent-bar { height: 3px; border-radius: 2px; width: 35%; }
.sch-card-title { font-size: 8px; font-weight: 600; line-height: 1; }
.sch-card-desc { font-size: 7px; line-height: 1; }

.sch-agent {
  width: 36px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 5px;
  gap: 5px;
  border-left: 1px solid rgba(0,0,0,0.06);
}

.sch-agent-header { height: 6px; border-radius: 3px; width: 100%; }
.sch-agent-body { flex: 1; display: flex; flex-direction: column; gap: 3px; padding-top: 3px; }
.sch-agent-line { height: 4px; border-radius: 2px; width: 100%; }
.sch-agent-line--short { width: 55%; }

.suggestion-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.accept-btn, .reject-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.accept-btn {
  background: #007aff;
  color: white;
}

.accept-btn:hover {
  background: #0069d9;
}

.reject-btn {
  background: rgba(0,0,0,0.05);
  color: #6b7280;
  border: 1px solid rgba(0,0,0,0.1);
}

.reject-btn:hover {
  background: rgba(0,0,0,0.08);
  color: #1d1d1f;
}
</style>