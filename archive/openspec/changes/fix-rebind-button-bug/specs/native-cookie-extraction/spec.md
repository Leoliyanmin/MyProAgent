## Capability: native-cookie-extraction

使用 Tauri 原生 Cookie API 从 webview 中提取所有 Cookie（包括 HttpOnly），替代 `document.cookie` JS eval 方式。

### Behavior

#### 提取指定平台 Cookie

- **输入**: `platform`（`"tis"` 或 `"blackboard"`）
- **处理**:
  1. 根据 platform 确定目标 URL：
     - `"tis"` → `https://tis.sustech.edu.cn`
     - `"blackboard"` → `https://bb.sustech.edu.cn`
  2. 调用 `app.cookies_for_url(url)` 获取该 URL 下所有 Cookie
  3. 过滤仅保留目标域名的 Cookie
  4. 将 Tauri Cookie 对象转换为前端可用的 JSON 格式
- **输出**: Cookie 列表（JSON 数组），每个元素包含 `name`、`value`、`domain`、`path`、`secure`、`httpOnly` 字段
- **错误**: 若 webview 不存在或 API 调用失败，返回空列表并记录错误日志

#### 提取所有平台 Cookie

- **输入**: 无
- **处理**:
  1. 分别对 TIS 和 Blackboard URL 调用 `app.cookies_for_url(url)`
  2. 合并结果
- **输出**: 包含两个平台 Cookie 的 JSON 对象 `{ tis: [...], blackboard: [...] }`

### Constraints

- 仅在 Tauri webview 上下文中可用，不能在浏览器环境中使用
- Cookie 仅在本地进程内传递给后端，不暴露给网页 JS
- 需要依赖 Tauri v2.8+（`cookies_for_url` API 引入版本）
- 必须在 `Cargo.toml` 的 `tauri` features 中启用 `cookies` feature

### Dependencies

- Tauri v2.8+ with `cookies` feature enabled
- `tauri::Manager` trait for `app.cookies_for_url()`
