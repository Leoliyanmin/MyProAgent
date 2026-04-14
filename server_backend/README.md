# Server Backend - SUSTech Student Productivity Agent

## 概述

Server Backend 是 SUSTech Student Productivity Agent 项目的服务器端后端服务，主要负责用户认证、数据同步和远程备份。本服务部署在服务器端，为多个客户端提供集中式的认证和数据同步功能。

## 核心功能

- **用户认证**：用户注册、登录和身份验证
- **数据同步**：接收和发送同步数据
- **远程备份**：用户数据的远程存储和备份
- **安全管理**：密码验证和用户权限管理

## 技术架构

### 四层架构

1. **数据库层** (database/)
   - SQLite 数据库（生产环境可替换为PostgreSQL）
   - SQLAlchemy ORM
   - 数据模型和仓库模式

2. **业务层** (business/)
   - 认证服务 (auth_service.py)

3. **服务层** (service/)
   - 用户服务 (user_service.py)
   - 同步服务 (sync_service.py)

4. **表现层** (presentation/)
   - 路由定义 (auth_routes.py, sync_routes.py)
   - Pydantic模型 (schemas.py)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```env
# 应用配置
APP_NAME=SUSTech Student Productivity Agent (Server)
APP_VERSION=0.1.0
DEBUG=true

# 数据库配置（Server使用SQLite，生产环境可替换为PostgreSQL）
DATABASE_URL=sqlite:///./server_app.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

### 3. 初始化数据库

```bash
python database/code/database_init.py
```

### 4. 启动服务

**默认端口：8001**

```bash

uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 5. 访问API文档

打开浏览器访问：http://localhost:8001/docs

## API端点

| 模块 | 端点 | 方法 | 功能 |
|------|------|------|------|
| **认证** | /auth/register | POST | 用户注册 |
| **认证** | /auth/login | POST | 用户登录 |
| **同步** | /sync/from-client | POST | 接收客户端同步数据 |
| **同步** | /sync/to-client | GET | 向客户端发送同步数据 |

## 数据同步流程

1. **客户端 → 服务器**：
   - 客户端发送同步请求，包含数据类型和数据
   - 服务器验证用户身份
   - 服务器处理同步数据（创建或更新）
   - 服务器返回同步结果

2. **服务器 → 客户端**：
   - 客户端请求同步数据
   - 服务器验证用户身份
   - 服务器查询用户数据
   - 服务器返回同步数据

3. **同步数据类型**：
   - 日程数据 (schedules)
   - 任务数据 (tasks)
   - 聊天记录 (chats)

## 安全措施

- **密码验证**：服务器端密码验证
- **JWT认证**：使用JSON Web Token进行身份验证
- **HTTPS**：生产环境使用HTTPS传输
- **IP限制**：可配置访问IP限制
- **请求频率限制**：防止暴力攻击

## 性能优化

- **索引优化**：数据库查询索引
- **缓存机制**：常用数据缓存
- **异步处理**：异步处理同步请求
- **批量操作**：批量处理同步数据

## 开发指南

### 添加新功能

1. **业务逻辑**：在 `business/` 目录添加新的逻辑模块
2. **服务层**：在 `service/` 目录实现服务接口
3. **表现层**：在 `presentation/` 目录添加路由和Schema
4. **测试**：更新 `test_api.py` 添加测试用例

### 测试

运行服务器API测试：

```bash
python test_api.py
```

## 故障排除

### 常见问题

1. **认证失败**
   - 检查JWT密钥配置
   - 验证用户凭证
   - 查看认证日志

2. **同步失败**
   - 检查网络连接
   - 验证用户权限
   - 查看同步日志

3. **数据库连接失败**
   - 检查数据库配置
   - 验证数据库权限
   - 查看数据库状态

## 部署建议

### 开发环境
- 本地服务器或开发环境
- SQLite数据库
- 直接运行Python脚本

### 生产环境
- 云服务器或容器化部署
- PostgreSQL数据库
- Gunicorn + Nginx
- 配置HTTPS证书
- 定期备份数据库

### 扩展建议
- **水平扩展**：支持多实例部署
- **负载均衡**：配置负载均衡器
- **监控**：部署监控系统
- **日志管理**：集中式日志管理

## 依赖版本

| 依赖 | 版本 | 说明 |
|------|------|------|
| fastapi | 0.104.1 | Web框架 |
| uvicorn | 0.24.0 | ASGI服务器 |
| sqlalchemy | 1.4.50 | ORM框架 |
| pydantic | 1.10.12 | 数据验证 |
| python-jose | 3.3.0 | JWT库 |
| passlib | 1.7.4 | 密码加密 |

## 注意事项

- **数据库**：生产环境建议使用PostgreSQL
- **安全性**：生产环境必须使用HTTPS
- **性能**：根据用户量调整服务器配置
- **备份**：定期备份数据库
- **兼容性**：已适配Python 3.13，依赖版本固定

## 未来规划

- **多租户支持**：支持多个应用实例
- **高级认证**：OAuth2.0和第三方登录
- **数据统计**：用户数据统计和分析
- **API网关**：统一API管理和限流
- **微服务架构**：服务拆分和容器化
