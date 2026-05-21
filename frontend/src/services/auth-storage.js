let isTauriEnv = false
try {
  isTauriEnv = !!(window.__TAURI_INTERNALS__ || window.__TAURI__)
} catch { /* browser env */ }

const STORE_KEY = 'auth-session'

// Default: 7 days in seconds. Override via VITE_SESSION_TTL env var.
let sessionTTLSeconds = 7 * 24 * 60 * 60
if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_SESSION_TTL) {
  const parsed = parseInt(import.meta.env.VITE_SESSION_TTL, 10)
  if (!isNaN(parsed) && parsed > 0) sessionTTLSeconds = parsed
}

function sessionTTLMs() {
  return sessionTTLSeconds * 1000
}

// ── Tauri store (lazy) ──
let _store = null
let _storeModule = null

async function ensureStore() {
  if (_store) return
  if (!_storeModule) {
    _storeModule = await import('@tauri-apps/plugin-store')
  }
  _store = await _storeModule.load('auth-store.json', { autoSave: true })
}

// ── In-memory cache ──
let _cachedToken = null

// ── Public API ─────────────────────────────────────────────────────

/** Configure session TTL at runtime (seconds). */
export function setSessionTTL(seconds) {
  if (typeof seconds === 'number' && seconds > 0) {
    sessionTTLSeconds = seconds
  }
}

/** Read current session TTL in seconds. */
export function getSessionTTL() {
  return sessionTTLSeconds
}

/** Persist auth session. */
export async function saveAuth(session) {
  const payload = {
    token: session.token,
    user_email: session.user_email || '',
    expires_at: Date.now() + sessionTTLMs(),
  }
  _cachedToken = session.token

  if (isTauriEnv) {
    await ensureStore()
    await _store.set(STORE_KEY, payload)
    await _store.save()
  } else {
    localStorage.setItem(STORE_KEY, JSON.stringify(payload))
  }
}

/**
 * Load persisted session.
 *
 * Returns:
 *   { token: string, user_email: string } — valid session
 *   { token: null, expired: true }       — session existed but expired (cleaned up)
 *   null                                  — no session stored at all
 */
export async function loadAuth() {
  let raw = null

  if (isTauriEnv) {
    await ensureStore()
    raw = await _store.get(STORE_KEY)
  } else {
    const stored = localStorage.getItem(STORE_KEY)
    if (stored) {
      try { raw = JSON.parse(stored) } catch { raw = null }
    }
  }

  if (!raw || !raw.token) {
    _cachedToken = null
    return null
  }

  if (raw.expires_at && Date.now() > raw.expires_at) {
    // Expired — clean up and signal the caller
    await clearAuth()
    return { token: null, expired: true }
  }

  _cachedToken = raw.token
  return { token: raw.token, user_email: raw.user_email || '' }
}

/** Remove persisted session (sign out). */
export async function clearAuth() {
  _cachedToken = null
  if (isTauriEnv) {
    await ensureStore()
    await _store.delete(STORE_KEY)
    await _store.save()
  }
  localStorage.removeItem(STORE_KEY)
}

/** Extend current session TTL (e.g. on user activity). */
export async function refreshSessionTTL() {
  if (isTauriEnv) {
    await ensureStore()
    const raw = await _store.get(STORE_KEY)
    if (raw && raw.token) {
      raw.expires_at = Date.now() + sessionTTLMs()
      await _store.set(STORE_KEY, raw)
      await _store.save()
    }
  } else {
    const stored = localStorage.getItem(STORE_KEY)
    if (stored) {
      try {
        const raw = JSON.parse(stored)
        raw.expires_at = Date.now() + sessionTTLMs()
        localStorage.setItem(STORE_KEY, JSON.stringify(raw))
      } catch { /* corrupt */ }
    }
  }
}

/** Synchronous token read for api.js — relies on cache populated by loadAuth()/saveAuth(). */
export function getTokenSync() {
  if (_cachedToken) return _cachedToken
  if (isTauriEnv) return null
  try {
    const raw = JSON.parse(localStorage.getItem(STORE_KEY))
    if (raw && raw.token && (!raw.expires_at || Date.now() <= raw.expires_at)) {
      _cachedToken = raw.token
      return raw.token
    }
  } catch { /* ignore */ }
  return null
}
