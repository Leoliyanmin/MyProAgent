import { DEFAULTS } from '../stores/theme.js'

const THEME_BLOCK_RE = /```theme-suggestion\s*\n([\s\S]*?)\n```/g
const DELETE_CONFIRM_RE = /```delete-confirm\s*\n([\s\S]*?)\n```/g

const VALID_KEYS = new Set(Object.keys(DEFAULTS))

function sanitizeTokens(raw) {
  const tokens = {}
  for (const [key, value] of Object.entries(raw)) {
    if (!VALID_KEYS.has(key)) continue
    if (typeof value === 'string' && /^#[0-9a-fA-F]{6}$/.test(value)) {
      tokens[key] = value
    }
  }
  return tokens
}

function parseDeleteFiles(raw) {
  try {
    const arr = JSON.parse(raw)
    if (Array.isArray(arr)) {
      return arr.filter((item) => typeof item === 'string' && item.trim().length > 0)
    }
  } catch {
    return raw
      .split('\n')
      .map((line) => line.trim().replace(/^["',]|["',]$/g, ''))
      .filter((line) => line.length > 0)
  }
  return []
}

export function useMessageParser() {
  function parse(text) {
    if (!text) return [{ type: 'text', content: '' }]

    const segments = []
    let lastIndex = 0

    const allMatches = []

    THEME_BLOCK_RE.lastIndex = 0
    let match
    while ((match = THEME_BLOCK_RE.exec(text)) !== null) {
      allMatches.push({ index: match.index, end: match.index + match[0].length, type: 'theme', raw: match[1] })
    }

    DELETE_CONFIRM_RE.lastIndex = 0
    while ((match = DELETE_CONFIRM_RE.exec(text)) !== null) {
      allMatches.push({ index: match.index, end: match.index + match[0].length, type: 'delete', raw: match[1] })
    }

    allMatches.sort((a, b) => a.index - b.index)

    for (const m of allMatches) {
      if (m.index > lastIndex) {
        segments.push({ type: 'text', content: text.slice(lastIndex, m.index) })
      }

      if (m.type === 'theme') {
        try {
          const tokens = sanitizeTokens(JSON.parse(m.raw))
          if (Object.keys(tokens).length > 0) {
            segments.push({ type: 'theme-suggestion', tokens })
          } else {
            segments.push({ type: 'text', content: text.slice(m.index, m.end) })
          }
        } catch {
          segments.push({ type: 'text', content: text.slice(m.index, m.end) })
        }
      } else if (m.type === 'delete') {
        const files = parseDeleteFiles(m.raw)
        if (files.length > 0) {
          segments.push({ type: 'delete-confirm', files })
        } else {
          segments.push({ type: 'text', content: text.slice(m.index, m.end) })
        }
      }

      lastIndex = m.end
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