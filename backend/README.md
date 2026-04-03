# SUSTech Student Productivity Agent - Backend

SUSTech学生生产力助手后端服务，提供用户认证、日程管理、任务管理、AI助手交互等功能的RESTful API。

## ⚠️ 重要说明

### 架构分工

本项目采用**分层架构**，各层职责如下：

| 层级 | 职责 | 实现状态 |
|------|------|----------|
| **Presentation Layer** (表现层) | API路由、请求/响应模型、认证依赖 | ✅ 已实现 |
| **Service Layer** (服务层) | 业务编排、数据转换、流程控制 | ✅ 已实现 |
| **Business Layer** (业务层) | 核心业务逻辑、规则验证 | ✅ 已实现 |
| **Database Layer** (数据库层) | 数据持久化、数据库操作 | 🔄 **Mock实现** |

### 数据库层说明

**当前实现**：数据库层使用 **SQLite + SQLAlchemy** 进行Mock实现，用于本地开发和功能演示。

**实际部署**：数据库层将由另一位团队成员负责实现，计划替换为：
- 生产数据库：PostgreSQL / MySQL
- 连接池管理
- 分布式事务支持
- 数据库迁移工具（Alembic）

**接口契约**：数据库层通过 `repositories.py` 暴露以下接口，后续替换时需保持接口兼容：

```python
# UserRepository
- create_user(user_data: dict) -> User
- get_user_by_email(email: str) -> Optional[User]
- get_user_by_id(user_id: int) -> Optional[User]
- update_user(user_id: int, update_data: dict) -> Optional[User]
- delete_user(user_id: int) -> bool

# ScheduleRepository
- create_schedule(schedule_data: dict) -> Schedule
- get_schedules_by_user(user_id: int) -> List[Schedule]
- get_schedule_by_id(schedule_id: int) -> Optional[Schedule]
- update_schedule(schedule_id: int, update_data: dict) -> Optional[Schedule]
- delete_schedule(schedule_id: int) -> bool

# TaskRepository
- create_task(task_data: dict) -> Task
- get_tasks_by_user(user_id: int) -> List[Task]
- get_task_by_id(task_id: int) -> Optional[Task]
- update_task(task_id: int, update_data: dict) -> Optional[Task]
- delete_task(task_id: int) -> bool

# AgentChatRepository
- create_chat_message(chat_data: dict) -> AgentChat
- get_chat_history_by_session(session_id: str) -> List[AgentChat]
- get_chat_history_by_user(user_id: int) -> List[AgentChat]
```

## 技术栈

- **框架**: FastAPI 0.104.1
- **服务器**: Uvicorn
- **数据库**: SQLite (Mock) / PostgreSQL (生产环境)
- **ORM**: SQLAlchemy 1.4.50
- **认证**: JWT (python-jose)
- **密码加密**: bcrypt (passlib)
- **数据验证**: Pydantic 1.10.12
- **环境配置**: python-dotenv

## 项目结构

```
backend/
├── config.py                 # 配置文件
├── main.py                   # 应用入口
├── requirements.txt          # 依赖包
├── .env.example             # 环境变量示例
├── .gitignore               # Git忽略文件
├── init_db.py               # 数据库初始化脚本
├── test_api.py              # API集成测试
├── layers/                   # 分层架构
│   ├── database/            # Database Layer (数据库层) - Mock实现
│   │   ├── __init__.py
│   │   ├── connection.py    # 数据库连接配置
│   │   ├── models.py        # SQLAlchemy数据模型
│   │   └── repositories.py  # 数据仓库（Mock实现）
│   ├── business/            # Business Layer (业务层)
│   │   ├── __init__.py
│   │   ├── auth_service.py  # 认证业务逻辑
│   │   ├── schedule_logic.py # 日程业务逻辑
│   │   ├── task_logic.py    # 任务业务逻辑
│   │   ├── agent_logic.py   # Agent业务逻辑
│   │   └── file_logic.py    # 文件业务逻辑
│   ├── service/             # Service Layer (服务层)
│   │   ├── __init__.py
│   │   ├── user_service.py  # 用户服务
│   │   ├── schedule_service.py # 日程服务
│   │   ├── task_service.py  # 任务服务
│   │   ├── agent_service.py # Agent服务
│   │   └── file_service.py  # 文件服务
│   └── presentation/        # Presentation Layer (表现层)
│       ├── __init__.py
│       ├── schemas.py       # Pydantic数据模型
│       ├── dependencies.py  # 依赖注入（JWT认证等）
│       ├── auth_routes.py   # 认证路由
│       ├── schedule_routes.py # 日程路由
│       ├── task_routes.py   # 任务路由
│       ├── agent_routes.py  # Agent路由
│       └── file_routes.py   # 文件路由
└── tests/                    # 单元测试
    ├── __init__.py
    ├── test_auth.py
    ├── test_schedules.py
    ├── test_tasks.py
    └── test_agent.py
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 应用配置
APP_NAME=SUSTech Student Productivity Agent
APP_VERSION=0.1.0
DEBUG=true

# 数据库配置（当前使用SQLite Mock）
DATABASE_URL=sqlite:///./app.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### 3. 初始化数据库

```bash
python init_db.py
```

这将创建SQLite数据库文件和表结构。

### 4. 启动服务

```bash
python main.py
```

或使用 uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API端点概览

### 认证模块
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| GET | `/auth/me` | 获取当前用户信息 |

### 日程管理模块
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/schedules/` | 获取用户日程列表 |
| POST | `/schedules/` | 创建日程 |
| PUT | `/schedules/{id}` | 更新日程 |
| DELETE | `/schedules/{id}` | 删除日程 |

### 任务管理模块
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/tasks/` | 获取用户任务列表 |
| POST | `/tasks/` | 创建任务 |
| PUT | `/tasks/{id}` | 更新任务 |
| DELETE | `/tasks/{id}` | 删除任务 |
| GET | `/tasks/study-plan` | 获取AI学习计划 |

### AI助手模块
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/agent/chat` | 与AI助手对话 |
| GET | `/agent/history/{session_id}` | 获取对话历史 |

### 文件管理模块
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/files/upload` | 上传文件 |
| GET | `/files/` | 获取文件列表 |
| GET | `/files/{file_id}` | 下载文件 |
| DELETE | `/files/{file_id}` | 删除文件 |

## 测试

### 运行集成测试

```bash
python test_api.py
```

这将测试所有API端点的功能，包括：
- 用户注册/登录
- 日程CRUD操作
- 任务CRUD操作
- AI助手对话

### 运行单元测试

```bash
pytest tests/
```

## 开发指南

### 添加新功能

1. **定义数据模型** (`layers/presentation/schemas.py`)
2. **实现业务逻辑** (`layers/business/`)
3. **实现服务层** (`layers/service/`)
4. **添加路由** (`layers/presentation/`)
5. **更新仓库接口** (`layers/database/repositories.py`) - 如果需要新数据操作

### 数据库层替换指南

当数据库层由另一位团队成员实现时：

1. 保持 `repositories.py` 中的接口方法签名不变
2. 修改 `connection.py` 中的数据库连接配置
3. 更新 `models.py` 中的模型定义（如有需要）
4. 修改 `.env` 中的 `DATABASE_URL` 为生产数据库连接字符串

## 注意事项

1. **当前数据库为Mock实现**：数据存储在本地SQLite文件中，不适合生产环境
2. **JWT密钥**：生产环境请使用强密钥并妥善保管
3. **CORS配置**：生产环境请限制允许的域名
4. **文件上传**：当前存储在本地，生产环境建议改为云存储

## 依赖版本说明

由于Python 3.13兼容性问题，以下依赖被固定为特定版本：
- `pydantic==1.10.12` (而非2.x)
- `sqlalchemy==1.4.50` (而非2.x)

请勿随意升级这些依赖，以免出现兼容性问题。

## 贡献者

- 后端架构与业务实现: [你的名字]
- 数据库层实现: [另一位成员的名字]

## License

MIT License
