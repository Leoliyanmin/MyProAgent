# Blackboard / TIS / Mail 绑定接口说明

> 基础路径：`http://localhost:8002`（Local Backend）
>
> 所有接口均需携带 JWT Token：`Authorization: Bearer <jwt-token>`

---

## 一、Blackboard 接口

### GET /api/v1/blackboard/status
**描述**：获取 Blackboard 绑定状态

**成功响应**：
```json
{
    "success": true,
    "is_bound": true,
    "username": "用户ID或用户名",
    "bind_time": "2026-04-30 10:00:00",
    "last_sync_time": "2026-04-30 12:00:00"
}
```

---

### POST /api/v1/blackboard/bind?cookies=<str>
**描述**：使用 Cookie 绑定 Blackboard 账号，绑定成功后自动爬取课程/作业/公告并入库。

**参数**：`cookies` — Blackboard Cookie 的 JSON 字符串（需 URL 编码）

**必需 Cookie 字段**：
| 字段 | 说明 |
|---|---|
| `JSESSIONID` | Blackboard 会话 ID |
| `s_session_id` | Blackboard 安全会话 ID |

**绑定流程**：
1. 前端通过 Tauri 获取 `https://bb.sustech.edu.cn` 的 Cookie
2. 构造 JSON 字符串 `{"JSESSIONID":"...","s_session_id":"..."}` → URL 编码 → 传给后端
3. 后端验证 Cookie 有效性 → 爬取课程数据 → 写入数据库

**成功响应**：
```json
{
    "success": true,
    "message": "Blackboard账号绑定成功"
}
```

---

### POST /api/v1/blackboard/sync
**描述**：重新爬取并同步 Blackboard 数据（课程、作业含 due_date、公告、课程资料）

**成功响应**：
```json
{
    "success": true,
    "message": "同步成功",
    "data": { ... }
}
```

---

### POST /api/v1/blackboard/unbind
**描述**：解绑 Blackboard 账号（仅删除 account 记录，保留已入库数据）

**成功响应**：
```json
{
    "success": true,
    "message": "Blackboard账号解绑成功"
}
```

---

### GET /api/v1/blackboard/courses
**描述**：获取已同步的课程列表

**成功响应**：
```json
{
    "success": true,
    "courses": [
        {
            "category_id": 1,
            "category_kind": "course",
            "category_title": "Computer Vision Spring 2026",
            "category_link": "https://bb.sustech.edu.cn/...",
            "category_source": "blackboard",
            ...
        }
    ]
}
```

---

### GET /api/v1/blackboard/assignments
**描述**：获取已同步的作业列表（含 `data_ddl_time` 字段 = due_date）

**成功响应**：
```json
{
    "success": true,
    "assignments": [
        {
            "data_id": 1,
            "data_title": "Assignment3",
            "data_ddl_time": "May 13, 2026 2:00 PM",
            "data_link_url": "https://bb.sustech.edu.cn/webapps/assignment/...",
            "data_content_type": "assignment",
            ...
        }
    ]
}
```

---

### GET /api/v1/blackboard/announcements
**描述**：获取已同步的公告列表

---

### GET /api/v1/blackboard/materials
**描述**：获取已同步的课程资料列表

---

## 二、TIS 教务系统接口

### GET /api/v1/tis/status
**描述**：获取 TIS 绑定状态

**成功响应**：
```json
{
    "success": true,
    "is_bound": true,
    "student_id": "1221xxxx",
    "bind_time": "2026-04-30 10:00:00",
    "last_sync_time": "2026-04-30 10:05:00"
}
```

---

### POST /api/v1/tis/bind
**描述**：使用 Cookie 绑定 TIS 账号。**绑定成功后自动爬取课表并入库**，无需再调用 sync。

**请求体**：
```json
{
    "cookies": "{\"JSESSIONID\":\"...\",\"route\":\"...\",\"TGC\":\"...\"}"
}
```

**必需 Cookie 字段**：
| 字段 | 说明 |
|---|---|
| `JSESSIONID` | TIS 会话 ID |
| `route` | 路由标识 |
| `TGC` | CAS 认证票据 Cookie |

**绑定流程**：
1. 前端通过 Tauri 获取 `https://tis.sustech.edu.cn` 的 Cookie
2. 构造 JSON 请求体
3. 后端验证 Cookie → 获取用户信息 → 爬取课表 → 入库

**成功响应**：
```json
{
    "success": true,
    "message": "TIS账号绑定成功"
}
```

---

### POST /api/v1/tis/sync
**描述**：手动重新同步 TIS 课表数据

**成功响应**：
```json
{
    "success": true,
    "message": "同步完成，第9周共 6 门课程",
    "schedule": { "星期一": [...], ... },
    "term": "2024-2025-2",
    "week": "9",
    "total_courses": 6
}
```

---

### POST /api/v1/tis/unbind
**描述**：解绑 TIS 账号

---

### GET /api/v1/tis/schedule
**描述**：获取已同步的 TIS 课表数据（从数据库读取）

**成功响应**：
```json
{
    "success": true,
    "courses": [
        {
            "category_id": 2,
            "category_kind": "course",
            "category_title": "Computer Vision",
            "category_source": "tis",
            "category_content": "{\"day\":1,\"title\":\"Computer Vision\",\"teacher\":\"...\",\"weeks\":\"1-16周\",\"location\":\"...\",\"start\":\"08:00\",\"end\":\"09:50\"}",
            ...
        }
    ],
    "terms": [
        {
            "category_kind": "term",
            "category_title": "TIS课表 - 2024-2025-2",
            ...
        }
    ]
}
```

---

## 三、邮箱（Mail）接口

### GET /api/v1/email/status
**描述**：获取邮箱绑定状态

**成功响应**：
```json
{
    "success": true,
    "is_bound": true,
    "email_address": "1221xxxx@mail.sustech.edu.cn",
    "bind_time": "2026-04-30 10:00:00",
    "last_sync_time": "2026-04-30 11:00:00"
}
```

---

### POST /api/v1/email/bind
**描述**：使用客户端专用密码绑定南科大邮箱。

**请求体**：
```json
{
    "email_address": "1221xxxx@mail.sustech.edu.cn",
    "app_password": "客户端专用密码"
}
```

> ⚠️ `app_password` 是**客户端专用密码**，不是邮箱登录密码。
> 获取方式：登录 [mail.sustech.edu.cn](https://mail.sustech.edu.cn) → 设置 → 客户端专用密码 → 生成。

**成功响应**：
```json
{
    "success": true,
    "message": "邮箱账号绑定成功",
    "email_address": "1221xxxx@mail.sustech.edu.cn"
}
```

---

### POST /api/v1/email/sync?max_messages=50
**描述**：爬取并同步邮件数据（写入数据库 + 输出 mail_result.txt）

**查询参数**：
| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `max_messages` | int | 50 | 最大同步邮件数，范围 1-200 |

**成功响应**：
```json
{
    "success": true,
    "message": "成功同步 50 封邮件",
    "data": { "total": 152, "synced": 50 }
}
```

---

### POST /api/v1/email/unbind
**描述**：解绑邮箱账号

---

### GET /api/v1/email/messages
**描述**：获取已同步的邮件列表（从数据库读取）

**成功响应**：
```json
{
    "success": true,
    "messages": [
        {
            "data_id": 10,
            "data_title": "关于课程安排的通知",
            "data_content_type": "mail",
            "data_content_text": "各位同学好...",
            "data_release_time": "2026-04-29 10:15:00",
            "data_meta_json": "{\"sender\":\"老师 <teacher@sustech.edu.cn>\"}",
            ...
        }
    ]
}
```

---

## 四、数据库存储说明

| 数据源 | 表 | 说明 |
|---|---|---|
| **BB** | `account` | `account_platform_type='blackboard'`，`content` 存加密 Cookie |
| **BB** | `category` | `category_kind='course'`，`category_source='blackboard'` |
| **BB** | `data` | `data_content_type='assignment'/'announcement'/'material'`，`data_ddl_time` 存作业截止日期 |
| **TIS** | `account` | `account_platform_type='tis'` |
| **TIS** | `category` | `category_kind='term'`（学期）和 `category_kind='course'`（课程） |
| **Mail** | `account` | `account_platform_type='email'` |
| **Mail** | `category` | `category_kind='mail'`，自动创建 |
| **Mail** | `data` | `data_content_type='mail'`，`data_classification_code=4`，`data_release_time` 存收件时间 |

---

## 五、通用响应格式

**成功响应**：
```json
{ "success": true, "message": "操作成功" }
```

**失败响应**（HTTP 400）：
```json
{ "detail": "错误描述信息" }
```

**认证失败响应**（HTTP 401）：
```json
{ "detail": "Could not validate credentials" }
```
