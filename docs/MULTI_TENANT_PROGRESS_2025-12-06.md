# MaiMBot 多租户改造进度（2025-12-06，2025-12-09 更新）

> 依据 `MULTI_TENANT_MIGRATION_STRATEGY.md` 的风险地图，梳理当前 **MaiMBot 仓库（branch: saas）已暂存的改动**，并给出后续在 `maim_db` 侧的落地建议。本页已在 2025-12-09 更新磁盘迁移成果。

## 2025-12-09 新增：磁盘 → DB/租户目录迁移
- `src/hippo_memorizer/chat_history_summarizer.py`
  - 新增 `HippoTopicCache`、`HippoBatchState` 模型后，主题缓存/批次读取与持久化完全走 DB（`_load_topic_cache_from_db`、`_persist_topic_cache`、`_load_batch_from_db`）。
  - JSON 文件目录 `data/hippo_memorizer` 停止写入，等待一次性历史导入脚本。
- `src/manager/local_store_manager.py`
  - 新的 `RuntimeState` 表承载原 `data/local_store.json` 的键值，`LocalStoreManager` API 向后兼容但内部改为 Peewee 读写。
  - 统计/遥测调用通过 `RuntimeState` 隔离租户，部署时不再创建全局 JSON 文件。
- `src/common/utils/tenant_storage.py` + `src/chat/utils/utils_image.py` + `src/chat/emoji_system/emoji_manager.py` + `src/webui/emoji_routes.py`
  - 引入 `tenant_storage` 帮助函数，统一落盘根路径 `data/tenant_storage/<tenant>/<agent>/...`。
  - 图片、自动保存 emoji、WebUI/插件上传的注册目录全部改为租户路径，`Emoji`/`Images` 表存储 tenant-aware `full_path`。
  - 仍需把 Emoji 周期扫描迁入 `AsyncTaskManager` 以便按租户调度。

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
- `src/hippo_memorizer/chat_history_summarizer.py`
  - 替换磁盘 JSON，使用 `HippoTopicCache` / `HippoBatchState` 表按 `(tenant_id, agent_id, chat_id)` 存储主题与批次缓存。
  - 启动阶段即从 DB 恢复，运行中通过 `_persist_topic_cache` 原子化写库。
- `src/manager/local_store_manager.py`
  - 适配 `RuntimeState` 表，实现键值到 DB 的透明过渡；旧 `data/local_store.json` 仅作为可选导入源。
  - `StatisticOutputTask`、在线时长等调用全部读写 DB，解决共享文件风险。
- `src/common/utils/tenant_storage.py` & `src/chat/utils/utils_image.py` & `src/chat/emoji_system/emoji_manager.py` & `src/webui/emoji_routes.py`
  - 新 helper 为图片/emoji/缓存提供租户目录；`ImageManager`、emoji 自动保存、WebUI 上传、插件 API 全部写入 tenant-aware 路径。
  - `Emoji`、`Images` 表的 `full_path`/`path` 字段现记录绝对路径，便于巡检。

## 覆盖范围与局限
- 消息入口 + 配置代理 + Hippo 缓存 + RuntimeState + 图片/emoji 目录已经租户化，核心磁盘 JSON 风险基本清零。
- 仍待纳入范围：AsyncTaskManager 的 per-tenant 派发、ChatManager 的缓存拆前缀、统计 HTML 的 per-tenant 输出。
- 配置加载依赖 `config_merger.create_agent_global_config / create_agent_model_config`，需要确保 maim_db 提供的租户配置数据完整可读；加载失败仍会回退默认配置。
- Emoji 周期扫描尚未套 `tenant_context_async`，需要等目录/数据库完全租户化后迁移调度器。

## 对 maim_db 的下一步建议
1) **模型侧支撑**：在 `maim_db` 的核心表（ChatHistory, Messages, ThinkingBack, LLMUsage, Emoji, Expression, Jargon 等）补齐 `tenant_id` 字段与索引，便于 MaiMBot 侧挂接 `TenantModel`。
2) **任务/路由协同**：为后续 MaiMBot `AsyncTaskManager` 拆租户准备配置/接口，确保 WebUI & API 请求能传递 tenant_id/agent_id（与当前 API Key 解析保持一致）。
3) **验证与监控**：补充租户切换的集成测试用例（消息入口 + 配置读取），并记录当租户配置缺失时的降级/告警策略，避免静默跑在默认租户。
4) **文件/缓存规划**：在 maim_db 侧同时记录媒体对象/缓存的租户元数据，方便未来跨仓排障；统计 HTML 可迁入 DB 或对象存储并提供租户查询接口。
5) **历史数据迁移**：提供一次性工具，把旧 `data/hippo_memorizer` 与 `data/local_store.json` 的内容导入到新表，完成后可在部署脚本中加入自检。

## 待办清单（跨仓衔接）
- 将 `TenantContext`/配置 Proxy 引入后台任务调度与 ChatManager（防止无上下文的批处理）。
- 与 `maim_db` 同步 schema 变更与配置读写接口，验证 `config_merger` 能返回按租户合成的配置。
- 将 Emoji 周期扫描、聊天流自动保存、统计输出等周期任务迁入 `AsyncTaskManager`，并在调度入口注入 `tenant_context_async`。
- 为 Hippo/RuntimeState/媒体目录编写历史迁移与巡检脚本，纳入部署 checklist。
- 完成缓存前缀化与 ORM 租户化后，回归 `MULTI_TENANT_MIGRATION_STRATEGY.md` 的风险表逐项验证，并新增针对媒体/缓存的测试用例。
