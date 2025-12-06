# MaiMBot 多租户改造进度（2025-12-06）

> 依据 `MULTI_TENANT_MIGRATION_STRATEGY.md` 的风险地图，梳理当前 **MaiMBot 仓库（branch: saas）已暂存的改动**，并给出后续在 `maim_db` 侧的落地建议。

## 当前暂存进展（代码层）
- `src/common/message/tenant_context.py`
  - 引入基于 `ContextVar` 的租户上下文，提供同步/异步 context manager 与便捷 getter（tenant_id/agent_id）。
  - 用途：消息入口与后续后台任务可共享同一套上下文注入机制。
- `src/common/message/runtime_config.py`
  - 新增可缓存的租户配置运行时：按 `tenant_id[:agent_id]` 生成键，TTL 60s；并发下用 asyncio 锁防抖。
  - 通过 `prepare_tenant_runtime`/`reset_tenant_runtime` 在 ContextVar 中挂载 `TenantConfigBundle`，失败时回退默认配置并发出警告。
  - 提供 `GlobalConfigProxy`/`ModelConfigProxy`，让配置读取自动透传当前租户 bundle，否则回退默认配置。
- `src/config/config.py`
  - `global_config` / `model_config` 现改为上述 Proxy 包装，默认实例保留 `default_*` 供调试回退。
  - 配置加载/模板更新逻辑保持不变，Proxy 仅在访问时切换租户视图。
- `src/common/message/api.py`
  - API Server 认证/路由层现在解析 API Key 获取 `tenant_id`/`agent_id`，带 300s 本地缓存。
  - `message_handler` 在调用聊天处理前套 `tenant_context_async` + `prepare_tenant_runtime`，处理完毕后 `reset_tenant_runtime`，保证消息链路使用对应租户配置。
  - 解析失败时仍按默认上下文处理，记录 warning。

## 覆盖范围与局限
- 目前仅在“消息入口 + 配置读取”链路落地：配置代理已接入，消息处理可感知租户上下文。
- 尚未触及风险地图中的“缓存前缀化/ChatManager/AsyncTaskManager/ORM tenant_id”改造；后台任务、文件系统、WebUI 仍潜在串租。
- 配置加载依赖 `config_merger.create_agent_global_config / create_agent_model_config`，需要确保 maim_db 提供的租户配置数据完整可读；加载失败将静默回退默认配置。

## 对 maim_db 的下一步建议
1) **模型侧支撑**：在 `maim_db` 的核心表（ChatHistory, Messages, ThinkingBack, LLMUsage, Emoji, Expression, Jargon 等）补齐 `tenant_id` 字段与索引，便于 MaiMBot 侧挂接 `TenantModel`。
2) **任务/路由协同**：为后续 MaiMBot `AsyncTaskManager` 拆租户准备配置/接口，确保 WebUI & API 请求能传递 tenant_id/agent_id（与当前 API Key 解析保持一致）。
3) **验证与监控**：补充租户切换的集成测试用例（消息入口 + 配置读取），并记录当租户配置缺失时的降级/告警策略，避免静默跑在默认租户。
4) **文件/缓存规划**：按照策略文档要求预留租户化目录/命名（emoji/image/hippo cache/统计输出），以便后续代码改造直接落地。

## 待办清单（跨仓衔接）
- 将 `TenantContext`/配置 Proxy 引入后台任务调度与 ChatManager（防止无上下文的批处理）。
- 与 `maim_db` 同步 schema 变更与配置读写接口，验证 `config_merger` 能返回按租户合成的配置。
- 完成缓存前缀化与 ORM 租户化后，回归 `MULTI_TENANT_MIGRATION_STRATEGY.md` 的风险表逐项验证。
