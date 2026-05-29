## Capability: bind-flow-ux

绑定流程的用户体验改进，包括错误反馈和窗口管理行为。

### Behavior

#### 窗口管理

- **打开 CAS 登录窗口**:
  1. 检查同标签窗口是否已存在
  2. 若已存在：聚焦现有窗口，返回成功
  3. 若不存在：创建新 webview 窗口，加载 CAS 登录页
- **关闭 CAS 登录窗口**:
  1. 根据平台标签名查找窗口
  2. 若存在：关闭窗口
  3. 若不存在：静默返回成功

#### 错误反馈

- **Cookie 提取失败**:
  - 当 `extract_cookies` 返回空列表时，显示错误提示："未检测到登录信息，请确认已在弹出窗口中完成登录"
  - 将绑定状态设为 `unbound`，允许用户重试
- **绑定请求失败**:
  - 显示后端返回的错误信息
  - 将绑定状态设为 `unbound`，允许用户重试

### Constraints

- 窗口标签名固定：TIS 使用 `"cas-tis"`，Blackboard 使用 `"cas-bb"`
- 错误提示使用 Element Plus 的 `ElMessage.error()` 组件
- 错误提示应在 3-5 秒后自动消失

### Dependencies

- Element Plus UI 组件库（`ElMessage`）
- Tauri webview 窗口管理 API
