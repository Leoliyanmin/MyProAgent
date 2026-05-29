# 数据库全量扫描报告（最终版）

> 修订时间: 2026-05-24（第三次扫描后）
> 核验范围: `local_backend/`, `server_backend/`, `frontend/`
> 核验方式: 代码静态扫描 + `sqlite3` 实库检查 + 全量 grep

---

## 一、数据库现状

### `local.db` — 10 张表，全部正常

| 表 | 行数 | 说明 |
|---|---|---|
| event | 248 | 统一日程/任务/课表/作业 |
| users | 2 | |
| sync_state | 2 | |
| account | 1 | |
| session | 39 | |
| chat | 201 | |
| user_setting | 1 | |
| email_account | 1 | |
| email_message | 178 | |
| starred_emails | 2 | |

### `server.db` — 7 张表，已包含 `event`

| 表 | 行数 | 说明 |
|---|---|---|
| event | 0 | 结构已到位，数据待同步 |
| users | 1 | |
| sync_state | 1 | |
| account / chat / session / user_setting | 0 | |

---

## 二、代码迁移完成度

### P0 — 所有写入路径已切到 `event` ✅

| 文件 | 之前 | 现在 |
|---|---|---|
| `database_task_v2_operations.py` | 双写 `task`+`data` | ✅ **单写 `event`** |
| `database_tis_operations.py` | 写 `category`+`data`+`tis_*` | ✅ **写 `event`** |
| `database_schedule_operations.py` | 写 `schedule` | ✅ **写 `event`** |
| `import_tis_json.py` | 写 `tis_course`+`tis_schedule_event` | ✅ **写 `event`** |
| `database_mail_operations.py` | 写 `category`+`data` | ✅ **已清理，只剩 account** |

### P0 — 所有读取路径已切到 `event` ✅

| 文件 | 之前 | 现在 |
|---|---|---|
| `tis_routes.py` | `list_tis_courses_by_user` | ✅ **`list_events_by_user`** |
| `courses_routes.py` | `list_tis_courses_by_user` | ✅ **`list_events_by_user`** |
| `blackboard_routes.py` | `list_categories_by_user`+`list_data_by_user` | ✅ **`list_events_by_user`** |
| `scheduler_service.py` | `TaskOperations.get_tasks_by_user` | ✅ **`list_events_by_user`** |
| `handle/database_tis_handle.py` | 配套 category 操作 | ✅ 已通 |
| `handle/database_schedule_handle.py` | 配套 schedule | ✅ 已通 |

### P1 — 功能缺陷 ✅

| 文件 | 之前 | 现在 |
|---|---|---|
| `scheduler_service.py` | 同步发送旧表数据到 server | ✅ `data_type:"event"` |
| `database_mail_operations.py` | `create_category`+`create_data` | ✅ 删除两个旧类，只剩 account |
| `email_service.py` | ? | ✅ 走 `EmailV2Handle` 正确路径 |

---

## 三、仍然存在的死代码（🔴——无人调用，可直接删除）

| 文件 | 遗留原因 |
|---|---|
| `database/code/database_blackboard_operations.py` | 旧版 monolithic BlackboardOperations（写 category+data） |
| `database/code/database_blackboard_handle.py` | 配套旧 handle |
| `operations/database_blackboard_operations.py` | 模块化旧版 BlackboardOperations（写 category+data） |
| `handle/database_blackboard_handle.py` | 配套旧 handle（blackboard_service 已走 BbV2Handle→event） |
| `operations/database_task_operations.py` | TaskOperations 写 data 表（已被 v2 替代） |
| `operations/database_email_operations.py` | EmailMessageOperations 写 data 表（已被 v2 替代） |
| `handle/database_email_handle.py` | 配套旧 handle（email_service 已走 EmailV2Handle） |
| `operations/database_match_operations.py` | 匹配功能无人使用 |
| `handle/database_match_handle.py` | 同上 |
| `database_init_v2.sql` | 其中 task/bb/tis/match 等表已不在 DB，但仍有 user_setting/email_* |

---

## 四、剩余真实问题

### ⚠️ P0 — 新环境初始化会炸

**`database_init.py` 不会创建 `event` 表。** 重新初始化的新数据库将缺少 event 表，所有写入路径会报错。

你的主库是通过手动迁移达到当前状态的，但 init 脚本没有跟着改。

### 🟡 P2 — 前端 `calendar.js`

`createScheduleOnBackend` 和 `updateScheduleOnBackend` 仍走 `schedulesAPI`，后端 `/schedules` 路由还在但底层已切到 `event`。建议前端也改成 `eventsAPI`。

---

## 五、建议的下一步

### 1. 修 init 脚本（关键）

在 `database_init.sql` 里加上 `CREATE TABLE IF NOT EXISTS event (...)`，确保全新建库能直接跑。

或者在 `database_init.py` 里加 migration 逻辑：检测 `event` 表不存在时自动创建。

### 2. 删死代码

确认无人使用后，一次性删掉上面清单里的 10 个文件。

### 3. 更新文档

`database_synchronize_rules.md`、`db_design.md` 与当前 event 模型对齐。
