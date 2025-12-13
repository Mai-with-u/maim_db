# ChatStream 调用覆盖评估（基于当前上下文策略）

日期：2025-12-06
说明：本报告列出仓库中检索到的所有 `ChatStream` / `chat_id` 相关的生成或读取调用点，并判断该调用点在当前已部署的上下文策略（即 `tenant_context_async` + `prepare_tenant_runtime` 在 `src/common/message/api.py` 的消息入口实现）下是否被覆盖。对于“覆盖”的定义：该调用在其典型调用路径上会运行在已经建立的 `tenant_context`（或显式传入 tenant_id）环境下，从而能安全地使用不带租户的 stream_id 或在生成时自动获得租户；否则视为未覆盖或条件覆盖。

---

总结说明（快速结论）：
- 被当前上下文策略覆盖（YES）的调用点：消息主入口链路内的调用（`bot.py` 中的 `get_or_create_stream` 以及消息同步触发的下游同步调用），因为 `src/common/message/api.py:message_handler` 已在处理流中引入 `tenant_context_async` + `prepare_tenant_runtime`。
- 不被覆盖（NO）的调用点：典型的后台定时任务 / 异步独立任务（如 `ExpressionReflector`、`JargonMiner`、`MoodManager` 的周期任务、`ChatManager._auto_save_task` 等）以及模块级的全局枚举/统计接口（如 `plugin_system/apis/chat_api.py`），这些路径默认没有在外层建立 tenant 上下文。
- 有条件覆盖（CONDITIONAL）的调用点：很多模块（工具执行器、事件管理器、send_api、replyer、brain_chat、planner）在消息处理路径中会被覆盖（因为它们被 message pipeline 调用），但也可能被后台或外部调用触发，在这些非消息入口路径上则不被覆盖。

---

下面按文件逐条列出（文件名 — 行/函数 — 覆盖结论 — 说明/建议）：

- `src/chat/message_receive/bot.py` — `get_or_create_stream(...)` 调用
  - 覆盖：YES
  - 说明：`bot.message_process` 会被 `src/common/message/api.py:message_handler` 在 `async with tenant_context_async(...):` 内调用，因此这里生成/获取 stream_id 时能通过 context 读取 tenant，已覆盖。
  - 建议：无需改动；确保所有外部消息入口都走该 handler 或类似的上下文包装。

- `src/chat/heart_flow/hfc_utils.py` — `get_or_create_stream(...)`（`send_typing` / `stop_typing`）
  - 覆盖：NO (默认)
  - 说明：这两个工具函数可被独立调用（例如定时心流或外部 API），当前代码未在函数内部建立 tenant_context，故默认无上下文。
  - 建议：在调用方确保设置 tenant 上下文，或将这两个函数改为接收 `tenant_id/agent_id` 参数并传递给 `get_or_create_stream`。

- `src/express/expression_reflector.py` — 多处 `await chat_manager.get_or_create_stream(...)` 与 `chat_manager.get_stream(...)`
  - 覆盖：NO
  - 说明：`ExpressionReflector`/Manager 的 check/ask/调度通常是后台周期任务或独立调度器触发，缺少外层 tenant 上下文。
  - 建议：将反思调度拆成 per-tenant 执行或在任务入口注入 `tenant_context`，或者改为传参式传入 tenant/agent。

- `src/express/expression_learner.py` — `get_stream(...)`、`get_stream_name(...)`
  - 覆盖：NO
  - 说明：学习器触发通常由定时/批量任务或管理器触发，默认无 tenant 上下文。
  - 建议：同上，按租户循环执行学习或在实例创建时需要显式 tenant 参数。

- `src/jargon/jargon_miner.py` — `get_stream(self.chat_id)` 用于学习/推断
  - 覆盖：NO
  - 说明：`JargonMiner` 的 `run_once()` 为异步独立任务，可能由后台任务触发，默认无 tenant 上下文。
  - 建议：把调用方（任务调度器）改为 per-tenant 调度，或在 miner 实例化时提供 tenant 标识并在读取 chat_stream 时构造带 tenant 的 id。

- `src/mood/mood_manager.py` / `ChatMood` — 构造时 `get_stream(self.chat_id)`
  - 覆盖：NO
  - 说明：情绪管理以管理器与后台任务形式存在（`MoodRegressionTask`），默认不在 tenant_context 下运行。
  - 建议：将 `MoodManager` 的周期任务改为 per-tenant 执行或在获取/创建 `ChatMood` 时强制传 tenant。

- `src/plugin_system/core/tool_use.py` — `ToolExecutor.__init__` 中 `get_stream(self.chat_id)`
  - 覆盖：CONDITIONAL
  - 说明：工具执行器通常在消息处理流程（命令处理/插件执行）中被构建 —— 此路径有 tenant context，因此覆盖。但若工具执行器被外部直接调用（例如管理脚本或后台任务），则无上下文。
  - 建议：在工具执行器构造处接受可选 `tenant_id`/`agent_id` 参数或在使用点确保上下文已建立。

- `src/plugin_system/core/events_manager.py` — 多处 `get_stream(stream_id)` 调用（事件分发/构建消息）
  - 覆盖：CONDITIONAL
  - 说明：事件由消息 pipeline 触发时覆盖；若事件由外部/后台触发（外部 scheduler、管理命令等），则不被覆盖。
  - 建议：事件触发的调度器/调用者需要负责在外层设置 tenant_context 或传入带租户前缀的 stream_id。

- `src/plugin_system/apis/send_api.py` — `_send_to_target` 使用 `get_stream(stream_id)`
  - 覆盖：CONDITIONAL
  - 说明：`send_api` 可被消息流程内调用（覆盖）或被外部 API/脚本直接调用（不覆盖）。注意 `src/common/message/api.py` 的 message_handler 仅为 incoming messages 设置上下文，不会自动给所有调用 `send_api` 的外部入口设置上下文。
  - 建议：外部/HTTP 的发送端点应在入参中包含 API Key / 租户信息并在入点建立 tenant_context，内部模块调用则可沿用上下文。

- `src/plugin_system/apis/chat_api.py` — 遍历 `get_chat_manager().streams` 的函数（get_all_streams / get_group_streams / ...）
  - 覆盖：NO
  - 说明：这些 API 直接访问全局 `streams` 字典并返回 / 枚举，不会做 tenant 过滤，也没有依赖 tenant_context。
  - 建议：API 层应读取当前请求的 tenant（HTTP header / API Key 解析）并在返回前做过滤，或改为只返回当前 tenant 的 streams（需要流 id 前缀或分桶策略）。

- `src/person_info/person_info.py` — `store_person_memory_from_answer(..., chat_id)` 中 `get_stream(chat_id)`
  - 覆盖：CONDITIONAL
  - 说明：该函数可能在消息处理流程中由交互触发（覆盖），也可能被外部调用（不覆盖）。
  - 建议：明确调用方责任，或在函数入口强制要求 `tenant_id` 参数。

- `src/chat/brain_chat/brain_chat.py`, `src/chat/heart_flow/heartFC_chat.py`, `src/chat/planner_actions/action_modifier.py`, `src/chat/replyer/replyer_manager.py`, `src/chat/utils/utils.py` 等使用 `get_stream(stream_id)` 的位置
  - 覆盖：大多为 CONDITIONAL
  - 说明：这些组件在消息处理链路中会被覆盖；但也可能有后台/外部触发点导致无上下文。
  - 建议：同上，优先用 context 覆盖典型消息路径，对独立/后台触发点实施 per-tenant 调度或在调用时传 tenant 参数。

- `src/chat/message_receive/chat_stream.py` 内部（`_generate_stream_id` / `get_stream_id` / `get_or_create_stream`）
  - 覆盖：N/A（这是生成/访问点，本次已改造为强制依赖上下文或显式参数）
  - 说明：已修改以在缺失 tenant 时抛错，强制调用方在外层注入 tenant 或显式传 tenant 参数。

---

结论与行动建议（优先级排序）：
1. **保证消息入口覆盖**（已完成）：继续确保所有外部消息入口（WebSocket / HTTP API /平台对接）都走 `src/common/message/api.py` 或等效的入口逻辑，从而自动注入 `tenant_context`。
2. **改造后台任务为 per-tenant 执行**：将 `ExpressionReflector`、`JargonMiner`、`MoodManager`、`ChatManager._auto_save_task`、统计类任务等改为枚举租户列表并为每个租户在独立上下文中运行任务（`async with tenant_context_async(...)` 或显式传 tenant）。
3. **对条件覆盖的模块逐一硬化**：扫描 `plugin_system`、`send_api`、`tool_use`、`events_manager` 等，加入参数可选项 `tenant_id/agent_id`，并在模块入口处做一次策略选择：优先使用当前 context，否则要求显式传参并报错。
4. **封装/文档化兼容策略**：短期可以在 `get_stream`/`get_or_create_stream` 中保留“先查 tenant 前缀再查旧 key”的迁移逻辑（可选开启），但你已选择不保留向后兼容的话，应在所有调用点完成改造后再清理旧逻辑。

---

如果你同意，我下一步可以：
- 自动生成一份调用点清单（含文件/行号/函数）并将每一项标为 YES/NO/CONDITIONAL（目前已基于扫描初步判断）；或
- 直接修改若干关键调用点（例如在 `hfc_utils.send_typing`、`expression_reflector` 的调度入口）为显式接收 `tenant_id`，并添加注释/抛错；或
- 生成一份迁移计划（按优先级和改造成本排序的具体修改任务清单）。

请选择下一步行动。