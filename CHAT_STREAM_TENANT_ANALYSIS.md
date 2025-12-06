# ChatStream 租户标识改造分析（落实多租户策略第 2 步）

基于 `MULTI_TENANT_MIGRATION_STRATEGY.md` 要求，对 MaiMBot 仓库内 **所有 ChatStream 生成/读取调用** 逐点审计，给出三类结论：
1) 能直接传入 `tenant_id` / `agent_id` 的位置。
2) 无法直接传参但可通过“与配置一致的上下文”获取租户的调用。
3) 即便采用上述两种手段仍可能串租或手动组装 chat_id 的残留点。

> 当前代码路径基于 `saas` 分支，重点文件：`src/chat/message_receive/chat_stream.py`。

## 1) 可直接传入租户标识的调用点
这些调用握有“消息入口”上下文，可在调用时显式附带 `(tenant_id, agent_id)` 参数，或在 ChatManager 生成 stream_id 时加入租户前缀。

- `src/chat/message_receive/bot.py`（消息主入口）
  - `get_chat_manager().register_message(message)`
  - `await get_chat_manager().get_or_create_stream(platform, user_info, group_info)`
  - 现有 API Server 已在 `message_handler` 外层设置了 `tenant_context_async` + `prepare_tenant_runtime`，可在此处直接读取上下文并将租户写入 stream_id。
- `src/chat/heart_flow/hfc_utils.py`（心流入口）
  - 两处 `get_or_create_stream(...)` 用于心流初始化/重试，调用源于消息流程，仍在租户上下文内，适合直接透传。
- `src/chat/message_receive/chat_stream.py` 内部
  - `_generate_stream_id` / `get_or_create_stream` / `get_stream_id` 可升级为接受 `(tenant_id, agent_id)` 并把租户前缀（如 `tenant:agent:`）纳入哈希输入或直接前缀化。
- 其他紧贴消息生命周期的构造：
  - `src/chat/brain_chat/brain_chat.py` / `brain_planner.py`
  - `src/chat/planner_actions/planner.py` / `action_modifier.py`
  - `src/chat/heart_flow/heartFC_chat.py`
  - `src/express/expression_learner.py`
  - `src/person_info/person_info.py`
  - 它们在消息链路后续阶段使用 `ChatStream` 或 `get_stream_name`，可沿用入口的租户前缀化 stream_id，避免额外参数扩散。

## 2) 不能轻松传参，但可用“与配置一致的上下文”注入的调用
这些调用没有显式拿到消息/租户标识，但运行时可以通过 `tenant_context`（`src/common/message/tenant_context.py`）或后续计划中的 `TenantChatManager` 来决策：

- `ChatManager` 全局实例获取 / 新建（`get_chat_manager()` 返回单例）。
  - 可在 `ChatManager._generate_stream_id` 内部读取 `tenant_context`，若无直接参数则自动前缀当前租户；缺省则回退旧行为。
- 下游只持有 `chat_id` 的读取类场景：
  - `get_stream(stream_id)` 调用点：`replyer_manager.py`、`heartflow.py`、`hippo_memorizer/chat_history_summarizer.py`、`plugin_system/core/tool_use.py`、`jargon_miner.py`、`plugin_system/core/events_manager.py` 等。
  - 若 stream_id 在生成时已包含租户前缀/哈希种子，则读取时无需显式参数；否则需在 `get_stream` 内先尝试“租户前缀 + 原 stream_id”再回退旧 key。
- 只枚举/遍历内存 `streams` 的 API：`plugin_system/apis/chat_api.py`。
  - 可在 API 层读取 `tenant_context` 过滤/命名空间隔离；没有上下文则可能跨租户枚举，需要后续在调用链（HTTP 路由）补充租户注入。

## 3) 采用参数 + 上下文后仍需重点改造的残留点
这些位置缺乏租户信息或手动拼装 chat_id，单靠上下文前缀无法完全避免串租。

- **手动拼装/存储 chat_id 的后台任务**
  - `ChatManager._auto_save_task`（`chat_stream.py`，由 `main.py` 启动）定期保存内存 streams → DB，无上下文，需改为 per-tenant 调度或在保存前明确租户前缀。
  - `src/chat/utils/statistic.py`（在线时长/统计输出）若读取 `ChatManager.streams` 将混用各租户数据；必须拆分为 per-tenant 统计或输出独立文件。
- **插件/外部 API 枚举全局 streams**
  - `plugin_system/apis/chat_api.py` 的 `get_all_streams/get_group_streams/get_private_streams/...` 直接遍历 `get_chat_manager().streams`，没有租户过滤；需要路由层传入租户或在 API 内读取 `tenant_context` 并过滤。
- **配置中使用裸 stream_id 的逻辑**
  - `src/config/official_configs.py` 的 `expression_configs` 使用哈希 chat_stream_id；若不前缀 tenant，则同群跨租户共用配置。需要将租户前缀并入哈希源或在查表前拼上租户。
- **直接按 chat_id 取文件/缓存的模块**（虽不在 ChatStream 生成处，但与 chat_id 串租强相关）
  - `hippo_memorizer/chat_history_summarizer.py` 缓存、`replyer_manager`、`mood_manager` 等使用 chat_id 作为 key/路径，必须与 ChatStream 前缀方案同步切换。
- **历史/外部入口**
  - 如未来新增非 WebSocket 的入口（CLI、测试脚本）若未设置 `tenant_context`，将继续生成无前缀 stream_id，需要在公共入口封装（同配置代理）强制注入。

## 推荐落地方案（结合三类结论）
- 在 `ChatManager._generate_stream_id` / `get_or_create_stream` 增加可选参数 `(tenant_id, agent_id)`，默认从 `tenant_context` 读取；生成 key 时将租户前缀纳入哈希或直接前缀。
- `get_stream` 增加“先查租户前缀 key，再查旧 key”逻辑，便于平滑迁移。
- `ChatManager._auto_save_task` 与所有遍历 `streams` 的 API（插件/统计）改为：
  1) 每租户一桶的 `streams` 字典，或
  2) 在访问前设置租户上下文 + 过滤；
  否则跨租户数据仍会混写 DB 与文件。
- 在 HTTP / WebSocket 路由层（或事件管理器）统一确保 `tenant_context` 已设置，避免后续调用无上下文。
- 将 `expression_config` 等以 chat_stream_id 为键的配置生成/查找逻辑改为包含租户前缀，保证配置不共享。

## 结论快照
- **可以直接传参的入口**：消息主入口 (`bot.py`)、心流入口 (`hfc_utils.py`) 以及 ChatManager 本身。
- **可靠上下文兜底的调用**：多数读取场景（`get_stream`、`get_stream_name`）和遍历 API，只要 stream_id 已含租户前缀即可。
- **必须额外改造的残留**：自动保存任务、统计/插件全局枚举、配置中裸 stream_id、以及任何未设置租户上下文的新入口。

> 建议先落地“前缀化 stream_id + get_stream 双查 + per-tenant auto-save/遍历”三件事，再回归策略文档逐项验证串租风险是否关闭。
