import { DEFAULTS } from '../stores/theme.js'

const THEME_BLOCK_RE = /```theme-suggestion\s*\n([\s\S]*?)\n```/g

const VALID_KEYS = new Set(Object.keys(DEFAULTS))

function sanitizeTokens(raw) {
  const tokens = {}
  for (const [key, value] of Object.entries(raw)) {
    if (!VALID_KEYS.has(key)) continue
    if (key === 'cardRadius') {
      const num = Number(value)
      if (!isNaN(num) && num >= 0 && num <= 24) tokens[key] = num
    } else if (typeof value === 'string') {
      if (value.startsWith('#') && /^#[0-9a-fA-F]{3,8}$/.test(value)) {
        tokens[key] = value
      } else if (value === '') {
        tokens[key] = value
      }
    }
  }
  return tokens
}

export function useMessageParser() {
  function parse(text) {
    if (!text) return [{ type: 'text', content: '' }]

    const segments = []
    let lastIndex = 0

    THEME_BLOCK_RE.lastIndex = 0
    let match

    while ((match = THEME_BLOCK_RE.exec(text)) !== null) {
      if (match.index > lastIndex) {
        segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
      }

      try {
        const tokens = sanitizeTokens(JSON.parse(match[1]))
        if (Object.keys(tokens).length > 0) {
          segments.push({ type: 'theme-suggestion', tokens })
        } else {
          segments.push({ type: 'text', content: match[0] })
        }
      } catch {
        segments.push({ type: 'text', content: match[0] })
      }

      lastIndex = match.index + match[0].length
    }

    if (lastIndex < text.length) {
      segments.push({ type: 'text', content: text.slice(lastIndex) })
    }

    if (segments.length === 0) {
      segments.push({ type: 'text', content: '' })
    }

    return segments
  }

  return { parse }
}