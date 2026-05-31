import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsAPI } from '../services/api.js'

export const useDailyQuoteStore = defineStore('dailyQuote', () => {
  const text = ref('')
  const loading = ref(false)
  const history = ref([])

  async function load() {
    loading.value = true
    try {
      const data = await settingsAPI.get()
      text.value = data?.daily_quote || ''
    } catch {
      text.value = ''
    } finally {
      loading.value = false
    }
  }

  async function update(newText) {
    await settingsAPI.update({ daily_quote: newText })
    text.value = newText
  }

  async function refresh() {
    loading.value = true
    try {
      const res = await fetch('https://v1.hitokoto.cn/')
      const data = await res.json()
      text.value = data.hitokoto
      await settingsAPI.update({
        daily_quote: data.hitokoto,
        daily_quote_source: 'hitokoto',
        daily_quote_author: data.from_who || '',
        daily_quote_from: data.from || '',
      })
      return data.hitokoto
    } catch {
      throw new Error('获取失败，请检查网络')
    } finally {
      loading.value = false
    }
  }

  async function loadHistory() {
    try {
      history.value = await settingsAPI.getQuoteHistory()
    } catch {
      history.value = []
    }
  }

  function clear() {
    text.value = ''
  }

  return { text, loading, history, load, update, refresh, loadHistory, clear }
})
