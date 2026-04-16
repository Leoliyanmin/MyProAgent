import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'

export const DEFAULTS = {
  accent:      '#007aff',
  bgApp:       '#f5f5f7',
  bgAppImage:  '',
  bgSidebar:   '#ebebeb',
  bgTopbar:    '#ebebeb',
  bgContent:   '#f5f5f7',
  bgAgent:     '#ebebeb',
  bgSidebarImage: '',
  bgTopbarImage: '',
  bgContentImage: '',
  bgAgentImage: '',
  bgCard:      '#ffffff',
  textPrimary: '#1d1d1f',
  textMuted:   '#6b7280',
  borderColor: '#e5e7eb',
  cardRadius:  12,
}

export const useThemeStore = defineStore('theme', () => {
  const tokens    = reactive({ ...DEFAULTS })
  const history   = ref([])
  const redoStack = ref([])

  const canUndo = computed(() => history.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  // 从 localStorage 加载保存的主题
  const loadFromStorage = () => {
    try {
      const saved = localStorage.getItem('proagent_theme')
      if (saved) {
        Object.assign(tokens, JSON.parse(saved))
      }
    } catch (e) {
      console.warn('Failed to load theme from storage:', e)
    }
  }

  // 保存到 localStorage
  const saveToStorage = () => {
    try {
      localStorage.setItem('proagent_theme', JSON.stringify(tokens))
    } catch (e) {
      console.warn('Failed to save theme to storage:', e)
    }
  }

  const applyToRoot = () => {
    const r = document.documentElement
    r.style.setProperty('--clr-accent',       tokens.accent)
    r.style.setProperty('--clr-bg-app',        tokens.bgApp)
    r.style.setProperty('--clr-bg-app-image',  tokens.bgAppImage ? `url("${tokens.bgAppImage}")` : 'none')
    r.style.setProperty('--clr-bg-sidebar',    tokens.bgSidebar)
    r.style.setProperty('--clr-bg-sidebar-image', tokens.bgSidebarImage ? `url("${tokens.bgSidebarImage}")` : 'none')
    r.style.setProperty('--clr-bg-topbar',     tokens.bgTopbar)
    r.style.setProperty('--clr-bg-topbar-image', tokens.bgTopbarImage ? `url("${tokens.bgTopbarImage}")` : 'none')
    r.style.setProperty('--clr-bg-content',    tokens.bgContent)
    r.style.setProperty('--clr-bg-content-image', tokens.bgContentImage ? `url("${tokens.bgContentImage}")` : 'none')
    r.style.setProperty('--clr-bg-agent',      tokens.bgAgent)
    r.style.setProperty('--clr-bg-agent-image', tokens.bgAgentImage ? `url("${tokens.bgAgentImage}")` : 'none')
    r.style.setProperty('--clr-bg-card',       tokens.bgCard)
    r.style.setProperty('--clr-text-primary',  tokens.textPrimary)
    r.style.setProperty('--clr-text-muted',    tokens.textMuted)
    r.style.setProperty('--clr-border',        tokens.borderColor)
    r.style.setProperty('--clr-card-radius',   tokens.cardRadius + 'px')
  }

  watch(tokens, applyToRoot, { deep: true })

  const snapshot = () => ({ ...tokens })

  const setToken = (key, value) => {
    history.value.push(snapshot())
    redoStack.value = []
    tokens[key] = value
  }

  const undo = () => {
    if (!history.value.length) return
    redoStack.value.push(snapshot())
    Object.assign(tokens, history.value.pop())
  }

  const redo = () => {
    if (!redoStack.value.length) return
    history.value.push(snapshot())
    Object.assign(tokens, redoStack.value.pop())
  }

  const reset = () => {
    history.value.push(snapshot())
    redoStack.value = []
    Object.assign(tokens, DEFAULTS)
  }

  // 初始化时加载
  loadFromStorage()
  applyToRoot()

  return { tokens, canUndo, canRedo, setToken, undo, redo, reset, applyToRoot, saveToStorage, loadFromStorage }
})
