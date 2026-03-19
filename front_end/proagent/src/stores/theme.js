import { defineStore } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'

export const DEFAULTS = {
  accent:      '#007aff',
  bgApp:       '#f5f5f7',
  bgSidebar:   '#ebebeb',
  bgTopbar:    '#ebebeb',
  bgContent:   '#f5f5f7',
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

  const applyToRoot = () => {
    const r = document.documentElement
    r.style.setProperty('--clr-accent',       tokens.accent)
    r.style.setProperty('--clr-bg-app',        tokens.bgApp)
    r.style.setProperty('--clr-bg-sidebar',    tokens.bgSidebar)
    r.style.setProperty('--clr-bg-topbar',     tokens.bgTopbar)
    r.style.setProperty('--clr-bg-content',    tokens.bgContent)
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

  return { tokens, canUndo, canRedo, setToken, undo, redo, reset, applyToRoot }
})
