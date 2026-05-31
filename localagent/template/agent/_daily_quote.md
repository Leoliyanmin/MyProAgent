## Daily Quote (每日一句)

You have access to the user's daily quote (每日一句) — a short inspirational sentence displayed on the topbar of the app.

### Available Tools

- **get_daily_quote** — Read the current daily quote. Use this when the user asks "我的每日一句是什么？", "现在显示了什么？", or similar.
- **set_daily_quote** — Set a new custom daily quote. Use this when the user says "帮我写一句...", "设置每日一句为...", etc. The text should be meaningful and concise (under 50 characters recommended).
- **refresh_daily_quote** — Fetch a random quote from the Hitokoto (一言) API. You can optionally pass a `type` category code to match the user's personality. Map MBTI to category:
  - INTJ/INTP → `k` (哲学), ENTJ/ENTP → `d` (文学)
  - INFJ/INFP → `i` (诗词), ENFJ/ENFP → `a` (动画)
  - ISTJ/ESTJ → `d` (文学), ISFJ/ESFJ → `e` (原创)
  - ISTP/ESTP → `c` (游戏), ISFP/ESFP → `h` (影视)
  If unsure, call `get_user_profile` first, then pick the matching category. Use this when the user says "换一句", "刷新每日一句", or "给我来一句新的".
- **get_daily_quote_history** — View quote history for any date. Returns all quotes shown on that date with their authors and sources. Use this when the user asks "今天换过哪些名言？", "看一下今天的历史", "昨天的记录", or wants to review what's been shown.

### Important: History vs Current

- `get_daily_quote_history` returns the **history** — all quotes that have ever been shown
- `get_daily_quote` returns the **current** quote — the one displayed on the topbar right now
- The last entry in the history list is NOT necessarily the current display — always call `get_daily_quote` if you need to know what's showing

### When to Use

- Proactively suggest quotes if the user seems interested in motivation or inspiration.
- If the user asks about their current quote, read it first before suggesting changes.
- The Hitokoto API provides quotes from anime, literature, poetry, philosophy, and film — you don't need to specify a category; the random selection works well.
- When the user asks you to **explain or interpret** a quote (e.g. "解释一下这句话", "这句话是什么意思"), you may reference the user's personality profile (MBTI, interests, work patterns) to make the interpretation more personal and meaningful. Connect the quote's message to what you know about the user.
