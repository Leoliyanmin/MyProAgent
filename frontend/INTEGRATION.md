# 前后端连接指南

本文档说明如何将前端 Vue3 应用连接到后端 FastAPI 服务。

## 📋 连接概览

### 架构关系
```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vue3)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  src/services/api.js          (API 服务层)           │  │
│  │  src/stores/auth.js            (认证状态)             │  │
│  │  src/stores/dashboard.js       (任务管理)             │  │
│  │  src/stores/calendar.js        (日程管理)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ HTTP API                          │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Vite Proxy (Development)                            │  │
│  │  - /auth/*  → http://localhost:8002/auth/*           │  │
│  │  - /tasks/* → http://localhost:8002/tasks/*          │  │
│  │  - /schedules/* → http://localhost:8002/schedules/*  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI + SQLite)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Local Backend: http://localhost:8002               │  │
│  │  - 用户认证 (JWT Token)                              │  │
│  │  - 任务管理 (CRUD)                                  │  │
│  │  - 日程管理 (CRUD)                                  │  │
│  │  - AI 助手                                          │  │
│  │  - 数据同步 (Local ↔ Server)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 已完成的连接

### 1. API 服务层 (`src/services/api.js`)

封装了所有后端 API 调用：

```javascript
// 认证 API
authAPI.login(email, password)
authAPI.register(email, password, full_name, code)
authAPI.sendVerificationCode(email, purpose)
authAPI.getCurrentUser()

// 任务 API  
tasksAPI.getTasks()
tasksAPI.createTask(taskData)
tasksAPI.updateTask(taskId, taskData)
tasksAPI.deleteTask(taskId)
tasksAPI.getStudyPlan()

// 日程 API
schedulesAPI.getSchedules()
schedulesAPI.createSchedule(scheduleData)
schedulesAPI.updateSchedule(scheduleId, scheduleData)
schedulesAPI.deleteSchedule(scheduleId)

// AI 助手 API
agentAPI.chat(message, session_id)
agentAPI.getHistory()

// 数据同步 API
syncAPI.pushToServer()
syncAPI.pullFromServer()
```

### 2. 认证状态 (`src/stores/auth.js`)

```javascript
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// 登录
await auth.login(email, password)

// 注册
await auth.register(email, password, full_name, code)

// 发送验证码
await auth.sendVerificationCode(email)

// 检查登录状态
if (auth.isAuthenticated) {
  console.log('Logged in as:', auth.user.full_name)
}
```

### 3. 任务/Dashboard 连接 (`src/stores/dashboard.js`)

原有的本地任务管理现在支持后端同步：

```javascript
import { useDashboardStore } from '../stores/dashboard.js'

const dashboard = useDashboardStore()

// 原有功能（本地状态）
dashboard.addTodo(task)
dashboard.updateTodo(task)
dashboard.toggleTodo(id)
dashboard.removeTodo(id)

// 新增：从后端加载任务
await dashboard.loadTasks()

// 新增：后端同步
await dashboard.createTaskOnBackend(taskData)
await dashboard.updateTaskOnBackend(taskId, taskData)
await dashboard.getStudyPlan()
```

**数据映射** (Frontend ↔ Backend)：

| Frontend | Backend |
|----------|---------|
| `id` | `id` |
| `title` | `title` |
| `start` | `start_date` |
| `end` | `end_date` |
| `startTime` | `start_time` |
| `endTime` | `end_time` |
| `priority` | `priority` |
| `completed` | `completed` |
| `color` | `color` |

### 4. 日程/Calendar 连接 (`src/stores/calendar.js`)

```javascript
import { useCalendarStore } from '../stores/calendar.js'

const calendar = useCalendarStore()

// 原有功能（合并了 Todo 事件和日程事件）
calendar.allEvents  // 计算属性，合并 dashboard.todos + basicEvents
calendar.addEvent(event)
calendar.updateEvent(event)
calendar.removeEvent(id)

// 新增：从后端加载日程
await calendar.loadSchedules()

// 新增：后端同步
await calendar.createScheduleOnBackend(eventData)
await calendar.updateScheduleOnBackend(scheduleId, eventData)
```

**数据映射** (Frontend ↔ Backend)：

| Frontend | Backend |
|----------|---------|
| `id` | `id` |
| `title` | `title` |
| `description` | `description` |
| `start` | `start_date` |
| `end` | `end_date` |
| `startTime` | `start_time` |
| `endTime` | `end_time` |
| `color` | `color` |

### 5. Vite 代理配置 (`vite.config.js`)

开发环境下，Vite 自动代理 API 请求到后端：

```javascript
server: {
  proxy: {
    '/auth': { target: 'http://localhost:8002' },
    '/tasks': { target: 'http://localhost:8002' },
    '/schedules': { target: 'http://localhost:8002' },
    '/agent': { target: 'http://localhost:8002' },
    '/sync': { target: 'http://localhost:8002' }
  }
}
```

## 🚀 启动步骤

### 1. 启动后端

```bash
cd local_backend

# 创建虚拟环境（首次）
python -m venv venv
source venv/bin/activate

# 安装依赖（首次）
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，确保包含：
# - DATABASE_URL
# - SECRET_KEY
# - CORS_ORIGINS=http://localhost:5173

# 初始化数据库
python database/code/database_init.py

# 启动服务
python main.py
# 或: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8002 运行
API 文档：http://localhost:8002/docs

### 2. 启动前端

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

### 3. 验证连接

打开浏览器控制台，测试 API：

```javascript
// 测试认证
fetch('/auth/me', {
  headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
})

// 测试任务
fetch('/tasks/')
  .then(r => r.json())
  .then(console.log)
```

## 📚 在组件中使用

### 示例：DashboardView 加载任务

```vue
<script setup>
import { onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboard.js'
import { useAuthStore } from '../stores/auth.js'

const dashboard = useDashboardStore()
const auth = useAuthStore()

onMounted(async () => {
  // 初始化认证
  await auth.initAuth()
  
  // 如果已登录，加载任务
  if (auth.isAuthenticated) {
    await dashboard.loadTasks()
  }
})
</script>
```

### 示例：CalendarView 加载日程

```vue
<script setup>
import { onMounted } from 'vue'
import { useCalendarStore } from '../stores/calendar.js'

const calendar = useCalendarStore()

onMounted(async () => {
  await calendar.loadSchedules()
})
</script>
```

### 示例：登录组件

```vue
<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')

const handleLogin = async () => {
  const result = await auth.login(email.value, password.value)
  
  if (result.success) {
    router.push('/dashboard')
  } else {
    alert(result.message)
  }
}
</script>
```

## ⚠️ 注意事项

### 1. 认证流程

所有需要认证的 API 会自动携带 Token：

```javascript
// api.js 中自动处理
const token = localStorage.getItem('token')
if (token) {
  headers['Authorization'] = `Bearer ${token}`
}
```

### 2. 错误处理

每个 store 都有 `loading` 和 `error` 状态：

```javascript
const dashboard = useDashboardStore()

if (dashboard.loading) {
  console.log('Loading...')
}

if (dashboard.error) {
  console.error('Error:', dashboard.error)
}
```

### 3. 数据格式转换

后端使用 `snake_case`，前端使用 `camelCase`：
- 后端: `start_date`, `end_date`
- 前端: `start`, `end`

转换自动在 store 中进行。

### 4. 开发 vs 生产

```javascript
// api.js
const API_BASE_URL = import.meta.env.DEV ? '' : 'http://localhost:8002'
```

- 开发：使用 Vite 代理（无前缀）
- 生产：使用完整 URL

## 🔧 下一步

1. **实现登录/注册页面** - 使用 `auth.js` store
2. **添加加载状态** - 在组件中显示 `loading` 状态
3. **错误提示** - 显示 API 错误信息
4. **数据持久化** - 确保 Token 保存在 localStorage
5. **自动同步** - 定期调用 `syncAPI.pushToServer()` 和 `pullFromServer()`

## 📖 API 文档

- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc
- 后端 README: `backend/README.md`
