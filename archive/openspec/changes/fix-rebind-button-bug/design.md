## Architecture

本次修复不引入新架构，仅修改现有绑定流程中的三个关键环节：Cookie 提取、窗口管理、错误反馈。

### 数据流（修复后）

```
用户点击"绑定TIS/BB"
  → open_cas_login(platform)
    → 检查同标签窗口是否已存在
      → 已存在: webview.focus()，返回现有窗口
      → 不存在: WebviewBuilder::new() 创建新窗口
  → 用户在 CAS 窗口登录
  → 用户点击"完成登录，开始绑定"
  → completeBinding(platform)
    → invoke('extract_cookies', { platform })
      → app.cookies_for_url(url) 获取所有 Cookie（含 HttpOnly）
      → 过滤目标域名 Cookie
      → 返回 Cookie 列表
    → Cookie 列表为空?
      → 是: 显示错误提示"未检测到登录信息，请确认已在弹出窗口中完成登录"
      → 否: invoke('bind_tis'/'bind_blackboard', { cookies })
        → 后端处理绑定
        → 刷新绑定状态
```

## Components

### Component: `extract_cookies` 命令（Rust）

**变更**: 用 Tauri 原生 Cookie API 替换 `document.cookie` JS eval

**当前实现**:
```rust
let cookies_js = "document.cookie";
let cookies_str = webview.eval(cookies_js).await?;
// 解析 "key1=val1; key2=val2" 格式
```

**修复后实现**:
```rust
let all_cookies = app.cookies_for_url(url)?;
// 过滤目标域名，返回 Vec<Cookie>
```

**关键差异**:
- `document.cookie` 无法读取 HttpOnly Cookie（JSESSIONID、TGC 等 CAS 核心 Cookie）
- `cookies_for_url` 返回所有 Cookie，包括 HttpOnly
- cas-demo 的 `extract_all_cookies` 已使用此 API，可参考

### Component: `open_cas_login` 命令（Rust）

**变更**: 增加窗口存在性检查

**当前实现**:
```rust
let webview = WebviewBuilder::new(url, WebviewUrl::External(url.parse()?))
    .label(label)
    ...;
webview_builder.build()?;
```

**修复后实现**:
```rust
// 先检查同标签窗口是否已存在
if let Some(existing) = app.get_webview(label) {
    existing.set_focus()?;
    return Ok("窗口已存在，已聚焦");
}
// 不存在则创建新窗口
let webview = WebviewBuilder::new(url, WebviewUrl::External(url.parse()?))
    .label(label)
    ...;
webview_builder.build()?;
```

### Component: `completeBinding` 函数（Vue）

**变更**: 增加 Cookie 为空时的错误反馈

**当前实现**:
```typescript
async function completeBinding(platform: string) {
    const cookies = await invoke('extract_cookies', { platform });
    if (!cookies || cookies.length === 0) {
        tisBindingStatus.value = 'unbound'; // 静默失败
        return;
    }
    // ... 调用后端绑定
}
```

**修复后实现**:
```typescript
async function completeBinding(platform: string) {
    const cookies = await invoke('extract_cookies', { platform });
    if (!cookies || cookies.length === 0) {
        // 显示错误提示
        ElMessage.error('未检测到登录信息，请确认已在弹出窗口中完成登录');
        tisBindingStatus.value = 'unbound';
        return;
    }
    // ... 调用后端绑定
}
```

## Data Model

无数据模型变更。Cookie 提取结果的数据结构保持不变（`Vec<Cookie>`），仅提取方式变更。

## API

无 API 变更。前端 `invoke` 调用签名不变，后端路由不变。

## Security

- **修复后安全性提升**: 使用原生 Cookie API 不增加安全风险，`cookies_for_url` 仅在 Tauri webview 上下文中可用
- **HttpOnly Cookie**: 这些 Cookie 仅在本地 Tauri 进程中传递给后端，不会暴露给网页 JS，安全性不变
- **窗口标签**: 使用固定标签名（`cas-tis`、`cas-bb`）确保窗口唯一性

## Performance

- Cookie 提取从 JS eval（异步、需等待 webview 执行）变更为原生 API 调用（同步），性能提升
- 窗口存在性检查为 O(1) 操作，无性能影响
