# SUSTech CAS Cookie Extractor (Toy Demo)

在 Tauri WebView 中完成 SUSTech CAS 登录，提取所有 Cookie（包括 TGC）。

## 前置条件

- Node.js 20+ 
- Rust toolchain (rustup)
- Tauri v2 CLI

## 启动方式

```bash
# 1. 安装前端依赖
cd cas-demo
npm install

# 2. 启动 Tauri 开发模式
npm run tauri dev
```

> ⚠️ 首次启动会编译 Rust 代码，需要几分钟。

## 使用方法

1. 点击 **🔐 打开 CAS 登录** 按钮，弹出 SUSTech 统一认证窗口
2. 在弹窗中输入你的 SUSTech 账号密码完成登录
3. 登录成功后，页面会自动跳转到 tis.sustech.edu.cn
4. 如需 BB 系统的 Cookie，点击 **📚 跳转到 BB 系统**
5. 回到主窗口，点击 **🍪 提取已知域 Cookie** 或 **🍪🧹 提取全部 SUSTech Cookie**
6. 查看提取结果（TGC, session cookie 等）
7. 可 **📋 复制 JSON** 或 **💾 保存到文件** (~/.proagent/cas-cookies.json)

## 提取的 Cookie 域

| 域名 | 说明 |
|------|------|
| cas.sustech.edu.cn | TGC（CAS 统一认证票据）和其他 CAS Session Cookie |
| tis.sustech.edu.cn | 教学管理与服务平台 Session |
| bb.sustech.edu.cn | Blackboard Learn Session |

## 关键 API

- `WebviewWindow::cookies_for_url(url)` — 获取指定 URL 的所有 Cookie
- `WebviewWindow::cookies()` — 获取 WebView 中的所有 Cookie
- `WebviewUrl::External(url)` — 在新窗口中打开外部 URL

## 注意事项

- 需要 **Tauri v2.8+**（`cookies_for_url` API 在 v2.8 引入）
- macOS 使用 WKWebView，Windows 使用 WebView2，Cookie 存储与系统浏览器共享
- HttpOnly Cookie 可以被提取（这是 Rust 级别的 API，不受 JavaScript 限制）
- TGC Cookie 是 SUSTech CAS SSO 的核心令牌，有了它就能免登录访问所有 CAS 接入的服务