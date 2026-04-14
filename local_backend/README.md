# Local Backend - SUSTech Student Productivity Agent

## 概述

Local Backend 是 SUSTech Student Productivity Agent 项目的本地后端服务，主要负责本地数据存储、核心业务逻辑和离线功能。本服务部署在用户设备本地，提供完整的功能集，确保在无网络环境下也能正常工作。

## 核心功能

- **用户认证**：本地用户管理和认证（与服务器同步）
- **日程管理**：完整的日程CRUD操作
- **任务管理**：任务创建、更新、删除和AI学习计划生成
- **AI助手**：智能对话和学习助手功能
- **文件管理**：本地文件存储和管理
- **数据同步**：与服务器后端的数据同步

## 技术架构

### 四层架构

1. **数据库层** (database/)
   - SQLite 本地数据库
   - SQLAlchemy ORM
   - 数据模型和仓库模式

2. **业务层** (business/)
   - 认证服务 (auth_service.py)
   - 日程逻辑 (schedule_logic.py)
   - 任务逻辑 (task_logic.py)
   - Agent逻辑 (agent_logic.py)

3. **服务层** (service/)
   - 用户服务 (user_service.py)
   - 日程服务 (schedule_service.py)
   - 任务服务 (task_service.py)
   - Agent服务 (agent_service.py)

4. **表现层** (presentation/)
   - 路由定义 (auth_routes.py, schedule_routes.py, etc.)
   - Pydantic模型 (schemas.py)
   - 依赖注入 (dependencies.py)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```env
# 应用配置
APP_NAME=SUSTech Student Productivity Agent (Local)
APP_VERSION=0.1.0
DEBUG=true

# 数据库配置（Local使用SQLite）
DATABASE_URL=sqlite:///./local_app.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# 服务器后端配置
SERVER_BACKEND_URL=http://localhost:8001
```

### 3. 初始化数据库

```bash
python database/code/database_init.py
```

### 4. 启动服务

**默认端口：8000**

```bash

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

打开浏览器访问：http://localhost:8000/docs

## API端点

| 模块 | 端点 | 方法 | 功能 |
|------|------|------|------|
| **认证** | /auth/register | POST | 用户注册 |
| **认证** | /auth/login | POST | 用户登录 |
| **认证** | /auth/me | GET | 获取当前用户信息 |
| **日程** | /schedules/ | GET | 获取用户日程列表 |
| **日程** | /schedules/ | POST | 创建日程 |
| **日程** | /schedules/{id} | PUT | 更新日程 |
| **日程** | /schedules/{id} | DELETE | 删除日程 |
| **任务** | /tasks/ | GET | 获取用户任务列表 |
| **任务** | /tasks/ | POST | 创建任务 |
| **任务** | /tasks/{id} | PUT | 更新任务 |
| **任务** | /tasks/{id} | DELETE | 删除任务 |
| **任务** | /tasks/study-plan | GET | 获取AI学习计划 |
| **Agent** | /agent/chat | POST | 与AI助手对话 |
| **Agent** | /agent/history/{session_id} | GET | 获取对话历史 |
| **同步** | /sync/to-server | POST | 同步数据到服务器 |
| **同步** | /sync/from-server | GET | 从服务器同步数据 |

## 离线功能

Local Backend 设计为支持离线使用：

1. **本地数据存储**：所有数据存储在本地SQLite数据库中
2. **离线认证**：用户登录信息本地验证
3. **功能完整性**：即使无网络也能使用所有核心功能
4. **自动同步**：网络恢复后自动与服务器同步数据

## 数据同步流程

1. **Local → Server**：
   - 本地数据变更时触发同步
   - 支持批量同步和增量同步
   - 网络异常时自动重试

2. **Server → Local**：
   - 用户登录时同步
   - 手动触发同步
   - 定期自动同步

3. **冲突处理**：
   - 本地数据优先原则
   - 服务器数据作为备份
   - 冲突时保留本地版本

## 安全措施

- **密码加密**：本地存储加密后的密码
- **JWT认证**：使用JSON Web Token进行身份验证
- **数据保护**：本地数据文件权限控制
- **网络传输**：使用HTTPS与服务器通信

## 性能优化

- **本地缓存**：频繁访问的数据本地缓存
- **延迟加载**：按需加载数据
- **批处理**：批量操作减少数据库访问
- **索引优化**：数据库查询优化

## 开发指南

### 添加新功能

1. **业务逻辑**：在 `business/` 目录添加新的逻辑模块
2. **服务层**：在 `service/` 目录实现服务接口
3. **表现层**：在 `presentation/` 目录添加路由和Schema
4. **测试**：更新 `test_api.py` 添加测试用例

### 测试

运行本地API测试：

```bash
python test_api.py
```

## 故障排除

### 常见问题

1. **数据库初始化失败**
   - 检查SQLite文件权限
   - 确保依赖包版本正确

2. **同步失败**
   - 检查网络连接
   - 验证服务器地址配置
   - 查看日志确认错误信息

3. **认证失败**
   - 检查JWT密钥配置
   - 验证用户凭证
   - 检查服务器认证服务状态

## 部署建议

### 本地部署
- 使用PyInstaller打包为可执行文件
- 配置为系统服务自动启动
- 定期备份本地数据库文件

### 移动设备部署
- 适配移动环境的资源使用
- 优化电池消耗
- 实现后台同步机制

## 依赖版本

| 依赖 | 版本 | 说明 |
|------|------|------|
| fastapi | 0.104.1 | Web框架 |
| uvicorn | 0.24.0 | ASGI服务器 |
| sqlalchemy | 1.4.50 | ORM框架 |
| pydantic | 1.10.12 | 数据验证 |
| python-jose | 3.3.0 | JWT库 |
| passlib | 1.7.4 | 密码加密 |
| requests | 2.31.0 | HTTP客户端 |

## 注意事项

- **数据库**：使用SQLite作为本地存储，适合单用户场景
- **性能**：本地操作速度快，但存储空间有限
- **安全性**：本地数据文件需要适当保护
- **兼容性**：已适配Python 3.13，依赖版本固定

## 未来规划

- **多用户支持**：支持多用户本地存储
- **数据导出**：支持本地数据导出和导入
- **智能同步**：基于网络状态的智能同步策略
- **扩展存储**：支持外部存储设备
