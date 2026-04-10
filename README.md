[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/py413vYq)
https://kcnshyb9xgl3.feishu.cn/wiki/VOTmwDTd1ipr9JkpZ27cW0BCnrb 就是feishu

## 项目进度
已完成local backend和server backend的基本框架，实现基本api接口，local与server backend之间的通信。 
目前未集成数据库，使用的是mock数据库。
数据集成，agent，寻友匹配，文件管理功能正在开发中，可在本框架下继续集成。

## 项目架构

# SUSTech Student Productivity Agent

## 项目概述

SUSTech Student Productivity Agent 是一个为南方科技大学学生设计的智能生产力助手，采用 **Local + Server** 双后端架构，提供本地离线功能和服务器同步备份能力。

## 系统架构

### 整体架构

```
┌─────────────────────────┐       ┌─────────────────────────┐
│                         │       │                         │
│  Local Backend          │◄──────►  Server Backend         │
│  (用户设备本地)         │       │  (服务器端)             │
│                         │       │                         │
├─────────────────────────┤       ├─────────────────────────┤
│  - 本地数据存储         │       │  - 用户认证             │
│  - 核心业务逻辑         │       │  - 数据同步             │
│  - 离线功能             │       │  - 远程备份             │
│  - 实时同步             │       │  - 安全管理             │
│                         │       │                         │
└─────────────────────────┘       └─────────────────────────┘
```

### 架构分工

| 组件 | 职责 | 部署位置 | 技术栈 |
|------|------|----------|--------|
| **Local Backend** | 本地数据存储、核心业务逻辑、离线功能 | 用户设备本地 | FastAPI + SQLite |
| **Server Backend** | 用户认证、数据同步、远程备份 | 服务器端 | FastAPI + SQLite (可替换为PostgreSQL) |

## 核心功能

### 功能模块分配

| 功能 | Local Backend | Server Backend |
|------|--------------|---------------|
| 用户注册/登录 | ✅ (本地验证 + 服务器同步) | ✅ (密码验证) |
| 日程管理 | ✅ (完整CRUD) | ✅ (同步备份) |
| 任务管理 | ✅ (完整CRUD) | ✅ (同步备份) |
| AI助手 | ✅ (完整功能) | ❌ (本地实现) |
| 文件管理 | ✅ (本地存储) | ❌ (本地实现) |
| 数据同步 | ✅ (发起同步) | ✅ (接收同步) |

## 系统流程

### 1. 用户注册流程

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Local as Local Backend
    participant Server as Server Backend
    
    Client->>Local: 注册请求
    Local->>Server: 转发注册请求
    Server->>Server: 验证邮箱和密码
    Server->>Server: 创建用户记录
    Server-->>Local: 返回注册结果
    Local->>Local: 存储本地用户信息
    Local-->>Client: 返回注册成功
```

### 2. 用户登录流程

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Local as Local Backend
    participant Server as Server Backend
    
    Client->>Local: 登录请求
    Local->>Local: 本地验证
    alt 本地验证成功
        Local-->>Client: 返回本地令牌
    else 本地验证失败
        Local->>Server: 服务器验证
        Server->>Server: 验证密码
        Server-->>Local: 返回服务器令牌
        Local->>Local: 同步用户信息
        Local-->>Client: 返回登录成功
    end
```

### 3. 数据同步流程

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Local as Local Backend
    participant Server as Server Backend
    
    alt 本地数据变更
        Client->>Local: 修改数据
        Local->>Local: 更新本地数据库
        Local->>Server: 同步到服务器
        Server->>Server: 存储同步数据
        Server-->>Local: 确认同步成功
    end
    
    alt 服务器数据同步
        Local->>Server: 请求同步数据
        Server->>Server: 查询用户数据
        Server-->>Local: 返回同步数据
        Local->>Local: 更新本地数据库
        Local-->>Client: 通知数据更新
    end
```

### 4. 任务管理流程

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Local as Local Backend
    participant Server as Server Backend
    
    Client->>Local: 创建任务
    Local->>Local: 存储本地任务
    Local->>Server: 同步任务到服务器
    Server->>Server: 存储任务备份
    Server-->>Local: 确认同步成功
    Local-->>Client: 返回创建成功
    
    Client->>Local: 请求AI学习计划
    Local->>Local: 生成学习计划
    Local-->>Client: 返回学习计划
```

### 5. AI助手流程

```mermaid
sequenceDiagram
    participant Client as 前端
    participant Local as Local Backend
    
    Client->>Local: 发送聊天消息
    Local->>Local: 处理Agent逻辑
    Local->>Local: 生成响应
    Local->>Local: 存储聊天历史
    Local-->>Client: 返回Agent响应
```

## 部署流程

### 1. 本地开发环境部署

#### Local Backend

```bash
# 进入目录
cd local_backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env

# 初始化数据库
python init_db.py

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Server Backend

```bash
# 进入目录
cd server_backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env

# 初始化数据库
python init_db.py

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 2. 生产环境部署

#### Local Backend
- 使用PyInstaller打包为可执行文件
- 配置为系统服务自动启动
- 定期备份本地数据库文件

#### Server Backend
- 部署在云服务器上
- 使用PostgreSQL数据库
- 配置Gunicorn + Nginx
- 启用HTTPS
- 配置监控和日志管理

## 系统集成

### 前端集成

前端应用可以通过以下方式集成：

1. **Local Backend API**：http://localhost:8000
2. **Server Backend API**：http://localhost:8001 (开发环境)

### API文档

- **Local Backend**：http://localhost:8000/docs
- **Server Backend**：http://localhost:8001/docs

### 环境变量配置

| 配置项 | Local Backend | Server Backend | 说明 |
|--------|---------------|----------------|------|
| APP_NAME | ✅ | ✅ | 应用名称 |
| APP_VERSION | ✅ | ✅ | 应用版本 |
| DEBUG | ✅ | ✅ | 调试模式 |
| DATABASE_URL | ✅ | ✅ | 数据库连接字符串 |
| SECRET_KEY | ✅ | ✅ | JWT密钥 |
| ALGORITHM | ✅ | ✅ | JWT算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | ✅ | ✅ | 令牌过期时间 |
| CORS_ORIGINS | ✅ | ✅ | CORS允许的源 |
| SERVER_BACKEND_URL | ✅ | ❌ | 服务器后端地址 |

## 系统监控

### 健康检查

- **Local Backend**：http://localhost:8000/health
- **Server Backend**：http://localhost:8001/health

### 日志管理

- **Local Backend**：本地日志文件
- **Server Backend**：服务器日志系统

## 安全考虑

1. **数据安全**：
   - 密码在服务器端验证和存储
   - 本地存储加密后的密码
   - 传输使用HTTPS

2. **认证安全**：
   - JWT令牌认证
   - 令牌过期机制
   - 防暴力攻击措施

3. **数据保护**：
   - 本地数据文件权限控制
   - 服务器数据备份
   - 数据传输加密

## 性能优化

1. **Local Backend**：
   - 本地缓存
   - 延迟加载
   - 批处理操作

2. **Server Backend**：
   - 数据库索引优化
   - 缓存机制
   - 异步处理

## 扩展规划

1. **功能扩展**：
   - 多语言支持
   - 第三方服务集成
   - 高级AI功能

2. **架构扩展**：
   - 微服务架构
   - 容器化部署
   - 负载均衡

3. **技术升级**：
   - 数据库迁移到PostgreSQL
   - 引入缓存系统
   - 实现消息队列

## 开发指南

### 代码结构

```
team-project-26spring-26s-27/
├── local_backend/         # 本地后端
│   ├── database/         # 数据库层
│   ├── business/         # 业务层
│   ├── service/          # 服务层
│   ├── presentation/     # 表现层
│   ├── config.py         # 配置文件
│   ├── main.py           # 应用入口
│   ├── init_db.py        # 数据库初始化
│   ├── requirements.txt  # 依赖包
│   └── README.md         # 本地后端文档
├── server_backend/        # 服务器后端
│   ├── database/         # 数据库层
│   ├── business/         # 业务层
│   ├── service/          # 服务层
│   ├── presentation/     # 表现层
│   ├── config.py         # 配置文件
│   ├── main.py           # 应用入口
│   ├── init_db.py        # 数据库初始化
│   ├── requirements.txt  # 依赖包
│   └── README.md         # 服务器后端文档
└── README.md            # 整体流程文档
```

### 开发流程

1. **环境搭建**：
   - 安装Python 3.13
   - 安装依赖包
   - 配置环境变量

2. **代码开发**：
   - 遵循四层架构
   - 编写单元测试
   - 代码风格一致

3. **测试**：
   - 运行API测试
   - 验证功能完整性
   - 检查性能和安全

4. **部署**：
   - 本地测试
   - 服务器部署
   - 监控和维护

## 故障排除

### 常见问题

1. **依赖兼容性**：
   - Python 3.13需要特定版本的依赖
   - 已固定pydantic==1.10.12和sqlalchemy==1.4.50

2. **同步失败**：
   - 检查网络连接
   - 验证服务器地址配置
   - 查看同步日志

3. **认证问题**：
   - 检查JWT密钥配置
   - 验证用户凭证
   - 查看认证日志

4. **数据库问题**：
   - 检查数据库连接字符串
   - 验证数据库权限
   - 查看数据库日志

## 贡献指南

1. **代码贡献**：
   - 遵循代码风格
   - 编写测试用例
   - 提交Pull Request

2. **文档贡献**：
   - 更新README文件
   - 编写API文档
   - 完善开发指南

3. **问题反馈**：
   - 提交Issue
   - 提供详细的错误信息
   - 建议改进方案

## 许可证

MIT License
