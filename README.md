# ProAgent - 智能协作工作台 (Full Stack)

这是一个完整的全栈应用，整合了前端 Vue3 界面和后端 FastAPI 服务。

![Version](https://img.shields.io/badge/version-0.0.0-blue)
![Vue](https://img.shields.io/badge/Vue-3.5.29-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688)

## 📁 项目结构

```
.
├── frontend/                   # Vue3 前端应用
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── layout/       # 布局组件 (Sidebar, TopBar)
│   │   │   ├── widgets/      # 仪表板小部件
│   │   │   └── icons/        # 图标组件
│   │   ├── views/            # 页面视图
│   │   │   ├── DashboardView.vue      # 工作台概览
│   │   │   ├── CalendarView.vue       # 日历管理
│   │   │   ├── SelfPortraitView.vue   # 自我画像
│   │   │   ├── ThemeSettingsView.vue  # 主题设置
│   │   │   ├── FileManagerView.vue    # 文件管理
│   │   │   └── UserSettingsView.vue   # 用户设置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── README.md             # 前端详细文档
│
├── backend/                   # FastAPI 后端服务
│   ├── local_backend/         # 本地后端 (FastAPI + SQLite)
│   │   ├── business/          # 业务逻辑
│   │   │   ├── agent_logic.py         # AI 助手逻辑
│   │   │   ├── auth_service.py        # 认证服务
│   │   │   ├── schedule_logic.py      # 日程逻辑
│   │   │   └── task_logic.py          # 任务逻辑
│   │   ├── database/          # 数据库层
│   │   │   └── code/
│   │   │       ├── database_init.sql       # 数据库初始化
│   │   │       ├── database_schedule_*.py   # 日程数据库操作
│   │   │       ├── database_task_*.py       # 任务数据库操作
│   │   │       ├── database_user_*.py       # 用户数据库操作
│   │   │       └── database_synchronize_*.py  # 数据同步操作
│   │   ├── presentation/      # API 路由
│   │   │   ├── agent_routes.py        # AI 助手接口
│   │   │   ├── auth_routes.py         # 认证接口
│   │   │   ├── schedule_routes.py     # 日程接口
│   │   │   ├── task_routes.py         # 任务接口
│   │   │   └── sync_routes.py         # 同步接口
│   │   ├── service/           # 服务层
│   │   ├── main.py            # 本地后端入口
│   │   └── requirements.txt   # 依赖
│   │
│   ├── server_backend/        # 服务器后端 (远程同步)
│   │   ├── business/          # 业务逻辑
│   │   │   ├── auth_service.py        # 认证服务
│   │   │   └── email_service.py       # 邮件服务
│   │   ├── database/          # 数据库层
│   │   ├── presentation/        # API 路由
│   │   ├── service/           # 服务层
│   │   ├── main.py            # 服务器后端入口
│   │   └── requirements.txt   # 依赖
│   │
│   ├── README.md              # 后端架构文档
│   ├── DATABASE_TESTING.md    # 数据库测试指南
│   ├── database_invoke_rules.md       # 数据库调用规范
│   └── database_synchronize_rules.md  # 数据同步规范
│
├── UI\ design/                # UI 设计资源 (图片)
├── .gitignore                 # Git 忽略规则
└── README.md                  # 本文档

```

## ✨ 功能特性

### 前端 (Vue3 + Vite)
- 📊 **工作台概览** - 可拖拽布局，热力图、便签、待办、消息组件
- 📅 **日历管理** - 日/周/月视图，事件管理，多日事件，待办同步
- 🎨 **自我画像** - 个人资料、技能标签、背景图片、360°评价
- 🎭 **主题设置** - 动态主题编辑、色彩管理
- 📁 **文件管理** - 文件浏览、上传、下载
- ⚙️ **用户设置** - 账户、通知、隐私、系统信息

### 后端 (FastAPI + SQLite)
- 🔐 **用户认证** - 注册/登录、JWT Token
- 📅 **日程管理** - 完整 CRUD、提醒通知
- ✅ **任务管理** - 完整 CRUD、优先级、时间
- 🤖 **AI 助手** - 智能对话、任务建议
- 🔄 **数据同步** - Local ↔ Server 双向同步
- 📧 **邮件服务** - 验证码、通知邮件
- 💾 **数据库** - SQLite 本地存储

## 🚀 快速开始

### 1. 启动后端 (Local)

```bash
cd backend/local_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置

# 初始化数据库
python database/code/database_init.py

# 启动服务
python main.py
```

后端服务将在 http://localhost:8000 运行

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 配置 API 地址
# 编辑 src/stores/ 中的 API URL 配置

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

### 3. 启动服务器后端 (可选，用于远程同步)

```bash
cd backend/server_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动服务
python main.py
```

## 🔧 开发指南

### 前后端通信

前端通过 HTTP API 与后端通信：

```javascript
// 示例: 获取日程列表
const response = await fetch('http://localhost:8000/api/schedules', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

### 数据库操作

后端提供统一的数据库操作接口：

```python
from database.code.database_schedule_operations import get_schedules
from database.code.database_task_operations import get_tasks
from database.code.database_user_operations import get_user
```

### 数据同步

Local 和 Server 之间通过 sync API 同步数据：

```python
# 本地推送数据到服务器
POST /api/sync/push

# 从服务器拉取数据
POST /api/sync/pull
```

## 📝 API 文档

启动后端后，访问自动生成的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue | 3.5.29 |
| 构建工具 | Vite | 7.3.1 |
| 状态管理 | Pinia | 3.0.4 |
| UI 布局 | vue3-grid-layout | 1.0.0 |
| 图表 | ECharts | ^6.0.0 |
| 后端框架 | FastAPI | 0.100+ |
| 数据库 | SQLite | 3 |
| ORM | SQLAlchemy | 2.0+ |
| 认证 | JWT | - |

## 📚 详细文档

- [前端详细文档](./frontend/README.md) - Vue3 开发指南
- [后端架构文档](./backend/README.md) - 系统架构设计
- [数据库测试指南](./backend/DATABASE_TESTING.md) - 数据库测试
- [数据库调用规范](./backend/database_invoke_rules.md)
- [数据同步规范](./backend/database_synchronize_rules.md)

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
