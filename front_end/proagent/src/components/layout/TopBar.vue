<template>
  <header class="macos-topbar">
    <div class="segmented-control">
      <button 
        class="segment" 
        :class="{ active: currentView === 'dashboard' }"
        @click="emit('update:currentView', 'dashboard')"
      >主界面</button>
      <button 
        class="segment" 
        :class="{ active: currentView === 'calendar' }"
        @click="emit('update:currentView', 'calendar')"
      >日程规划</button>
    </div>
    
    <button class="icon-btn" @click="emit('toggleAgent')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="15" y1="3" x2="15" y2="21"></line></svg>
    </button>
  </header>
</template>

<script setup>
defineProps({
  currentView: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:currentView', 'toggleAgent'])
</script>