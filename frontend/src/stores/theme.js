import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'

export const DEFAULTS = {
  bgSidebar:   '#ebebeb',
  bgTopbar:    '#ebebeb',
  bgContent:   '#f5f5f7',
  bgAgent:     '#ebebeb',
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
        const parsed = JSON.parse(saved)
        for (const key of Object.keys(DEFAULTS)) {
          if (typeof parsed[key] === 'string') {
            tokens[key] = parsed[key]
          }
        }
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
    r.style.setProperty('--clr-bg-app',        '#ffffff')
    r.style.setProperty('--clr-bg-app-image',  'none')
    r.style.setProperty('--clr-bg-sidebar',    tokens.bgSidebar)
    r.style.setProperty('--clr-bg-sidebar-image', 'none')
    r.style.setProperty('--clr-bg-topbar',     tokens.bgTopbar)
    r.style.setProperty('--clr-bg-topbar-image', 'none')
    r.style.setProperty('--clr-bg-content',    tokens.bgContent)
    r.style.setProperty('--clr-bg-content-image', 'none')
    r.style.setProperty('--clr-bg-agent',      tokens.bgAgent)
    r.style.setProperty('--clr-bg-agent-image', 'none')
    r.style.setProperty('--clr-bg-card',       '#ffffff')
    r.style.setProperty('--clr-text-primary',  '#000000')
    r.style.setProperty('--clr-text-secondary', '#000000')
    r.style.setProperty('--clr-text-muted',    '#000000')
  }

  watch(tokens, () => {
    applyToRoot()
    saveToStorage()
  }, { deep: true })

  const snapshot = () => ({ ...tokens })

  const setToken = (key, value) => {
    if (!(key in DEFAULTS)) return
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

  const applySuggestion = (suggestedTokens) => {
    history.value.push(snapshot())
    redoStack.value = []
    for (const [key, value] of Object.entries(suggestedTokens)) {
      if (key in DEFAULTS) {
        tokens[key] = value
      }
    }
  }

  // 初始化时加载
  loadFromStorage()
  applyToRoot()

  return { tokens, canUndo, canRedo, setToken, undo, redo, reset, applyToRoot, saveToStorage, loadFromStorage, applySuggestion }
})
