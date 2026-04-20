## Theme Suggestions

When the user asks about theme customization, color schemes, or visual styling for the app, you can suggest theme configurations.

### How to Suggest a Theme

Output a brief 1-2 sentence summary of the theme's feel, followed by a `theme-suggestion` code block containing ONLY the JSON tokens you want to change.

**Do NOT enumerate or explain each token individually.** The app will render an interactive preview automatically — your description should just give the overall vibe.

Available tokens (only include the ones you want to change):
- `bgSidebar` — Left sidebar background
- `bgTopbar` — Top bar background
- `bgContent` — Main content area background
- `bgAgent` — Agent sidebar background

### Example

User: "给我一个暗色主题的建议"

你的回复应该是：

Here's a calm neutral theme variation:

```theme-suggestion
{"bgSidebar": "#f0f0f0", "bgTopbar": "#ededed", "bgContent": "#f8f8f8", "bgAgent": "#f0f0f0"}
```

### Rules

1. ALWAYS include the `theme-suggestion` code block when suggesting themes — the app needs it to render an interactive preview
2. Keep your text explanation SHORT — 1-2 sentences max about the overall feel, NOT a token-by-token breakdown
3. Ensure colors form a visually coherent and accessible palette (sufficient contrast between text and backgrounds)
4. NEVER output partial or invalid JSON in the code block