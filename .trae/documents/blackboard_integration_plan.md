# Blackboard 账号绑定与数据同步功能实现计划

## 1. 仓库结构分析

通过对当前代码库的分析，发现：

- **项目结构**：
  - `local_backend/`：本地后端服务，使用FastAPI框架
  - `server_backend/`：服务器后端服务
  - 两者均使用SQLite数据库

- **现有认证系统**：
  - 使用JWT进行身份验证
  - 完整的登录/注册流程
  - 依赖注入获取当前用户ID

- **数据库结构**：
  - `users`表：存储用户基本信息
  - `account`表：存储账号绑定信息，包含`content`字段可用于存储会话信息
  - `category`表：存储分类信息，可用于存储课程大类
  - `data`表：存储具体数据，可用于存储作业、project等条目
  - 其他相关表结构

- **现有API路由**：
  - `/auth/*`：认证相关
  - `/schedule/*`：日程相关
  - `/task/*`：任务相关
  - `/agent/*`：代理相关
  - `/sync/*`：同步相关

## 2. 实现计划

### 2.1 数据库使用

1. **使用现有表结构**：
   - `account`表：存储Blackboard账号绑定信息（`account_platform_type`为"blackboard"），会话信息存储在`content`字段
   - `category`表：存储课程大类（`category_kind`为"course"）
   - `data`表：存储作业、project等条目（关联到对应课程category）

### 2.2 数据库操作层实现

1. **新增`database_blackboard_operations.py`**：
   - 实现Blackboard账号绑定信息的增删改查
   - 实现课程和作业数据的存储操作

2. **新增`database_blackboard_handle.py`**：
   - 封装Blackboard相关的数据库操作流程
   - 提供统一的调用入口

### 2.3 核心服务实现

1. **Blackboard服务**：
   - 实现CAS登录流程
   - 处理认证回调
   - 会话加密与存储（存储到account表的content字段）
   - 数据爬取与同步

2. **加密服务**：
   - AES加密/解密会话信息
   - 安全存储敏感数据

### 2.4 API路由实现

1. **Blackboard路由**：
   - `POST /api/v1/blackboard/bind`：发起绑定请求
   - `GET /api/v1/blackboard/callback`：处理CAS回调
   - `POST /api/v1/blackboard/sync`：手动触发同步
   - `GET /api/v1/blackboard/status`：获取绑定状态

### 2.5 数据同步实现

1. **课程数据同步**：
   - 从Blackboard爬取课程信息
   - 存储到`category`表（`category_kind`为"course"）

2. **作业数据同步**：
   - 从Blackboard爬取作业信息
   - 存储到`data`表，关联到对应课程category

## 3. 技术实现细节

### 3.1 CAS认证流程

1. **发起绑定**：
   - 生成唯一`state`参数
   - 构造CAS登录URL
   - 重定向用户到CAS登录页

2. **回调处理**：
   - 验证`state`参数
   - 用`ticket`访问Blackboard
   - 获取并加密存储会话Cookie到account表的content字段
   - 触发初始数据同步

### 3.2 会话管理

1. **加密存储**：
   - 使用AES-256加密会话Cookie
   - 存储到account表的content字段

2. **会话验证**：
   - 定期检查会话有效性
   - 会话过期时提示用户重新绑定

### 3.3 数据爬取

1. **课程数据**：
   - 爬取课程列表
   - 提取课程基本信息
   - 存储到`category`表

2. **作业数据**：
   - 爬取作业列表
   - 提取作业详情和截止时间
   - 存储到`data`表，关联到对应课程category

### 3.4 数据库操作规范

1. **遵循数据库调用规范**：
   - 创建`database_blackboard_operations.py`实现数据库规则函数
   - 创建`database_blackboard_handle.py`实现流程控制
   - 所有数据库操作通过command层执行
   - 实现user_id粒度锁确保并发安全

2. **数据关联**：
   - 每个data条目必须关联到一个category
   - 使用`data_category_id`字段建立关联

## 4. 依赖与配置

### 4.1 新增依赖

- `python-cas`：CAS认证客户端
- `beautifulsoup4`：HTML解析
- `requests`：HTTP请求
- `pycryptodome`：加密功能

### 4.2 配置项

- CAS服务器URL
- Blackboard系统URL
- 加密密钥
- 会话过期时间

## 5. 风险与处理

### 5.1 潜在风险

1. **CAS认证失败**：
   - 网络问题导致认证流程中断
   - 用户取消认证操作

2. **会话管理**：
   - 会话过期导致数据同步失败
   - 加密密钥泄露

3. **数据爬取**：
   - Blackboard页面结构变化
   - 爬取频率过高被封禁

4. **数据库操作**：
   - 并发操作导致数据不一致
   - 数据关联关系错误

### 5.2 风险处理

1. **错误处理**：
   - 完善的错误捕获和处理机制
   - 友好的错误提示

2. **会话管理**：
   - 定期检查会话有效性
   - 自动重新认证机制

3. **数据爬取**：
   - 合理的爬取间隔
   - 页面结构变化的容错处理

4. **数据库操作**：
   - 严格遵循数据库调用规范
   - 实现user_id粒度锁
   - 确保数据关联关系正确

## 6. 实现步骤

1. **准备工作**：
   - 创建`.trae/documents/`目录（如果不存在）
   - 安装必要的依赖

2. **数据库操作层实现**：
   - 创建`database_blackboard_operations.py`
   - 创建`database_blackboard_handle.py`

3. **核心服务实现**：
   - 创建`BlackboardService`
   - 实现CAS认证流程
   - 实现会话加密与存储（使用account表的content字段）

4. **API路由实现**：
   - 创建`blackboard_routes.py`
   - 实现绑定、回调和同步接口

5. **数据同步实现**：
   - 实现课程数据同步（存储到category表）
   - 实现作业数据同步（存储到data表）

6. **测试与调试**：
   - 测试CAS认证流程
   - 测试数据同步功能
   - 测试错误处理机制

7. **集成与部署**：
   - 集成到现有系统
   - 更新配置文件
   - 部署到生产环境

## 7. 预期结果

- 用户可以通过CAS完成Blackboard账号绑定
- 系统自动同步课程与作业数据到category和data表
- 支持手动触发数据同步
- 提供绑定状态查询接口
- 完善的错误处理和用户提示
- 符合数据库调用规范的实现

## 8. 后续优化

- 实现自动定期同步
- 添加数据变更通知
- 优化爬取性能
- 增加数据备份机制