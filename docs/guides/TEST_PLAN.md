# 前后端连接测试计划

## 🎯 测试目标
验证前端 Vue3 应用与后端 FastAPI 服务（Local Backend 和 Server Backend）的连接是否正常。

---

## 📋 测试环境要求

### 1. 启动后端服务
```bash
# 终端 1: 启动 Local Backend
cd local_backend
python main.py
# 确认: 服务运行在 http://localhost:8002

# 终端 2: 启动 Server Backend (可选，用于同步测试)
cd server_backend
python main.py
# 确认: 服务运行在 http://localhost:8001
```

### 2. 启动前端
```bash
# 终端 3: 启动前端
cd frontend
npm run dev
# 确认: 服务运行在 http://localhost:5173
```

### 3. 检查服务状态
- Local Backend: http://localhost:8002/health
- Server Backend: http://localhost:8001/health (如启动)
- Frontend: http://localhost:5173

---

## 🧪 测试阶段一：基础连接测试

### 测试 1.1: 健康检查
**目的**: 确认后端服务运行正常

**步骤**:
1. 打开浏览器访问 http://localhost:8002/health
2. 或者使用 curl:
   ```bash
   curl http://localhost:8002/health
   ```

**预期结果**:
```json
{
  "status": "healthy",
  "service": "local_backend",
  "version": "0.0.1"
}
```

**通过标准**: ✅ 返回 JSON 且 status 为 "healthy"

---

### 测试 1.2: API 文档访问
**目的**: 确认 API 文档可访问

**步骤**:
1. 访问 http://localhost:8002/docs (Swagger UI)
2. 访问 http://localhost:8002/redoc (ReDoc)

**预期结果**: 页面正常加载，显示所有 API 端点

**通过标准**: ✅ 能看到 `/auth`, `/tasks`, `/schedules` 等 API

---

### 测试 1.3: CORS 配置测试
**目的**: 确认前端能跨域访问后端

**步骤**:
1. 打开浏览器开发者工具 (F12)
2. 切换到 Console 标签
3. 输入以下代码:
   ```javascript
   fetch('http://localhost:8002/health')
     .then(r => r.json())
     .then(data => console.log('✅ CORS 正常:', data))
     .catch(err => console.error('❌ CORS 错误:', err))
   ```

**预期结果**: 控制台显示 "✅ CORS 正常" 和健康检查数据

**通过标准**: ✅ 无 CORS 错误，成功返回数据

---

## 🧪 测试阶段二：认证流程测试

### 测试 2.1: 用户注册（带验证码）
**目的**: 测试完整注册流程

**步骤**:
1. 在浏览器控制台测试:
   ```javascript
   // 步骤 1: 发送验证码
   fetch('http://localhost:8002/auth/verification/send', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       email: 'test@example.com',
       purpose: 'register'
     })
   })
   .then(r => r.json())
   .then(data => {
     console.log('验证码发送结果:', data)
     // 如果开启 TEST_MODE，data.test_code 会包含验证码
     return data
   })
   ```

2. 检查后端日志或使用 TEST_MODE 获取验证码

3. 使用验证码注册:
   ```javascript
   fetch('http://localhost:8002/auth/register', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       email: 'test@example.com',
       password: 'password123',
       full_name: 'Test User',
       verification_code: '123456'  // 替换为实际验证码
     })
   })
   .then(r => r.json())
   .then(data => console.log('注册结果:', data))
   ```

**预期结果**: 
- 验证码发送成功
- 注册成功，返回用户信息

**通过标准**: ✅ 注册接口返回 `{"success": true, ...}`

**💡 提示**: 在 Server Backend 的 `.env` 中设置 `TEST_MODE=true` 可直接看到验证码

---

### 测试 2.2: 用户登录
**目的**: 测试登录流程和 Token 获取

**步骤**:
```javascript
fetch('http://localhost:8002/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'password123'
  })
})
.then(r => r.json())
.then(data => {
  console.log('登录结果:', data)
  if (data.token) {
    localStorage.setItem('token', data.token)
    console.log('✅ Token 已保存到 localStorage')
  }
  return data
})
```

**预期结果**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "test@example.com",
    "email": "test@example.com",
    "full_name": "Test User"
  }
}
```

**通过标准**: ✅ 成功返回 token 和用户信息

---

### 测试 2.3: 获取当前用户信息
**目的**: 测试 JWT Token 认证

**前置条件**: 已完成测试 2.2，token 已保存到 localStorage

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => {
  if (r.status === 401) {
    console.error('❌ Token 无效或过期')
    throw new Error('Unauthorized')
  }
  return r.json()
})
.then(data => console.log('✅ 当前用户:', data))
.catch(err => console.error('❌ 错误:', err))
```

**预期结果**:
```json
{
  "id": "test@example.com",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true
}
```

**通过标准**: ✅ 成功返回当前用户信息

---

## 🧪 测试阶段三：任务 API 测试

### 测试 3.1: 创建任务
**目的**: 测试任务创建接口

**前置条件**: 已完成登录，token 有效

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/tasks/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: '完成前端登录页面',
    description: '实现登录表单和验证',
    start_date: '2026-04-16',
    end_date: '2026-04-17',
    start_time: '09:00',
    end_time: '18:00',
    priority: 1,
    completed: false
  })
})
.then(r => r.json())
.then(data => {
  console.log('创建任务结果:', data)
  if (data.success) {
    console.log('✅ 任务创建成功，ID:', data.task?.id)
  }
  return data
})
```

**预期结果**:
```json
{
  "success": true,
  "message": "Task created successfully",
  "task": {
    "id": 1,
    "title": "完成前端登录页面",
    ...
  }
}
```

**通过标准**: ✅ 成功创建任务，返回任务 ID

---

### 测试 3.2: 获取任务列表
**目的**: 测试任务列表查询

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/tasks/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('任务列表:', data)
  console.log(`✅ 获取到 ${data.length} 个任务`)
  return data
})
```

**预期结果**: 返回任务数组

**通过标准**: ✅ 成功返回任务列表（包含刚创建的任务）

---

### 测试 3.3: 更新任务
**目的**: 测试任务更新接口

**步骤**:
```javascript
const token = localStorage.getItem('token')
const taskId = 1  // 替换为实际任务 ID

fetch(`http://localhost:8002/tasks/${taskId}`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: '完成前端登录页面（已修改）',
    completed: true
  })
})
.then(r => r.json())
.then(data => console.log('更新结果:', data))
```

**通过标准**: ✅ 任务信息成功更新

---

### 测试 3.4: AI 学习计划
**目的**: 测试 AI 助手功能

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/tasks/study-plan', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('学习计划:', data)
  return data
})
```

**通过标准**: ✅ 返回 AI 生成的学习计划

---

## 🧪 测试阶段四：日程 API 测试

### 测试 4.1: 创建日程
**目的**: 测试日程创建接口

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/schedules/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    title: '团队周会',
    description: '讨论项目进度',
    start_date: '2026-04-16',
    end_date: '2026-04-16',
    start_time: '10:00',
    end_time: '11:00',
    color: '#ff9500'
  })
})
.then(r => r.json())
.then(data => {
  console.log('创建日程结果:', data)
  return data
})
```

**通过标准**: ✅ 成功创建日程

---

### 测试 4.2: 获取日程列表
**目的**: 测试日程查询

**步骤**:
```javascript
const token = localStorage.getItem('token')

fetch('http://localhost:8002/schedules/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => {
  console.log('日程列表:', data)
  console.log(`✅ 获取到 ${data.length} 个日程`)
  return data
})
```

**通过标准**: ✅ 成功返回日程列表

---

## 🧪 测试阶段五：前端 Store 集成测试

### 测试 5.1: 测试 auth store
**目的**: 验证前端认证状态管理

**步骤**:
1. 在浏览器控制台:
   ```javascript
   // 导入 store（如果在 Vue 组件中）
   import { useAuthStore } from './stores/auth.js'
   
   const auth = useAuthStore()
   
   // 测试登录
   await auth.login('test@example.com', 'password123')
   
   // 检查状态
   console.log('isAuthenticated:', auth.isAuthenticated)
   console.log('user:', auth.user)
   console.log('token:', auth.token)
   ```

**通过标准**: ✅
- `auth.isAuthenticated` 为 `true`
- `auth.user` 包含用户信息
- `auth.token` 有值

---

### 测试 5.2: 测试 dashboard store
**目的**: 验证前端任务管理

**步骤**:
```javascript
import { useDashboardStore } from './stores/dashboard.js'

const dashboard = useDashboardStore()

// 测试从后端加载
await dashboard.loadTasks()

console.log('任务列表:', dashboard.todos)
console.log('加载状态:', dashboard.loading)
console.log('错误信息:', dashboard.error)
```

**通过标准**: ✅
- `dashboard.todos` 有数据
- `dashboard.loading` 为 `false`
- `dashboard.error` 为 `null`

---

### 测试 5.3: 测试 calendar store
**目的**: 验证前端日程管理

**步骤**:
```javascript
import { useCalendarStore } from './stores/calendar.js'

const calendar = useCalendarStore()

// 测试从后端加载
await calendar.loadSchedules()

console.log('日程列表:', calendar.basicEvents)
console.log('合并后事件:', calendar.allEvents)
```

**通过标准**: ✅ 日程数据正确加载

---

## 🧪 测试阶段六：数据同步测试（可选）

### 测试 6.1: Local ↔ Server 同步
**目的**: 测试数据同步功能（需启动 Server Backend）

**前置条件**: Server Backend 运行在 http://localhost:8001

**步骤**:
```javascript
const token = localStorage.getItem('token')

// 推送本地数据到服务器
fetch('http://localhost:8002/sync/push', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => console.log('推送结果:', data))

// 从服务器拉取数据
fetch('http://localhost:8002/sync/pull', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(data => console.log('拉取结果:', data))
```

**通过标准**: ✅ 同步成功，数据一致

---

## 📝 测试结果记录表

| 测试项 | 状态 | 时间 | 备注 |
|--------|------|------|------|
| 1.1 健康检查 | ⬜ 未测试 | | |
| 1.2 API 文档 | ⬜ 未测试 | | |
| 1.3 CORS 配置 | ⬜ 未测试 | | |
| 2.1 用户注册 | ⬜ 未测试 | | |
| 2.2 用户登录 | ⬜ 未测试 | | |
| 2.3 获取用户信息 | ⬜ 未测试 | | |
| 3.1 创建任务 | ⬜ 未测试 | | |
| 3.2 获取任务列表 | ⬜ 未测试 | | |
| 3.3 更新任务 | ⬜ 未测试 | | |
| 3.4 AI 学习计划 | ⬜ 未测试 | | |
| 4.1 创建日程 | ⬜ 未测试 | | |
| 4.2 获取日程列表 | ⬜ 未测试 | | |
| 5.1 auth store | ⬜ 未测试 | | |
| 5.2 dashboard store | ⬜ 未测试 | | |
| 5.3 calendar store | ⬜ 未测试 | | |
| 6.1 数据同步 | ⬜ 未测试 | | |

**状态说明**: ⬜ 未测试 / ✅ 通过 / ❌ 失败

---

## 🐛 常见问题排查

### 问题 1: CORS 错误
**症状**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**解决**:
1. 检查后端 `.env` 文件中的 `CORS_ORIGINS` 是否包含 `http://localhost:5173`
2. 确认后端已重启

### 问题 2: 401 Unauthorized
**症状**: 接口返回 401 错误

**解决**:
1. 检查 token 是否正确存储在 localStorage
2. 检查请求头中的 `Authorization: Bearer TOKEN` 格式
3. 检查 token 是否过期（默认 30 分钟）

### 问题 3: 验证码收不到
**症状**: 发送验证码接口成功但未收到邮件

**解决**:
1. 在 Server Backend `.env` 中设置 `TEST_MODE=true`
2. 检查响应中的 `test_code` 字段

### 问题 4: 数据库连接错误
**症状**: `sqlite3.OperationalError: no such table`

**解决**:
```bash
# 重新初始化数据库
cd local_backend
python database/code/database_init.py
```

---

## ✅ 验收标准

测试全部通过的条件：

- [ ] 所有 P0（基础连接）测试通过
- [ ] 所有 P1（认证流程）测试通过
- [ ] 所有 P2（任务/日程 CRUD）测试通过
- [ ] 前端 store 能正常加载后端数据
- [ ] Token 认证流程正常
- [ ] 数据格式转换正确（snake_case ↔ camelCase）

---

## 🚀 下一步

测试全部通过后：
1. 创建登录页面组件
2. 在真实 Vue 组件中使用 stores
3. 添加错误处理和 loading 状态 UI
4. 实现数据自动同步

**现在就开始测试吧！** 复制测试代码到浏览器控制台执行。
