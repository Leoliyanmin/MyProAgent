# ProAgent 数据库重设计方案

## 背景

当前数据库 `local_backend/database/db/local.db` 现状：

1. **EAV 模式过泛**：任务、邮件、BB 数据全部塞进 `category` + `data` 表，靠字符串类型区分，查询复杂、字段语义不清
2. **关键数据未入库**：TIS 课表 → JSON 文件；BB 课程 → JSON 文件；聊天记录 → 文件系统
3. **缺失关键表**：用户设置无表、email 专用字段缺失（sender/receiver 塞 JSON）
4. **部分表未启用**：schedule(0)、session(0)、chat(0)、sync_state(0)

**当前实际数据**：users(3)、account(1)、category(1)、data(56，全是 mail)，其余表 0 行。

---

## 设计约束

本方案受以下三份规范约束，不可违反：

| 规范文件 | 关键约束 |
|---|---|
| `database_invoke_rules.md §3.4` | **不允许修改 command 层**，只能新增函数 |
| `database_invoke_rules §5-6` | 架构：command → operations → handle；operations 必须类封装 |
| `database_synchronize_rules.md §4` | 同步协议硬依赖 `category`/`data` 表结构，**不可删除** |

---

## 设计思路

**两条腿走路：保留旧表 + 新增专用表，operations 层双写。**

```
                    ┌──────────────────┐
  routes            │   API 契约不变    │
                    ├──────────────────┤
  service/handle    │   对外接口不变     │
                    ├──────────────────┤
  operations        │  双写（新）       │ ← 唯一改动层
                    ├────────┬─────────┤
  command           │ 旧函数  │ 新函数   │ ← 只加不改
                    │(不动)  │(新增)   │
                    ├────────┴─────────┤
  DB                │ category,data,  │ task,email_account,
                    │ schedule,session│ email_message,
                    │ chat,account,   │ tis_course,bb_course,
                    │ sync_state,     │ bb_assignment,... 
                    │ users (保留)    │ (新增)
                    └─────────────────┘
```

### 为什么保留 category/data

1. **同步协议依赖**：`database_synchronize_rules.md §4` 定义的同步包结构包含 `category`/`data` 数组字段
2. **command 层不可改**：`database_invoke_rules.md §3.4`
3. **测试兼容**：`DATABASE_TESTING.md` 中测试覆盖了这些表

### 双写策略

每个模块的 operations 在写入时同时写两处：
- **新表**：业务查询用（语义清晰、查询高效）
- **category/data**：同步用（sync 协议走这条通道）

举例（Task 创建）：
```python
class TaskOperations:
    def create_task(self, user_id, title, ...):
        # 1. 写入新表
        task_id = create_task(user_id, title, ...)           # 新 command
        
        # 2. 双写到旧表（同步用）
        cat_id = ensure_category(user_id, kind='task')       # 旧 command
        create_data(user_id, cat_id, type='task', ...)       # 旧 command
        
        return task_id
```

---

## 表结构

### 保留不变的旧表

以下表结构完全不动：

```sql
-- account      (第三方平台绑定)
-- sync_state   (同步状态)
-- match_profile (匹配画像，开发中)
-- match_result  (匹配结果，开发中)
-- perm         (权限，暂不动)
```

### 保留但微调的旧表

#### users — 仅加一个字段

```sql
-- 原有字段不变，新增 password_hash
ALTER TABLE users ADD COLUMN password_hash TEXT;
```

#### schedule — 加两个字段

```sql
-- 原有字段不变，新增 source 和 source_id
ALTER TABLE schedule ADD COLUMN source TEXT DEFAULT 'manual';
ALTER TABLE schedule ADD COLUMN source_id TEXT;
```

| 字段 | 用途 |
|---|---|
| `source` | `manual` / `tis_course` / `bb_assignment` |
| `source_id` | 关联外部来源的主键 |

#### session / chat — 字段补齐（仅 server 端）

server 端 session 表缺少 `session_title`、`session_created_at`：
```sql
ALTER TABLE session ADD COLUMN session_title TEXT NOT NULL DEFAULT '';
ALTER TABLE session ADD COLUMN session_created_at TEXT;
```

---

### 新增专用表

#### 1. user_setting — 用户设置

对应前端 `UserSettingsView.vue`。

```sql
CREATE TABLE IF NOT EXISTS user_setting (
    user_id              TEXT PRIMARY KEY REFERENCES users(user_id),
    avatar_url           TEXT,
    bio                  TEXT,
    current_focus        TEXT,
    work_preference      TEXT,
    skills               TEXT,                    -- JSON: ["Python","Vue","React"]
    theme_config         TEXT,                    -- JSON: 主题色/背景色配置
    notification_enabled INTEGER NOT NULL DEFAULT 1,
    privacy_share_data   INTEGER NOT NULL DEFAULT 0,
    updated_at           TEXT NOT NULL
);
```

#### 2. task — 任务表

```sql
CREATE TABLE IF NOT EXISTS task (
    task_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            TEXT NOT NULL REFERENCES users(user_id),
    title              TEXT NOT NULL,
    description        TEXT,
    priority           INTEGER NOT NULL DEFAULT 2,  -- 0=低 1=中 2=高 3=紧急
    status             TEXT NOT NULL DEFAULT 'pending',  -- pending|in_progress|completed
    due_date           TEXT,
    linked_schedule_id INTEGER,
    source             TEXT DEFAULT 'manual',         -- manual|blackboard|ai
    created_at         TEXT NOT NULL,
    updated_at         TEXT
);
```

**双写映射**：`category`(kind='task') + `data`(type='task', ddl_time=due_date)

#### 3. tis_course — TIS 课程

```sql
CREATE TABLE IF NOT EXISTS tis_course (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    course_name    TEXT NOT NULL,
    teacher        TEXT,
    location       TEXT,
    weeks          TEXT,                           -- "1-16周"
    term           TEXT,                           -- "2025-2026-2"
    raw_data       TEXT,                           -- JSON：原始爬取数据备份
    created_at     TEXT NOT NULL,
    UNIQUE(user_id, course_name, term)
);
```

**双写映射**：`category`(kind='tis_course', title=course_name, source='tis')

#### 4. tis_schedule_event — TIS 课表事件

```sql
CREATE TABLE IF NOT EXISTS tis_schedule_event (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id      INTEGER NOT NULL REFERENCES tis_course(course_id),
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    day_of_week    INTEGER NOT NULL,               -- 0=周一 ~ 6=周日
    week_num       INTEGER NOT NULL,
    period_start   INTEGER NOT NULL,
    period_end     INTEGER NOT NULL,
    start_time     TEXT,                           -- "08:00"
    end_time       TEXT,                           -- "09:50"
    UNIQUE(course_id, day_of_week, week_num, period_start)
);
```

**双写映射**：`data`(type='tis_event', category_id=对应tis_course的category) + 同步写 `schedule`(source='tis_course')

#### 5. bb_course — Blackboard 课程

```sql
CREATE TABLE IF NOT EXISTS bb_course (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    bb_course_id   TEXT,
    course_name    TEXT NOT NULL,
    course_link    TEXT,
    raw_data       TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT,
    UNIQUE(user_id, bb_course_id)
);
```

**双写映射**：`category`(kind='bb_course', title=course_name, source='blackboard', external_id=bb_course_id)

#### 6. bb_assignment — Blackboard 作业

```sql
CREATE TABLE IF NOT EXISTS bb_assignment (
    assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id      INTEGER NOT NULL REFERENCES bb_course(course_id),
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    title          TEXT NOT NULL,
    description    TEXT,
    link           TEXT,
    due_date       TEXT,
    status         TEXT DEFAULT 'pending',         -- pending|submitted|graded
    raw_data       TEXT,
    created_at     TEXT NOT NULL,
    UNIQUE(user_id, course_id, link)
);
```

**双写映射**：`data`(type='assignment', category_id=对应bb_course的category)

#### 7. bb_announcement — Blackboard 公告

```sql
CREATE TABLE IF NOT EXISTS bb_announcement (
    announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL REFERENCES bb_course(course_id),
    user_id         TEXT NOT NULL REFERENCES users(user_id),
    title           TEXT NOT NULL,
    content         TEXT,
    link            TEXT,
    posted_at       TEXT,
    created_at      TEXT NOT NULL,
    UNIQUE(user_id, course_id, link)
);
```

**双写映射**：`data`(type='announcement', category_id=对应bb_course的category)

#### 8. bb_material — Blackboard 课程资料

```sql
CREATE TABLE IF NOT EXISTS bb_material (
    material_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id     INTEGER NOT NULL REFERENCES bb_course(course_id),
    user_id       TEXT NOT NULL REFERENCES users(user_id),
    title         TEXT NOT NULL,
    content       TEXT,
    link          TEXT,
    created_at    TEXT NOT NULL,
    UNIQUE(user_id, course_id, link)
);
```

**双写映射**：`data`(type='material', category_id=对应bb_course的category)

#### 9. email_account — 邮箱账号

```sql
CREATE TABLE IF NOT EXISTS email_account (
    account_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT NOT NULL REFERENCES users(user_id),
    email_address       TEXT NOT NULL,
    encrypted_password  TEXT NOT NULL,
    bind_time           TEXT,
    last_sync_time      TEXT,
    UNIQUE(user_id, email_address)
);
```

#### 10. email_message — 邮件消息

```sql
CREATE TABLE IF NOT EXISTS email_message (
    message_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL REFERENCES users(user_id),
    account_id     INTEGER NOT NULL REFERENCES email_account(account_id),
    mail_uid       TEXT NOT NULL,
    subject        TEXT NOT NULL,
    sender         TEXT NOT NULL,
    recipients     TEXT,                           -- JSON
    body_text      TEXT,
    body_html      TEXT,
    received_at    TEXT,
    is_read        INTEGER DEFAULT 0,
    created_at     TEXT NOT NULL,
    UNIQUE(user_id, account_id, mail_uid)
);
```

**双写映射**：`category`(kind='mail') + `data`(type='mail', external_id=mail_uid)

---

## 新旧对比

| 数据 | 旧存储 | 新存储 |
|---|---|---|
| 用户 | `users` | `users`（+ password_hash） |
| 用户设置 | ❌ 无 | **`user_setting`** |
| 任务 | `category` + `data` | **`task`**（+ 双写旧表） |
| 日程 | `schedule` | `schedule`（+ source/source_id） |
| 聊天 | `session` + `chat`（文件系统） | `session` + `chat`（启用 DB） |
| TIS 课程 | JSON 文件 | **`tis_course` + `tis_schedule_event`**（+ 双写旧表） |
| BB 课程 | JSON 文件 | **`bb_course/assignment/announcement/material`**（+ 双写旧表） |
| 邮箱 | `data`(type=mail) | **`email_account` + `email_message`**（+ 双写旧表） |
| 绑定 | `account` | `account`（不变） |
| 同步 | `sync_state` | `sync_state`（不变） |

---

## 新增文件清单

按 `database_invoke_rules.md` 命名规范：

### command 层（新增函数，不改旧函数）

| 文件 | 新增内容 |
|---|---|
| `local_backend/database/code/command/database_command.py` | `create_task()`, `get_task()`, `update_task()`, `delete_task()` |
| 同上 | `create_tis_course()`, `create_tis_event()`, ... |
| 同上 | `create_bb_course()`, `create_bb_assignment()`, ... |
| 同上 | `create_email_account()`, `create_email_message()`, ... |
| 同上 | `create_user_setting()`, `update_user_setting()`, ... |

### operations 层（新建文件）

| 文件 | 类 |
|---|---|
| `database/code/operations/database_task_v2_operations.py` | `TaskV2Operations` |
| `database/code/operations/database_tis_operations.py` | `TisCourseOperations`, `TisEventOperations` |
| `database/code/operations/database_bb_v2_operations.py` | `BbCourseV2Operations`, `BbAssignmentV2Operations`, ... |
| `database/code/operations/database_email_v2_operations.py` | `EmailAccountV2Operations`, `EmailMessageV2Operations` |
| `database/code/operations/database_user_setting_operations.py` | `UserSettingOperations` |

### handle 层（新建文件）

| 文件 | 类 |
|---|---|
| `database/code/handle/database_task_v2_handle.py` | `TaskV2Handle` |
| `database/code/handle/database_tis_handle.py` | `TisHandle` |
| `database/code/handle/database_bb_v2_handle.py` | `BbV2Handle` |
| `database/code/handle/database_email_v2_handle.py` | `EmailV2Handle` |
| `database/code/handle/database_user_setting_handle.py` | `UserSettingHandle` |

---

## 实现计划

### Phase 1：Schema + 注册链路

| Step | 内容 | 涉及文件 |
|---|---|---|
| 1 | 编写新 schema SQL（仅新增表，不删旧表） | `database/code/init/database_init_v2.sql` |
| 2 | `database_init.py` 改为执行旧 SQL + 新 SQL | `database/code/init/database_init.py` |
| 3 | 补 `sync_state` 初始化（注册时自动创建） | `database/code/handle/database_user_handle.py` |
| 4 | 改 `auth_routes` 注册/登录打通 DB | `presentation/auth_routes.py` |
| 5 | Seed 脚本 | `scripts/seed_v2.py` |

### Phase 2：功能模块入库（每模块独立，可并行）

| Step | 内容 | 涉及文件 |
|---|---|---|
| 6 | Task 模块：新建 operations + handle → `task` 表（双写） | `database/code/operations/database_task_v2_operations.py`, `database_task_v2_handle.py`, 改 `service/task_service.py` |
| 7 | Schedule 模块：加 source/source_id 字段 | `presentation/schedule_routes.py`, `service/schedule_service.py` |
| 8 | Chat 模块：补 `agent_service.py` 写入 `session`/`chat` | `service/agent_service.py` |
| 9 | Email 模块：新建 operations → `email_account`/`email_message`（双写） | `database_email_v2_operations.py`, 改 `service/email_service.py` |
| 10 | TIS 模块：新建 operations → `tis_course`/`event`（双写） | `database_tis_operations.py`, 改 `service/tis_service.py` |
| 11 | BB 模块：改 `blackboard_service.py` 走 DB（双写） | 改 `service/blackboard_service.py`, `presentation/blackboard_routes.py` |

### Phase 3：补齐 & 验证

| Step | 内容 |
|---|---|
| 12 | `user_setting` 接入前端 UserSettingsView |
| 13 | JSON 历史数据迁移脚本（TIS/BB JSON → 新表） |
| 14 | 更新测试文件 `DATABASE_TESTING.md` |
| 15 | 更新同步协议文档（sync 包中新增 tis/bb/email 字段） |
