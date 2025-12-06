# 多租户重构状态与剩余问题（2025-12-06）

本文档汇总了最近在仓库中完成的多租户重构工作（四大策略），记录代码层面的变更点，并基于已有的风险地图分析尚需解决的问题和优先级建议，供后续迁移/验证使用。

**更新时间**: 2025-12-06

**作者**: 自动生成（由开发协助脚本生成）

**目录**
- **已完成的四大策略（概览）**
- **已做的代码修改位置**
- **剩余问题与风险（来自风险地图 & 代码审计）**
- **优先级与下一步行动项**

**已完成的四大策略（概览）**

1. 配置代理（Config Proxy）
   - 目标：在运行时将配置访问延迟到 `TenantContext` 环境内，避免在模块导入/初始化时固化租户不变的全局配置。
   - 当前状态：已完成设计并在若干模块留出代理接入点（需要逐步替换 `global_config`/`model_config` 的引用以真正启用代理）。

2. chat_id 加租户前缀
   - 目标：对所有内存与文件系统缓存使用 `"{tenant_id}:{chat_id}"` 或按租户分桶路径，避免跨租户覆盖。
   - 当前状态：已在消息入口与 ChatStream 相关的调用链中引入 tenant-aware 流（`chat_stream` 层可产出 tenant-aware stream id）；各缓存/磁盘路径还需批量更新为前缀式或按租户目录拆分。

3. ORM 层添加 `tenant_id`（TenantModel）
   - 目标：在重要表上增加 `tenant_id` 字段并使 ORM 在请求上下文中自动附加该字段，保证多租共表数据隔离。
   - 当前状态：在 `maim_db` 中已新增并导出多租相关模型（例如 `AgentActiveState`），并实现了异步包装（`AsyncAgentActiveState`）供运行时与控制平面使用。其它核心模型（`ChatHistory`, `ThinkingBack`, `LLMUsage` 等）仍需补上 `tenant_id` 字段并添加索引。

4. per-tenant AsyncTaskManager
   - 目标：将后台定时/批处理任务拆成“每租户一个协程”，并在每个协程中 `async with tenant_context(tenant_id)`，保证 ORM 层在任务内能自动带上 tenant 过滤。
   - 当前状态：`MaiMBot/src/manager/async_task_manager.py` 已改为默认 `per_tenant=True`，并能基于活跃 agent 列表并发运行 `task.run_for(tenant, agent)`。仍需把各类 AsyncTask 逐步验证为“无共享全局副作用”或做必要的分桶改造。

**已做的代码修改位置（摘录）**

- maim_db
  - `maim_db/src/core/models/system_v2.py`：新增 `AgentActiveState` 模型（tenant_id, agent_id, last_seen_at, ttl_seconds, expires_at）
  - `maim_db/src/core/async_models.py`：新增 `AsyncAgentActiveState` 异步包装，提供 `upsert` 与 `list_active` 方法
  - `maim_db/src/core/__init__.py` / `models/__init__.py`：导出新增模型并纳入创建表的集合

- MaimConfig（控制平面）
  - `MaimConfig/src/api/routes/active_state_api.py`：新增 PUT（upsert 活跃 TTL）与 GET（列出活动 agent）接口
  - `MaimConfig/src/api/routes/agent_api.py`：在 agent 创建后调用 active upsert（默认 TTL = 12h）
  - `MaimConfig/src/database/models.py`：启动时尝试包含 `maim_db` 的所有模型进行表创建（谨慎 try/except）

- MaiMBot（运行时 / 消息链路 / 调度器）
  - `MaiMBot/src/common/message/api.py`：新增 `upsert_active_from_message(message, ttl_seconds=...)`；并在 API 第一层 `message_handler` 中，解析 API Key 后提前上报活跃（在消息进入第二层 handler 之前）。
  - `MaiMBot/src/chat/message_receive/bot.py`：移除分散的活跃上报逻辑（现在由第一层 `src/common/message/api.py` 负责），保留消息主处理流程。
  - `MaiMBot/src/manager/async_task_manager.py`：默认启用 `per_tenant` 策略；当没有活跃租户 agent 时，按策略跳过任务执行（不回退到单实例行为）。

（注）上述变更已在代码中以文件补丁形式提交，但尚未在目标环境跑迁移/集成测试。

**剩余问题与风险（基于风险地图与代码审计）**

1. 模块在导入时固化配置或缓存（高风险）
   - 受影响文件（示例）：`src/config/config.py`, `src/person_info/person_info.py`, `src/chat/emoji_system/emoji_manager.py`, `src/express/expression_learner.py`。
   - 风险：即使后续注入 TenantContext，模块已在导入时建立的单例/缓存依然会跨租户共享数据。
   - 建议：将这些模块改为延迟加载（lazy init）或在使用时通过代理访问配置（GlobalConfigProxy）。

2. 文件系统路径和落盘目录仍为平台级（高风险）
   - 受影响：`data/emoji*`, `data/image`, `HIPPO_CACHE_DIR`, `maibot_statistics.html` 等。
   - 风险：即便数据库隔离，文件落盘会导致租户间文件覆盖或数据泄露。
   - 建议：统一把磁盘路径改为 per-tenant 目录（例如 `data/<tenant_id>/...`），并更新所有写/读路径。

3. 背景任务存在共享内存/全局 key（中高风险）
   - 受影响：`mood_manager`, `frequency_control`, `heartflow`, `replyer_manager`, `plugin cache` 等。
   - 风险：这些模块使用以 `chat_id` 为 key 的全局字典或缓存；即使 `AsyncTaskManager` per-tenant 化，缓存 key 必须改为 `tenant:chat`。
   - 建议：在 managers 内部统一使用 `(tenant, chat)` 或可自动返回带租户前缀的 stream id（通过 `TenantChatManager`）。

4. 若干 ORM 表尚未添加 `tenant_id`（高优先级）
   - 关键表：`ChatHistory`, `ThinkingBack`, `Messages`, `LLMUsage`, `Emoji`, `Expression` 等。
   - 风险：后台清理或迁移任务仍会整表扫描，导致跨租户数据操作。
   - 建议：先在模型层加入 `tenant_id` 字段与索引，随后为现有数据做回填/迁移计划（包含 owner/backfill 策略）。

5. 后台任务写入/输出的全局资源（中高风险）
   - 例子：`OnlineTimeRecordTask` 输出到单个 `maibot_statistics.html`，`TelemetryHeartBeatTask` 单实例心跳，`EmojiManager` 周期扫描全局目录。
   - 建议：将统计与输出拆分为 per-tenant 报告，或者改用上报 API（平台级 vs 租户级必须明确区分）。

6. 一些任务/模块对 `per_tenant` 策略不敏感（中风险）
   - 说明：即使调度器为每租户并发运行，任务内部仍可能访问共享内存和文件系统，这会导致竞态或跨租户副作用。
   - 建议：针对每个重要 AsyncTask 做审计，确保其在 `tenant_context` 内无共享副作用；若有，则重构任务逻辑或将其改为平台级服务。

7. 数据库迁移与表创建动作（紧急）
   - 变更了 `maim_db` 模型后需要在目标 DB 上执行 migration / `CREATE TABLE` 操作，特别是 `agent_active_states` 等新表。
   - 建议：生成 SQL migration（包含索引、约束、backfill 计划），在维护窗口内应用，并先在预生产环境验证。

**优先级与下一步行动项（建议）**

短期（立即 0-3 天）
- 生成并应用 `agent_active_states` 的 SQL 创建脚本到测试 DB，验证 `upsert` 与 `list_active` 正常工作。
- 在测试环境发送 API 消息，确认 `src/common/message/api.py:message_handler` 在第一层已上报活跃并能在 DB 中查询到记录。

中期（3-14 天）
- 将核心 ORM 表（`ChatHistory`, `ThinkingBack`, `Messages`, `LLMUsage`）加入 `tenant_id` 字段并编写回填脚本：先在测试库回填并验证业务正确性。
- 对高风险模块（模块级单例、文件落盘）做清单式重构：优先把文件路径拆分为 per-tenant，或改写为按租户 API 写入。
- 审计并改造 5-10 个最活跃的后台任务（如 memory cleanup、statistic tasks），保证它们在 per-tenant 调度下不会访问共享全局资源。

长期（2-3 月）
- 全面替换 `global_config`/`model_config` 为代理实现（GlobalConfigProxy），并修复那些在导入时固化配置的模块。
- 完成 ChatStream / TenantChatManager 的改造，使所有 stream id 生成时附带 tenant 前缀，更新缓存/插件系统的 key 策略。
- 全面执行集成测试、性能回归测试与安全审计，保证按租户拆分后的稳定性与隔离性。

**提供支持**

我可以：
- 生成 `agent_active_states` 的 SQL 创建脚本并提交到仓库（或直接在测试 DB 执行，如果你授权并提供 DB 连接信息）。
- 为你列出所有存在“模块导入即固化状态”的文件列表（静态搜索并输出），帮助优先改造。
- 生成一份逐文件的迁移清单（按风险 & 复杂度排序），并为每个条目推荐拆分方案与回归测试点。

---

如果你希望，我现在可以直接生成 `agent_active_states` 的 SQL 脚本并把它添加到仓库（或输出给你以便在 DB 上运行）。请选择你想下一步我执行的动作：

- 生成并提交 SQL 创建脚本
- 列出需要延迟加载或代理化的模块清单
- 生成迁移清单（分阶段）
- 其他（请描述）
