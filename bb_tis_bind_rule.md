# Blackboard 和 TIS 绑定接口说明

## Blackboard 接口

### GET /api/v1/blackboard/status
**描述**：获取Blackboard绑定状态

**请求头**：
- Authorization: Bearer <jwt-token>

---

### POST /api/v1/blackboard/bind?cookies=<str>
**描述**：使用Cookie绑定Blackboard账号

**参数**：
- cookies: Blackboard的Cookie字符串（JSON格式）

**必需Cookie**：
- JSESSIONID
- s_session_id

**请求头**：
- Authorization: Bearer <jwt-token>

---

### POST /api/v1/blackboard/sync
**描述**：同步Blackboard数据

**请求头**：
- Authorization: Bearer <jwt-token>

---

### POST /api/v1/blackboard/unbind
**描述**：解绑Blackboard账号

**请求头**：
- Authorization: Bearer <jwt-token>

---

## TIS 接口

### GET /api/v1/tis/status
**描述**：获取TIS绑定状态

**请求头**：
- Authorization: Bearer <jwt-token>

---

### POST /api/v1/tis/bind
**描述**：使用Cookie绑定TIS账号

**请求体**：
```json
{
    "cookies": "<cookie-string>"
}
```

**必需Cookie**：
- JSESSIONID
- route
- TGC

**请求头**：
- Authorization: Bearer <jwt-token>
- Content-Type: application/json

---

### POST /api/v1/tis/sync
**描述**：同步TIS课表数据

**请求头**：
- Authorization: Bearer <jwt-token>

---

### POST /api/v1/tis/unbind
**描述**：解绑TIS账号

**请求头**：
- Authorization: Bearer <jwt-token>

---

## 响应格式

成功响应：
```json
{
    "success": true,
    "message": "操作成功",
}
```

失败响应：
```json
{
    "success": false,
    "message": "错误信息"
}
```