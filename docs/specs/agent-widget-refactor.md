# Agent Widget 重构 Spec

## 目标

将 Agent 功能从固定的右侧栏解放出来，作为一个可嵌入 Dashboard vue3-grid-layout 的 widget，支持和其他 widget 一样的拖拽/调整大小。最终效果：AgentMini 拥有和 AgentSidebar 相同的完整功能（WebSocket 流式、工具展示、停止生成、多行输入等）。

## 架构决策

| # | 决策项 | 结论 |
|---|--------|------|
| 1 | Agent 放在哪 | Dashboard 的 vue3-grid-layout 网格中 |
| 2 | 和 AgentSidebar 的关系 | 两者共存，通过按钮双向切换 |
| 3 | 代码结构 | 抽一个 composable `useAgentChat(sessionId)`，AgentSidebar 和 AgentMini 都调用它。**各自负责 UI 布局**（排版、间距、字号不同），composable 负责核心逻辑 |
| 4 | WebSocket 生命周期 | App 层全局管理，登录即连 |
| 5 | 并发模型 | 多实例 composable + 多 WebSocket（通过不同 sessionId 区分） |
| 6 | 聊天记录 | chatList 全局共享（Pinia store），currentChatId 全局共享 |
| 7 | 临时对话 | 默认自动保存，可选"临时模式"开关（7 天自动清理） |

## 联动规则

| 操作 | AgentSidebar | AgentMini |
|------|:---:|:---:|
| Sidebar 点"弹出到仪表板" | 折叠 | 自动加入 Dashboard 网格 |
| AgentMini 点"收回到侧边栏" | 展开 | 自动移除 |
| topbar 按钮展开 Sidebar | 展开 | 移除 AgentMini（如果在） |

## 关联文件

```
frontend/src/
├── composables/
│   └── useAgentChat.js          # NEW
├── stores/
│   └── agentChat.js              # 改
├── components/
│   ├── layout/
│   │   └── AgentSidebar.vue     # 改
│   └── mini/
│       └── AgentMini.vue        # 重写
├── App.vue                      # 改
└── stores/dashboard.js          # 可能微调
```

## 各文件改动清单

### useAgentChat.js（新建）

从 AgentSidebar 提取核心逻辑：
- WebSocket 连接/断开
- REST 发送 + 流式消息处理
- 工具调用展示
- 模型切换
- 停止生成
- 发送后刷新面板（日程/任务/邮件）
- 主题建议/删除确认处理
- 参数: `sessionId`, `isTemporary`

### agentChat.js（改）

新增：
- `markChatTemporary(chatId)` / `markChatPermanent(chatId)`
- `cleanupExpiredTempChats()` (7天TTL)
- `saveChatMessages(chatId, messagesArray)`
- `loadChatMessagesFromStorage(chatId)`
- `formatTime(timestamp)`
- `_initialized` 防重复初始化标志

### AgentSidebar.vue（改）

- 删除所有内联逻辑（WebSocket、send、model、tool 等）
- 改用 `useAgentChat('sidebar')`
- 加"弹出到仪表板"按钮 → dispatch `agent-pop-to-dashboard`
- 监听 `agent-retract-to-sidebar` → 展开自身
- 保持现有样式不变

### AgentMini.vue（重写）

- 用 `useAgentChat('dashboard-agent')`
- 完整功能：流式响应、工具展示、停止生成、多行输入、模型切换、主题建议/删除确认 widget
- 加"收回到侧边栏"按钮 → dispatch `agent-retract-to-sidebar`
- 加临时对话开关 (🕐)
- 监听 `agent-pop-to-dashboard` → 重连 WebSocket

### App.vue（改）

联动逻辑：
- 监听 `agent-pop-to-dashboard` → `toggleMiniWidget('agent')` + `isAgentOpen = false`
- `toggleAgent()` → 展开时若 Mini 存在则移除

## Composable 对外接口

```js
const chat = useAgentChat(sessionId, { isTemporary: false })

// 状态
chat.messages          // 消息列表（临时模式用本地ref，普通模式用store.messages）
chat.inputText         // 输入框 v-model
chat.isSending         // 发送中
chat.isThinking        // AI 思考中（流式）
chat.currentToolLabel  // 当前工具标签（"正在创建日程..."）
chat.activeModels      // 可选模型列表
chat.currentModelLabel // 当前模型显示文本
chat.currentProvider   // 当前provider
chat.currentModel      // 当前model名
chat.noKeyModalVisible // 未配置Key弹窗
chat.isInputComposing  // IME输入中

// 从 store 透传
chat.chatList          // 聊天记录列表
chat.currentChatId     // 当前对话 ID
chat.switchChat(id)    // 切换对话
chat.deleteChat(id)    // 删除对话
chat.createNewChat(temporary) // 新建对话
chat.loadChatMessages(id)  // 加载对话消息
chat.formatTime(ts)    // 格式化时间

// 方法
chat.sendMessage()       // 发送消息（先 loadActiveModels，空则弹窗）
chat.stopGenerating()    // 停止生成
chat.switchModel(m)      // 切换模型
chat.loadActiveModels()  // 加载可用模型列表
chat.loadCurrentModel()  // 加载当前模型
chat.connectWebSocket()  // 连接WS
chat.disconnectWebSocket() // 断开WS
chat.init()              // 初始化（加载模型 + 连WS）
chat.cleanup()           // 清理（断开WS + 保存消息）
chat.saveMessagesToStore() // 保存消息到localStorage

// IME
chat.onCompositionStart()
chat.onCompositionEnd()
chat.isImeEnter(e)       // 判断是否是输入法回车

// 渲染
chat.renderMarkdown(text)
chat.parseMessage(text)  // 解析 theme-suggestion/delete-confirm 块

// 主题/删除
chat.applyThemeSuggestion(tokens)
chat.onDeleteConfirmed(msgIdx, files)
chat.onDeleteDismissed(msgIdx)
chat.isThemeDismissed(chatId, msgIdx)
chat.markThemeDismissed(chatId, msgIdx)

// 工具标签
chat.getToolLabel(toolName)
chat.getToolChatLabel(toolName)

// 滚动容器
chat.setScrollContainer(fn) // 组件传入自己的 scrollToBottom

// 引用
chat.fmStore     // FileManager store
chat.chatStore   // AgentChat store
chat.router      // Vue Router
```

## 关键实现细节

1. **messages 引用**：非临时模式下，composable 的 `messages` 直接指向 `chatStore.messages`，避免同步问题
2. **init 只调用一次**：store 加 `_initialized` 标志，防止多个 composable 实例重复初始化
3. **WebSocket sessionId**：Sidebar 用 `'sidebar'`，Mini 用 `'dashboard-agent'`
4. **saveMessagesToStore()**：封装保存逻辑，临时模式跳过
5. **非当前对话的消息路由**：通过 localStorage 直接读写，不覆盖 store.messages
6. **联动用 CustomEvent**：
   - `agent-pop-to-dashboard`（Sidebar→Mini，App.vue 监听）
   - `agent-retract-to-sidebar`（Mini→Sidebar，AgentSidebar 监听）
7. **消息格式兼容**：消息对象 `{ role: 'user'|'assistant'|'agent'|'tool', text: string, done: boolean }`
