**同步接口文档版 v1.1**

**1. 目标与范围**

1. 用 user 级字段完成前后端同步决策，不做逐条记录比对。
2. 支持登录后首拉、会话中探测、按需下发、客户端回传。
3. 明确请求参数、响应字段、状态码、错误码。
4. 不包含字段新增或迁移执行步骤。

**2. 通用约定**

1. 协议：HTTPS。
2. 数据格式：application/json，UTF-8。
3. 时间格式：ISO 8601，UTC，例如 2026-03-27T10:11:12.123456+00:00。
4. 鉴权：Authorization: Bearer 访问令牌。
5. 幂等建议：上传接口支持 Idempotency-Key 请求头。
6. 接口前缀：/api/v1。

**3. 同步判定核心字段（users + sync_state）**

3.1 字段落点

|表名|字段名|用途|
|-|-|-|
|users|user\_id|用户唯一标识|
|users|username, user\_email, user\_is\_active, user\_created\_at, user\_last\_login, user\_source\_device\_id|用户基础资料与状态|
|sync\_state|user\_id|与 users.user\_id 一一对应|
|sync\_state|user\_data\_updated\_at|用户业务数据最后变更时间|
|sync\_state|user\_last\_synced\_at|最近一次前后端同步成功时间|
|sync\_state|user\_version|单调递增版本号，时间比较兜底|
|sync\_state|sync\_updated\_at|同步状态行最后更新时间|

3.2 判定字段定义

|字段名|类型|说明|
|-|-|-|
|user\_id|string|用户唯一标识|
|user\_data\_updated\_at|string(date-time)|用户业务数据最后变更时间|
|user\_last\_synced\_at|string(date-time)|最近一次前后端同步成功时间|
|user\_version|integer|单调递增版本号，时间比较兜底|
|user\_source\_device\_id|string|最近变更来源设备，可选|

3.3 说明

1. user\_version、user\_last\_synced\_at、user\_data\_updated\_at 的数据库主存储位置是 sync\_state。
2. 同步包中的 user 对象可携带这些字段，作为传输层字段；落库时写入 sync\_state。

**4. 数据包结构（用于 pull 与 push）**
4.1 顶层结构

|字段|类型|必填|说明|
|-|-|-|-|
|meta|object|是|包元信息|
|user|object|是|user 同步字段|
|account|array<object>|否|账号集合|
|category|array<object>|否|分类集合|
|data|array<object>|否|数据集合|
|schedule|array<object>|否|日程集合|
|session|array<object>|否|会话集合|
|chat|array<object>|否|聊天集合|

4.2 meta

|字段|类型|必填|说明|
|-|-|-|-|
|schema\_version|integer|是|包结构版本|
|source|string|是|local 或 server|
|generated\_at|string(date-time)|是|包生成时间|
|request\_id|string|否|链路追踪 id|

4.3 user（同步相关）

|字段|类型|必填|说明|
|-|-|-|-|
|user\_id|string|是|用户 id|
|username|string|是|用户名|
|user\_email|string|是|邮箱|
|user\_is\_active|integer|是|0 或 1|
|user\_created\_at|string(date-time)|是|创建时间|
|user\_last\_login|string(date-time)|否|上次登录|
|user\_version|integer|是|版本|
|user\_source\_device\_id|string|否|设备标识|
|user\_last\_synced\_at|string(date-time)|否|最近同步时间|
|user\_data\_updated\_at|string(date-time)|是|业务数据最近变更时间|

说明：其中 user\_version、user\_last\_synced\_at、user\_data\_updated\_at 在数据库层写入 sync\_state。

4.4 data（分类相关新增字段）

|字段|类型|必填|说明|
|-|-|-|-|
|data\_classification\_code|integer|是|数据分类编码：1=公共，2=课程资料，3=作业|

**5. 接口 1：同步探测**
5.1 路径与方法  
POST /api/v1/sync/probe

5.2 请求参数

|字段|类型|必填|说明|
|-|-|-|-|
|user\_id|string|是|用户 id|
|client\_user\_data\_updated\_at|string(date-time)|否|客户端数据更新时间|
|client\_user\_last\_synced\_at|string(date-time)|否|客户端上次同步时间|
|client\_user\_version|integer|否|客户端版本|
|client\_device\_id|string|否|当前设备 id|

5.3 响应字段（200）

|字段|类型|必填|说明|
|-|-|-|-|
|action|string|是|noop、pull、push、conflict|
|reason|string|是|判定原因|
|server\_user\_data\_updated\_at|string(date-time)|否|服务端更新时间|
|server\_user\_last\_synced\_at|string(date-time)|否|服务端上次同步时间|
|server\_user\_version|integer|否|服务端版本|
|server\_time|string(date-time)|是|服务端当前时间|
|request\_id|string|否|请求 id|

5.4 业务语义

1. action=noop：双方无新变化。
2. action=pull：客户端需要拉取服务端数据。
3. action=push：客户端需要上传本地数据。
4. action=conflict：双方都有新变化，需冲突裁决。

**6. 接口 2：拉取数据**
6.1 路径与方法  
GET /api/v1/sync/pull?user\_id={user\_id}

6.2 查询参数

|参数|类型|必填|说明|
|-|-|-|-|
|user\_id|string|是|用户 id|
|mode|string|否|full 或 delta，默认 full|

6.3 响应字段（200）

1. 返回第 4 节定义的完整数据包。
2. meta.source 固定为 server。
3. 包内 user 字段包含服务端当前 user\_version、user\_data\_updated\_at、user\_last\_synced\_at（来自 sync\_state）。

6.4 安全规则

1. 不下发敏感字段：密码哈希、盐、自动登录令牌、账号凭据、验证码表数据。
2. 若请求越权，返回 403。

**7. 接口 3：上传数据**
7.1 路径与方法  
POST /api/v1/sync/push

7.2 请求体

1. 结构与第 4 节相同，meta.source 应为 local。
2. 必须包含 user.user\_id。
3. 建议包含 user.user\_version、user\_data\_updated\_at、user\_last\_synced\_at。

7.3 响应字段（200）

|字段|类型|必填|说明|
|-|-|-|-|
|applied|boolean|是|是否已应用|
|result|string|是|applied、discarded\_stale、conflict\_rejected|
|reason|string|是|处理原因|
|server\_user\_version|integer|否|应用后版本|
|server\_user\_data\_updated\_at|string(date-time)|否|应用后更新时间|
|server\_user\_last\_synced\_at|string(date-time)|否|应用后同步时间|
|request\_id|string|否|请求 id|

7.4 服务器处理规则

1. 先做旧包判断。
2. 若旧包：applied=false，result=discarded\_stale，不覆盖数据库。
3. 若可应用：执行导入并更新 sync\_state 同步字段；users 仅更新基础资料字段。
4. 若命中冲突策略拒绝：applied=false，result=conflict\_rejected。

**8. 接口 4：同步确认（可选但推荐）**
8.1 路径与方法  
POST /api/v1/sync/ack

8.2 请求参数

|字段|类型|必填|说明|
|-|-|-|-|
|user\_id|string|是|用户 id|
|ack\_type|string|是|pull\_applied 或 push\_applied|
|client\_applied\_at|string(date-time)|是|客户端应用完成时间|
|client\_user\_version|integer|否|客户端应用后版本|

8.3 响应（200）

|字段|类型|必填|说明|
|-|-|-|-|
|ok|boolean|是|是否成功|
|server\_user\_last\_synced\_at|string(date-time)|是|服务端收敛后的同步时间（来自 sync\_state）|
|request\_id|string|否|请求 id|

**9. 状态码清单**

|状态码|含义|典型场景|
|-|-|-|
|200|成功|probe 成功、pull 成功、push 已处理|
|202|已接收待处理|可选异步导入模式|
|400|参数错误|缺少 user\_id、字段类型不合法|
|401|未认证|token 缺失或失效|
|403|禁止访问|用户与 token 不匹配|
|404|资源不存在|user 不存在|
|409|冲突|服务端裁决要求客户端先 pull|
|412|前置条件失败|版本检查失败或同步前提不满足|
|422|语义错误|JSON 结构合法但业务字段不合法|
|429|频率限制|probe 或 push 过于频繁|
|500|服务器错误|非预期异常|

**10. 业务错误码清单**

|错误码|HTTP|说明|
|-|-|-|
|SYNC\_USER\_ID\_REQUIRED|400|缺少 user\_id|
|SYNC\_PAYLOAD\_INVALID|422|同步包结构不合法|
|SYNC\_USER\_NOT\_FOUND|404|用户不存在|
|SYNC\_UNAUTHORIZED\_USER|403|token 与 user\_id 不匹配|
|SYNC\_STALE\_PAYLOAD|200|上传包过旧，已丢弃|
|SYNC\_CONFLICT\_PULL\_REQUIRED|409|冲突，要求先拉取|
|SYNC\_VERSION\_INVALID|412|版本字段异常或不满足前置条件|
|SYNC\_TIME\_INVALID|422|时间字段格式错误|
|SYNC\_RATE\_LIMITED|429|请求过频|
|SYNC\_INTERNAL\_ERROR|500|服务器内部错误|

**11. 冲突与旧包判定规则**

1. 判定数据来源：默认读取 sync\_state（user\_version、user\_last\_synced\_at、user\_data\_updated\_at）。
2. 旧包判定优先级：先比较 user\_version，较小者旧。
3. 版本相同再比较 user\_last\_synced\_at，较早者旧。
4. 时间不可用时，回退以 version 判定。
5. 双端冲突裁决：先比较 user\_data\_updated\_at，较晚者胜。
6. 若时间相同则 user\_version 较大者胜。
7. 若仍相同则服务端胜，保证确定性。

**12. 客户端建议调用时序**

1. 登录成功后先调用 pull。
2. 会话中每 30 到 120 秒调用 probe。
3. probe 返回 pull 时调用 pull 并本地应用。
4. 本地有变更时防抖调用 push。
5. push 或 pull 成功后调用 ack（若启用）。

**13. 字段安全策略**

1. pull 响应中不返回敏感字段。
2. push 请求中若出现敏感字段，服务端忽略且不覆盖。
3. 服务端只接受白名单字段写入，避免越权更新。

如果你希望，我可以继续给你补一版“可直接给前端用的 OpenAPI 3.0 YAML 草案”，包括示例请求体与示例响应体。

