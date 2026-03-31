# 数据库测试说明

本文用于说明 local 与 server 两端数据库测试的区别，以及各条测试命令的运行方式。

## 1. 测试文件

- Local 端测试脚本：local/database/code/test_database_command_local.py
- Local 端测试数据：local/database/code/database_test_data.py
- Server 端测试脚本：server/database/code/test_database_command_server.py
- Server 端测试数据：server/database/code/database_test_data.py

## 2. 通用测试动作

local 与 server 两端测试脚本都支持以下动作：

- store：向选定表插入一条测试数据
- get：查询选定表并校验结果是否符合预期
- delete：删除选定表中的测试数据并校验是否删除成功
- sync：执行双端同步测试（由 local 发起，包含 server -> local pull 与 local -> server push）

两端脚本都支持按表范围执行：

- --table all
- --table <single_table>

## 3. Local 与 Server 的差异

### Local 端

- 覆盖表：user, personal_information, sync_state, account, category, data, schedule, session, chat
- 不测试：perm
- local 端无 code 表
- sync 动作为双端流程：
  - local 请求 server 生成 pull 包（模拟登录时从 server 同步）
  - local apply_pull 应用 server 数据
  - local build_push
  - server handle 接收 push 并写入 server test 库
  - server 返回 ack
  - local apply_server_ack

### Server 端

- 覆盖表：user, personal_information, sync_state, account, code, category, data, schedule, session, chat
- 不测试：perm
- 包含 server 独有的 code 表测试
- user 测试数据包含 server 专有字段：
  - user_password_hash
  - user_salt
  - user_auto_login_token
- account 测试数据包含 server 专有凭据字段：
  - account_mail_password
  - account_cookie
- server 不再提供单端 sync 测试命令。
- server 提供内部桥接动作：
  - sync_build_pull：生成发给 local 的 pull 包
  - sync_receive_push：接收 local 发来的 push 包

## 4. 测试命令

以下命令请在仓库根目录运行，并使用当前环境中的 Python 解释器（python）。

### Local 示例

- 对 local 全部表执行 store：
  - python local/database/code/test_database_command_local.py --action store --table all
- 对 local 单表执行 get：
  - python local/database/code/test_database_command_local.py --action get --table category
- 对 local 全部表执行 delete：
  - python local/database/code/test_database_command_local.py --action delete --table all
- 执行 local 发起的双端同步测试：
  - python local/database/code/test_database_command_local.py --action sync --table all

### Server 示例

- 对 server 全部表执行 store：
  - python server/database/code/test_database_command_server.py --action store --table all
- 对 server 单表执行 get：
  - python server/database/code/test_database_command_server.py --action get --table category
- 对 server 全部表执行 delete：
  - python server/database/code/test_database_command_server.py --action delete --table all
- server 单端 sync 已禁用。
- 如需手动触发 server 发包桥接（一般不需要手工执行）：
  - python server/database/code/test_database_command_server.py --action sync_build_pull --table all --user-id user-test-001 --packet-file <pull_packet.json> --marker <server_marker>
- 如需手动触发 server 接包桥接（一般不需要手工执行）：
  - python server/database/code/test_database_command_server.py --action sync_receive_push --table all --packet-file <packet.json> --ack-file <ack.json>

## 5. 双端同步推荐顺序

以下命令请在仓库根目录运行：

1. 准备 local 数据：
  - python local/database/code/test_database_command_local.py --action store --table all
2. 准备 server 基线用户（至少 user 表需要存在）：
  - python server/database/code/test_database_command_server.py --action store --table user
3. 执行双端同步（仅需运行 local 命令）：
  - python local/database/code/test_database_command_local.py --action sync --table all

## 6. 安全说明

- 测试脚本使用持久化测试数据库：
  - local/database/test_db/test_local.db
  - server/database/test_db/test_server.db
- sync 动作会临时 patch command 函数，使 handle 内调用也指向对应 test 库。
