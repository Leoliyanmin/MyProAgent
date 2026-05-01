# CHANGELOG

## 2026-04-26: 修复「最近交互」列表排序问题

### 问题症状
在「自我画像」页面的「最近交互」列表中，最新的对话记录没有显示出来，显示的是几天前的旧记录。

### 根因
`personal/interaction_logger.py` 中 `get_user_interactions` 方法按**文件名（UUID）**排序而非按**时间戳**排序。交互文件存储为 `{uuid}.json`，UUID 是随机生成的，其字母序与文件创建时间没有关系。

导致最新记录（如 17:44~17:53 的对话）排序靠后，被前端 `limit=5` 截断，用户看不到。

### 修改文件
- `personal/interaction_logger.py` — `get_user_interactions()` 方法

### 修改内容
**修改前**：遍历文件时直接用 `sorted(glob("*.json"), reverse=True)` 按文件名倒序，边遍历边截取 limit 条。

**修改后**：先遍历所有文件收集匹配的交互，再按 `metadata.timestamp` 字段倒序排序，最后截取 limit 条。

```python
# 修改后核心逻辑
interactions.sort(
    key=lambda x: x.get("metadata", {}).get("timestamp", ""),
    reverse=True
)
return interactions[:limit]
```

### 验证方式
API 请求 `GET /agent/profile/interactions?limit=5&offset=0` 返回的 `interactions` 数组现在按时间倒序排列，最新的记录排在第一位。
