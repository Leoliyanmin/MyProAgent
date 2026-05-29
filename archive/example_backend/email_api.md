# 邮件服务 API

所有接口统一前缀为 `/emails`，无需 JWT；只要满足参数要求即可调用。邮件数据与核心用户表解耦，但 `user_id` 依旧是唯一标识：它同时作为 `email_accounts` 的主键，也是所有邮件记录的外键。



使用流程描述：

首先，所有需要身份验证的时候（比如发送邮件，同步邮件），都必须确保数据库里能找到正确的user_id对应的帐号和密码，这个帐号密码在login的时候存入数据库里（如果用户选择不remember me 可以后续在前端用户登出邮箱的时候调用logout方法，删除该user_id以及存储的邮件（删不删邮件，后续可以调整））。

其次，测试的时候，调用 login方法，password和encrypted_password只需要填写**一个**，另一个不填写直接在请求体里把该字段删除就行，password就填写自己的原始密码，加密密码可以用我上传的code_encrypted_test进行测试，（加密需要保证脚本能读到后端**自动生成的RSA密钥**，测试的时候，可以手动将backend/app/core/keys里的）





## 目录
- [邮件服务 API](#邮件服务-api)
  - [目录](#目录)
  - [查询邮件](#查询邮件)
  - [查看邮件详情](#查看邮件详情)
  - [邮箱登录校验](#邮箱登录校验)
  - [获取邮箱加密公钥](#获取邮箱加密公钥)
  - [邮箱登出](#邮箱登出)
  - [发送邮件](#发送邮件)
  - [手动同步邮箱](#手动同步邮箱)
  - [自动同步邮箱](#自动同步邮箱)
  - [附件上传](#附件上传)

---

## 查询邮件
`GET /emails`

按用户分页查询已入库邮件，支持关键字搜索与「解析视图 / 原始视图」切换。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_id` | query | int | **必填**，内部用户主键，仅用于筛选邮件数据 |
| `skip` | query | int | 起始偏移，默认 0 |
| `limit` | query | int | 返回条数，默认 20，范围 1–100 |
| `search` | query | str? | 关键字，模糊匹配 `subject/sender/body/summary` |
| `view` | query | `parsed \| raw` | `raw` 时 snippet 取 MIME 原文 |

**响应：** `EmailListResponse`

```json
{
  "total": 2,
  "items": [
    {
      "id": 10,
      "raw_id": 6,
      "subject": "Welcome",
      "sender": "support@example.com",
      "received_time": "2025-11-27T14:00:00",
      "snippet": "Thank you for joining...",
      "summary": "欢迎邮件摘要",
      "has_attachments": false
    }
  ]
}
```

## 查看邮件详情
`GET /emails/{email_id}`

返回单封邮件的解析内容或原始 MIME。`view=raw` 时只提供 `mime_content` 与基础元信息。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `email_id` | path | int | **必填**，邮件主键 |
| `user_id` | query | int | **必填**，邮件归属者 |
| `view` | query | `parsed \| raw` | `raw` 模式下正文/摘要置空 |

**响应：** `EmailDetail`

## 邮箱登录校验
`POST /emails/login`

用于 IMAP 账号连通性测试；连接成功时会把账号配置写入 `email_accounts` 表，并立即从 `INBOX` 拉取邮件服务器上的前 5 封邮件（若不足 5 封则全量同步），供前端立刻查看最新内容。

**请求体：** `EmailLoginRequest`

```json
{
  "user_id": 1,
  "host": "imap.example.com",
  "port": 993,
  "email": "user@example.com",
  "password"："xxxx",
  "encrypted_password": "<RSA_BASE64>",
  "use_ssl": true
}
```

- `encrypted_password`: 使用 `/emails/public-key` 返回的 RSA 公钥对真实密码加密后再 Base64 编码；
- `password`：仅供本地调试/旧版本兼容，生产环境应移除该字段。

后端会解密后再使用，且在写入数据库前会再用对称密钥二次加密，后续 `/emails/send`、`/emails/auto-sync` 会自动解密复用。

**响应：**
```json
{"success": true, "message": "邮箱连接成功，已同步 3/5 封"}
```

## 获取邮箱加密公钥
`GET /emails/public-key`

返回一段 PEM 字符串，可供前端（例如 `jsencrypt` 或 Web Crypto API）对邮箱密码进行 RSA 加密。

```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...\n-----END PUBLIC KEY-----\n"
}
```

## 邮箱登出
`POST /emails/logout`

删除指定 `user_id` 对应的邮箱账号配置及其所有已存邮件，适用于用户主动解绑邮箱的场景。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_id` | query | int | **必填**，待登出邮箱的用户主键 |

请求体留空即可。

**响应：** `EmailLogoutResponse`

```json
{
  "success": true,
  "deleted_accounts": 1,
  "deleted_raw": 120,
  "deleted_parsed": 120,
  "message": "已删除账号 1 条，原始邮件 120 条，解析邮件 120 条"
}
```

## 发送邮件
`POST /emails/send`

走 SMTP 通道发送邮件，可携带多收件人与 Base64 附件。**必须提前调用 `/emails/login` 完成邮箱绑定**，发送时仅允许通过 query 指定 `user_id`，系统会自动读取 `email_accounts` 中已保存的主机/账号/密码完成鉴权。

为了避免重复输入 SMTP 地址，服务会依据登录时保存的 IMAP host 自动推导常见邮箱的 SMTP 配置，例如：
- `imap.qq.com → smtp.qq.com`（465/SSL）
- `imap.gmail.com → smtp.gmail.com`（465/SSL）
- `imap-mail.outlook.com → smtp-mail.outlook.com`（587/STARTTLS）
- `outlook.office365.com → smtp.office365.com`（587/STARTTLS）

若检测到用户在登录阶段手动填写了非 IMAP 端口（例如 465/587），系统会直接使用该端口，便于企业邮箱自定义。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_id` | query | int | **必填**，发送时使用的邮箱账号主键，必须已登录成功 |

**请求体（EmailSendRequest）核心字段：**

```json
{
  "subject": "主题",
  "to": ["a@example.com"],
  "body_text": "纯文本",
  "body_html": "<p>HTML</p>",
  "attachments": [
    {
      "filename": "report.pdf",
      "content": "<BASE64>",
      "content_type": "application/pdf"
    }
  ]
}
```

若查询参数中的 `user_id` 尚未绑定邮箱，将返回 404 并提示先登录。为保证 SMTP 鉴权一致，后台始终把 `MAIL FROM` 设为已绑定的邮箱地址，调用方无需也无法指定 `sender`。

> 所有邮箱密码在数据库中均以对称密钥加密存储，只有后台自解密后再发起 IMAP/SMTP 连接，外部请求无法读取明文。

**响应：** `EmailSendResponse`

## 手动同步邮箱
`POST /emails/sync`

拉取 IMAP 邮箱并写入 `email_raw` / `email_parsed`，自动跳过重复邮件。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_id` | query | int | **必填**，同步结果写入的用户主键（需与请求体内 `user_id` 一致） |
| `folder` | query | str | IMAP 文件夹，默认 `INBOX` |
| `limit` | query | int | 拉取数量，默认 50（1–500） |

**请求体：** `EmailLoginRequest`（其中 `user_id` 需与 query 参数一致）

**响应：** `EmailSyncResponse`

```json
{
  "fetched": 120,
  "stored": 90,
  "skipped": 30
}
```

## 自动同步邮箱
`POST /emails/auto-sync`

基于 `email_accounts` 中持久化的配置触发同步，无需再次提供邮箱密码。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `user_id` | query | int | **必填**，凭据表与邮件表共享的用户主键 |
| `folder` | query | str | IMAP 文件夹，默认 `INBOX` |
| `limit` | query | int | 拉取数量，默认 50（1–500） |

**响应：** `EmailSyncResponse`

```json
{
  "fetched": 40,
  "stored": 30,
  "skipped": 10
}
```

未找到凭据时返回 404，需先调用 `/emails/login` 成功完成初始化。

## 附件上传
`POST /emails/attachments/upload`

接收单个文件并返回 Base64，以方便 `/emails/send` 复用。

| 参数 | 位置 | 类型 | 说明 |
| --- | --- | --- | --- |
| `file` | form-data | UploadFile | **必填**，大小 ≤ 10MB |

**响应：** `EmailAttachmentUploadResponse`

```json
{
  "filename": "attachment.png",
  "content_type": "image/png",
  "size": 2048,
  "content": "<BASE64>"
}
```

