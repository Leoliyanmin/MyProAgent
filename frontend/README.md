# ProAgent - 智能协作工作台

ProAgent 是一个基于 Vue 3 的智能协作工作台，帮助团队高效管理任务、日程、文件和个人画像。

![版本](https://img.shields.io/badge/version-0.0.0-blue)
![Vue](https://img.shields.io/badge/Vue-3.5.29-green)
![Vite](https://img.shields.io/badge/Vite-7.3.1-yellow)

## ✨ 功能特性

### 🔐 用户认证 (Authentication)
- **登录页面** - 邮箱密码登录，JWT Token 认证
- **注册页面** - 支持邮箱验证码注册
- **自动登录** - 刷新页面保持登录状态
- **退出登录** - 侧边栏 Sign Out 按钮安全退出

### 📊 工作台概览 (Dashboard)
- **可拖拽布局** - 使用 vue3-grid-layout 实现自由拖拽和调整大小的组件布局
- **四种小组件**:
  - 📈 热力图 (WidgetHeatmap) - 可视化工作统计
  - 📝 便签 (WidgetNotes) - 快速记录想法
  - ✅ 待办事项 (WidgetTodo) - 带优先级和时间的任务管理
  - 💬 消息 (WidgetMessages) - 团队消息通知
- **自定义模式** - 支持编辑模式保存个人布局偏好

### 📅 日历管理 (Calendar)
- **多视图支持** - 日视图、周视图、月视图一键切换
- **事件管理** - 添加、编辑、删除日程事件
- **多日事件** - 支持跨越多天的事件显示
- **待办集成** - 待办事项自动同步到日历
- **快速跳转** - 一键回到今天，前后导航

### 🎨 自我画像 (Self Portrait)
- **个人资料编辑** - 一句话介绍、当前重点目标、工作偏好
- **能力标签** - 选择技能标签展示专业能力
- **背景图片** - 支持自定义个人主页背景
- **评价系统** - 可邀请他人进行 360° 评价
- **成长时间线** - 记录里程碑和作品集

### 🎭 主题设置 (Theme Settings)
- **动态主题编辑** - 实时预览主题变化
- **色彩管理** - 自定义主题色、背景色
- **主题切换** - 一键应用/重置主题配置

### 📁 文件管理 (File Manager)
- **文件浏览** - 清晰的文件列表展示
- **快速操作** - 支持文件上传、下载、删除

### ⚙️ 用户设置 (User Settings)
- **账户信息** - 修改用户名、邮箱、密码
- **通知偏好** - 自定义消息提醒方式
- **隐私设置** - 管理数据分享权限
- **系统信息** - 查看版本号和存储空间

## 🛠️ 技术栈

- **框架**: Vue 3.5.29 + Composition API
- **构建工具**: Vite 7.3.1
- **状态管理**: Pinia 3.0.4
- **UI 组件**:
  - vue3-grid-layout - 拖拽布局
  - 自定义 Vue 组件
- **图表**: ECharts ^6.0.0
- **图标**: 自定义 SVG 图标组件

## 📦 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── layout/           # 布局组件
│   │   │   ├── AgentSidebar.vue
│   │   │   ├── SidebarLeft.vue      # 左侧边栏（含退出登录）
│   │   │   ├── TopBar.vue
│   │   │   └── ThemeOverlayEditor.vue
│   │   ├── widgets/          # 仪表板小部件
│   │   │   ├── WidgetHeatmap.vue
│   │   │   ├── WidgetMessages.vue
│   │   │   ├── WidgetNotes.vue
│   │   │   └── WidgetTodo.vue
│   │   └── icons/            # 图标组件
│   ├── views/                # 页面视图
│   │   ├── LoginView.vue            # 登录页面
│   │   ├── RegisterView.vue         # 注册页面
│   │   ├── DashboardView.vue
│   │   ├── CalendarView.vue
│   │   ├── SelfPortraitView.vue
│   │   ├── ThemeSettingsView.vue
│   │   ├── FileManagerView.vue
│   │   └── UserSettingsView.vue
│   ├── stores/               # Pinia 状态管理
│   │   ├── auth.js                  # 认证状态（token、用户信息）
│   │   ├── dashboard.js
│   │   ├── theme.js
│   │   └── calendar.js
│   ├── services/             # API 服务
│   │   └── api.js                   # 封装后端 API 调用
│   ├── router/               # Vue Router
│   │   ├── index.js
│   │   └── guards.js                # 路由守卫（认证检查）
│   ├── App.vue
│   └── main.js
├── public/
├── index.html
├── package.json
└── vite.config.js
```

## 🚀 快速开始

### 环境要求

- **Node.js**: ^20.19.0 || >=22.12.0
- **包管理器**: npm

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173 查看应用

### 后端 API 配置

前端通过 Vite 代理连接后端，配置在 `vite.config.js`：

```javascript
server: {
  proxy: {
    '/auth': { target: 'http://localhost:8002' },  // Local Backend
    '/tasks': { target: 'http://localhost:8002' },
    '/schedules': { target: 'http://localhost:8002' },
    '/agent': { target: 'http://localhost:8002' },
    '/sync': { target: 'http://localhost:8002' }
  }
}
```

确保 Local Backend 在 http://localhost:8002 运行

### 生产构建

```bash
npm run build
```

构建后的文件位于 `dist/` 目录

### 预览生产版本

```bash
npm run preview
```

## 💻 推荐的开发环境

### IDE

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) 插件（建议禁用 Vetur）

### 浏览器调试工具

**Chromium 浏览器** (Chrome, Edge, Brave 等):
- [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
- [启用 Chrome DevTools 自定义对象格式化器](http://bit.ly/object-formatters)

**Firefox**:
- [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
- [启用 Firefox DevTools 自定义对象格式化器](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## 📝 开发指南

### 添加认证保护的路由

在 `router/index.js` 中添加 `requiresAuth: true`：

```javascript
{
  path: '/dashboard',
  name: 'dashboard',
  component: () => import('../views/DashboardView.vue'),
  meta: { requiresAuth: true }  // 需要登录
}
```

### 在组件中使用认证状态

```javascript
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

// 检查登录状态
if (auth.isAuthenticated) {
  console.log('当前用户:', auth.user)
}

// 调用退出
const handleLogout = () => {
  auth.logout()
}
```

### 添加新的小部件

1. 在 `src/components/widgets/` 创建新组件
2. 在 `DashboardView.vue` 的 `componentMap` 中注册
3. 更新布局配置 `layoutConfig`

### 状态管理

使用 Pinia 管理全局状态:

```javascript
import { useDashboardStore } from '../stores/dashboard'
import { useAuthStore } from '../stores/auth'

const dashboardStore = useDashboardStore()
const authStore = useAuthStore()

// 认证相关
authStore.login(email, password)    // 登录
authStore.logout()                  // 退出
authStore.isAuthenticated           // 是否已登录
```

### 自定义主题

主题配置存储在 `src/stores/theme.js`，支持:
- 主色调
- 背景色
- 边框样式
- 阴影效果

## 📄 配置文件

查看 [Vite Configuration Reference](https://vite.dev/config/) 了解更多配置选项。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目仅供学习和教学使用。

---

Made with ❤️ by Team 26S-27
