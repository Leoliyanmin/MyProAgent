# 数据库调用规范 v1.0

## 1\. 目标与范围

1. 规范本项目数据库相关文件的职责分工与调用边界。
2. 统一 local 与 server 两端新增数据库功能时的实现方式。
3. 统一 operations 与 handle 的命名、封装和并发控制要求。
4. 本文只解释文件职责，不解释表结构。

## 2\. 目录与文件职责（按端区分）

### 2.1 local 端文件职责

|文件|作用|
|-|-|
|local/database\_init.sql|本地数据库建库脚本（定义本地数据库对象）|
|local/database\_init.py|执行建库脚本，初始化本地数据库|
|local/database\_command.py|原子数据库操作层（单条 SQL 读写能力）|
|local/database\_功能名\_operations.py|组合 command 操作，形成功能级数据库规则函数|
|local/database\_功能名\_handle.py|面向功能调用入口，负责验证、分支、时序、调用 operations|

### 2.2 server 端文件职责

|文件|作用|
|-|-|
|server/database\_init.sql|服务端数据库建库脚本|
|server/database\_init.py|执行服务端建库脚本|
|server/database\_command.py|服务端原子数据库操作层|
|server/database\_功能名\_operations.py|服务端功能级数据库规则函数|
|server/database\_功能名\_handle.py|服务端功能数据库调用入口（请求级流程控制）|

### 2.3 前后端文件职责差异

1. local 端优先承接业务功能数据库调用。
2. server 端重点承接高敏数据访问、登录鉴权相关数据库操作。
3. 相同功能在两端都存在时，operations 和 handle 的流程必须分端实现，不可直接复制逻辑。

## 3\. 默认调用原则

1. 各功能默认在 local 端实现数据库调用。
2. 除非涉及高敏数据或登录逻辑或其他必须使用服务器端数据库的逻辑，否则不要在 server 端新增同类数据库调用。
3. 如果功能必须前后端同时调用数据库，必须分别实现本地逻辑与服务端逻辑。
4. 不允许修改command层，只能调用。

## 4\. 命名规范

当同一个功能模块需要调用数据库时，必须创建或复用以下文件名：

1. database\_功能名\_operations.py
2. database\_功能名\_handle.py

示例：同步功能

1. database\_synchronize\_operations.py
2. database\_synchronize\_handle.py

## 5\. operations 文件规范

文件名：database\_功能名\_operations.py

### 5.1 职责

1. 复用 database\_command 中的函数，封装成“按规则取数”的函数。
2. 复用 database\_command 中的函数，封装成“按规则执行业务写入序列”的函数。
3. 即使只调用一个 command 函数，也必须包一层 operations 函数，禁止在 handle 直接调用 command。

### 5.2 封装要求

1. 每个单独的数据库规则函数必须归属到类内。
2. 一个函数一个类封装为默认规范；如确需同类函数放在一个类中，需保持单一职责。
3. operations 内不处理外部请求协议层细节（例如 HTTP 状态码），只返回数据库语义结果。

### 5.3 参考实现风格

1. 参考 database\_synchronize\_operations 的类式封装风格。
2. 函数输入应支持最小必要参数，不暴露 command 层 SQL 细节。

## 6\. handle 文件规范

文件名：database\_功能名\_handle.py

### 6.1 职责

1. 复用 database\_功能名\_operations.py 中的类实现功能。
2. 承担验证、分情况存储、时序操作、结果组装等流程控制。
3. 提供功能可直接调用的入口，避免上层直接拼装 operations 细节。

### 6.2 封装要求

1. handle 中的一个函数不强制要求一个类封装。
2. 但应尽量使该功能通过一次类实例化即可完成全流程调用。
3. handle 不直接写 SQL，不直接替代 operations 的数据库规则职责。

### 6.3 参考实现风格

1. 参考 database\_synchronize\_handle 的流程式组织。
2. 推荐提供统一入口函数（例如 handle\_xxx\_request）。

## 7\. 前后端并发控制规范

前后端并发场景不同，必须分层处理。

### 7.1 command 层并发技术（两端共用）

1. 使用 SQLite WAL 模式。
2. 配置 busy\_timeout。
3. 对 database locked 类错误做有限重试与退避。
4. command 层只提供数据库并发基础能力，不做业务并发裁决。
5. command 层内容不允许修改，只能复用。

### 7.2 operations 层并发技术（核心层）

1. 必须实现 user\_id 粒度锁。
2. 所有同一用户的关键写路径必须串行执行。
3. 关键判定与写入应在同一串行区中完成（例如 stale 判定 + 写入）。
4. 优先在 operations 层实现并发一致性，不把核心并发逻辑放到 handle。

### 7.3 handle 层并发技术（前后端不同）

#### 服务端 handle

1. 处理请求级幂等（例如 request\_id / Idempotency-Key）。
2. 对 push、ack 等可重放请求做去重缓存或幂等落库。
3. handle 负责请求并发治理，不替代 operations 的 user 级锁。

#### 本地端 handle

1. 使用本地流程锁（例如 RLock）串行化 build\_probe/build\_push/apply\_pull/apply\_ack。
2. 重点防止“后台同步流程”与“前台本地更新流程”交错。
3. 本地端一般不需要服务端级别的全局幂等缓存。

## 8\. 新增功能流程示例

### 8.1 只在 local 端新增数据库调用（默认）

1. 新建或复用 local/database\_功能名\_operations.py。
2. 新建或复用 local/database\_功能名\_handle.py。
3. 在 handle 中调用 operations，不直接调用 command。

### 8.2 前后端都要新增数据库调用

1. 两端分别新增或复用 operations 与 handle 文件。
2. 两端分别实现并发控制，不共享同一套流程代码。
3. 服务端处理幂等与多请求竞争，本地端处理本地流程串行。

## 9\. 禁止事项

1. 禁止在 handle 层直接调用 SQL。
2. 禁止在上层业务代码直接调用 command 绕过 operations。
3. 禁止把服务端流程逻辑原样复制到 local（或反向复制）而不做分端调整。
4. 禁止忽略并发控制直接叠加新数据库功能。

## 10\. 变更检查清单

新增或修改数据库功能时，至少自检以下项目：

1. 是否按命名规范创建/复用 operations 与 handle。
2. 是否所有数据库动作都通过 command 复用实现。
3. 是否在 operations 中实现了该功能的规则封装。
4. 是否在 handle 中实现了验证、分支、时序流程。
5. 是否按前后端差异完成并发控制。
6. 是否避免了跨层职责混用（handle 代替 operations，或上层直调 command）。

