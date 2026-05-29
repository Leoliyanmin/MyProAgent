# Agent 工具补全计划

## 背景

`localagent/agent.py` 当前注册了 22 个工具，但覆盖不均——日程模块是全通的（前端→后端→Agent），任务及其他模块只有后端 API，Agent 无法调用。

### 现状矩阵

| 模块 | 后端 API | 前端回写 | Agent 工具 | 状态 |
|------|---------|---------|-----------|------|
| 日程 (Schedule) | ✅ CRUD | ✅ | ✅ 4 个 | **全通（基准）** |
| 任务 (Task) | ✅ CRUD + study-plan | ⚠️ 只读，不写回 | ❌ 零个 | **第一优先** |
| 邮件同步 | ✅ POST /email/sync | ✅ | ❌ | 第二优先 |
| 邮件垃圾箱 | ✅ GET /trash, DELETE, POST restore | ✅ | ❌ | 第二优先 |
| Blackboard | ✅ /status, /sync, /assignments | ✅ | ❌ | 第三优先 |
| TIS | ✅ /status, /schedule | ✅ | ❌ | 第三优先 |
| 课程列表 | ✅ GET /courses | — | ❌ | 第三优先 |

---

## 技术约定

所有新增工具需遵循以下约定（与现有 `calendar_tools`、`email_tools` 一致）：

1. **调用方式**：直接调 service / handle 层，**不走 HTTP**
2. **认证**：通过 `_runtime_context.get("user_id")` 获取当前用户
3. **返回格式**：返回字符串，错误以 `"Error: ..."` 开头
4. **命名**：工具名用 `snake_case` 英文，参数描述用中文
5. **基类**：继承 `localagent/tools/base.py` 的 `BaseTool`

---

## 分步计划

### Commit 1: 添加任务工具（最高优先）

**用户价值**：Agent 当前完全无法操作用户的 TODO List。补全后用户可以自然语言管理任务，如"帮我创建一个周五前完成论文的任务"。

#### 新建 `localagent/tools/task_tools.py`

仿照 `calendar_tools.py` 模式，直接调 `database_task_handle.py` 的 `TaskHandle`：

| Tool 名称 | 描述 | 必填参数 | 可选参数 |
|-----------|------|---------|---------|
| `list_tasks` | 列出当前用户所有任务，可按状态筛选 | — | `status`（"completed"/"pending"） |
| `create_task` | 创建新任务 | `title` | `due_date`, `priority`（p0/p1/p2/p3）, `description` |
| `update_task` | 修改已有任务 | `task_id` | `title`, `due_date`, `priority`, `description`, `status` |
| `delete_task` | 删除任务 | `task_id` | — |
| `get_study_plan` | 获取 AI 生成的学习计划 | — | — |

**搜索 task_id 的方式**（当用户不知道 id 时）：在 `update_task` 和 `delete_task` 中允许通过 `title_keyword` 模糊匹配，与 `calendar_tools.py` 中的 `_resolve_schedule_id` 逻辑一致。

#### 修改文件

| 文件 | 改动 |
|------|------|
| `localagent/tools/__init__.py` | 新增 5 个工具类的导出 |
| `localagent/agent.py` | 在 `_register_tools()` 中注册 5 个新工具 |

#### 验证

- 启动后端，发送"列出我的任务" → agent 调用 `list_tasks`
- 发送"帮我创建一个任务：周五前交论文" → agent 调用 `create_task`
- 发送"把刚才的任务优先级改为 P0" → agent 调用 `update_task`
- 发送"删除论文任务" → agent 调用 `delete_task`
- 发送"给我生成学习计划" → agent 调用 `get_study_plan`

---

### Commit 2: 添加邮件同步/垃圾箱工具

**用户价值**：用户可以触发式同步邮件（不用等 30 秒定时），管理垃圾箱。

#### 修改 `localagent/tools/email_tools.py`

在现有 7 个邮件工具基础上新增 5 个：

| Tool 名称 | 描述 | 必填参数 | 可选参数 |
|-----------|------|---------|---------|
| `sync_emails` | 触发邮件同步 | — | `max_messages` |
| `get_trash_emails` | 查看垃圾箱邮件列表 | — | — |
| `restore_email` | 从垃圾箱恢复邮件 | `message_id` | — |
| `permanent_delete_email` | 永久删除邮件 | `message_id` | — |
| `empty_trash` | 清空垃圾箱 | — | — |

> 注：`delete_email`（移入垃圾箱）和 `get_trash_emails` 在后端 `email_routes.py` 中已存在。新增工具直接调 `EmailService` 对应方法。

#### 修改文件

| 文件 | 改动 |
|------|------|
| `localagent/tools/email_tools.py` | 新增 5 个工具类 |
| `localagent/tools/__init__.py` | 导出新增工具（如需要） |
| `localagent/agent.py` | 注册新增工具 |

---

### Commit 3: 添加 Blackboard / TIS / 课程工具

**用户价值**：用户可以问"我下周有什么作业截止？""今天有什么课？""我有几门课？"

#### 新建 `localagent/tools/blackboard_tools.py`

直接调 `BlackboardService` 和数据库查询：

| Tool 名称 | 描述 | 参数 |
|-----------|------|------|
| `get_blackboard_status` | 查询 Blackboard 绑定状态 | — |
| `sync_blackboard` | 触发 Blackboard 数据同步 | — |
| `get_blackboard_assignments` | 查询作业列表（含截止日期） | — |

#### 新建 `localagent/tools/tis_tools.py`

直接调 `TisService` 和数据库查询：

| Tool 名称 | 描述 | 参数 |
|-----------|------|------|
| `get_tis_status` | 查询 TIS 绑定状态 | — |
| `get_tis_schedule` | 查询课表 | `current_week`（可选） |

#### 新建 `localagent/tools/course_tools.py`

直接调数据库查询：

| Tool 名称 | 描述 | 参数 |
|-----------|------|------|
| `list_courses` | 列出已同步的课程列表 | — |

#### 修改文件

| 文件 | 改动 |
|------|------|
| `localagent/tools/blackboard_tools.py` | 新建 |
| `localagent/tools/tis_tools.py` | 新建 |
| `localagent/tools/course_tools.py` | 新建 |
| `localagent/tools/__init__.py` | 新增 6 个工具类的导出 |
| `localagent/agent.py` | 在 `_register_tools()` 中注册 6 个新工具 |

---

## 改动汇总

| Commit | 新建文件 | 修改文件 | 新增工具数 |
|--------|---------|---------|-----------|
| Commit 1 | 1 (`task_tools.py`) | 2 (`__init__.py`, `agent.py`) | 5 |
| Commit 2 | 0 | 1 (`email_tools.py`) | 5 |
| Commit 3 | 3 | 2 (`__init__.py`, `agent.py`) | 6 |
| **合计** | **4** | **5** | **16** |

### 改后 Agent 工具全景

```
文件工具 (10) + 日程工具 (4) + 邮件工具 (7→12) + 用户画像 (1) + 任务 (5) + Blackboard (3) + TIS (2) + 课程 (1)
= 总计 38 个工具
```

---

## 不在此计划内的项

- **前端任务回写**：`dashboard.js` 的 `addTodo()` / `toggleTodo()` 未调用 `POST/PUT /tasks/`，数据只存 localStorage。这是前端问题，应单独开 PR。
- **Agent 调用方式**：保持直接调 service 层，不改为 HTTP 调用（性能更好，无网络开销）。
- **任务系统架构重构**：不加新表、不改 schema，只补 Agent 入口。
