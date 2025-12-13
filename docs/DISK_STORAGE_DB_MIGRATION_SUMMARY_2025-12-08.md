# 磁盘存储风险与可迁移性总结（2025-12-08）

本文件汇总了对 MaiMBot 仓库中与磁盘/本地文件存储相关的风险点分析，以及每个项能否迁移到数据库（DB）中的可行性评估与建议。

---

## Hippo 缓存
- 风险点：`src/hippo_memorizer/chat_history_summarizer.py` 将每个聊天的 `topic_cache` 和 `current_batch` 持久化为 `data/hippo_memorizer/<chat>.json`，不同租户若使用相同 `chat_id` 会写到同一文件，产生覆盖与串租风险。
- 可迁移性：高度可迁移。模块本身仅进行文件 IO，适合在 Peewee/ORM 中新增 `HippoTopicCache` / `HippoBatch` 表来存储 JSON/text blob，按 `tenant_id/agent_id/chat_id` 建索引。
- 好处：迁入 DB 后可借助已有的 `tenant_context` 做访问隔离、并发控制和事务保证。
- 建议步骤：设计表结构（topic/title/messages/participants/no_update_checks/timestamps 等），在原模块的持久化点改为 ORM 写入，并在启动时从 DB 恢复缓存；保留现有异步锁以减少并发变更风险。
- 最新进展（2025-12-09）：已新增 `HippoTopicCache`、`HippoBatchState` 模型并在 `ChatHistorySummarizer` 中落地 `_load_topic_cache_from_db` / `_persist_topic_cache` / `_load_batch_from_db`，所有读写均走 DB，`data/hippo_memorizer` 不再被访问。
- 后续事项：补充一次性迁移脚本处理历史 JSON，确认无残留后可删除旧目录。

## 图片管理器（ImageManager）
- 风险点：`src/chat/utils/utils_image.py` 将图片与自动保存的表情写入 `data/image`（由 `ImageManager.IMAGE_DIR` 控制），数据库仅保存文件路径元数据（`Images.path`），导致文件系统为共享资源。
- 可迁移性：可迁移，但存在权衡。
  - 直接把二进制放入 DB（blob 或 base64 字段）可消除目录争用，但会导致数据库体积膨胀、备份/恢复与查询性能下降；VLM/图像处理往往需要流式或临时文件，运行时开销提高。
  - 折衷方案：引入按租户分隔的文件存储路径（`data/image/<tenant>/<agent>/…`）或迁移到对象存储（S3/MinIO），在 DB 中保存 tenant-aware 路径/URL；这样兼顾性能与隔离性。
- 建议步骤：先将 `ImageManager` 写入带租户的路径并在 DB 中记录 tenant 信息；长期可评估对象存储或按需把小媒体迁移入 DB（并配合清理策略）。
- 最新进展（2025-12-09）：`tenant_storage` 助手提供 `data/tenant_storage/<tenant>/<agent>/images` 根目录，`ImageManager` 与自动保存的表情图片均已调用该助手；`EmojiManager` 与 WebUI 在保存自动表情时也引用相同助手，数据库 `full_path`/`Images.path` 现在写入 tenant-aware 路径。
- 后续事项：围绕对象存储/生命周期策略的评估仍未展开；需要补充清理脚本以释放 per-tenant 目录中的孤立文件。

## Emoji 管理器
- 风险点：`src/chat/emoji_system/emoji_manager.py` 使用 `data/emoji` 与 `data/emoji_registed` 目录，周期扫描/注册会移动物理文件，导致租户间文件争用；周期任务目前未按 per-tenant 上下文运行。
- 可迁移性：技术上可迁移到 DB（把表情二进制与元数据存为表记录），但实现工作量大，且需改造图片处理路径（Pillow、VLM 等依赖临时文件或流 API）。
- 折衷方案：将目录拆分为 `data/emoji/<tenant>/<agent>/…` 并在 `Emoji` 表中保存带租户的 `full_path`；同时把周期扫描改为 `AsyncTaskManager` 下以每租户上下文运行，确保扫描与注册不会跨租户混淆。
- 建议步骤：短期按租户拆目录并在 DB 保存路径；中期评估将 emoji 二进制存入 DB 或对象存储并重写管理器 IO 层。
- 最新进展（2025-12-09）：`EmojiManager`、插件 API 与 WebUI 表情上传接口已统一调用 `get_registered_emoji_storage_dir()` / `tenant_storage`，物理文件落到 `data/tenant_storage/<tenant>/<agent>/emoji*`；新上传记录在 `Emoji` 表中保存完整的租户路径，可防止串租。
- 后续事项：周期扫描仍停留在单租户上下文，需要迁入 `AsyncTaskManager` 并基于租户清单动态派发；若要进一步消除磁盘依赖，可探索对象存储或 DB blob。

## 表达学习器（ExpressionLearner）
- 风险点：`ExpressionLearnerManager` 创建 `data/expression/...` 目录（`_ensure_expression_directories()`），但学习结果已写入 `Expression` 数据表，目录实际未必要。
- 可迁移性：不需要迁移（目录为冗余）；若需要保留快照，请直接在数据库中新增 JSON 字段或 `ExpressionSnapshot` 表。
- 建议步骤：确认没有外部代码依赖这些目录后移除 mkdir 逻辑，或将任何持久化快照迁移到 DB 表。

## 统计与本地存储
- 风险点：`StatisticOutputTask` 会输出 `maibot_statistics.html`，而 `local_storage` (`src/manager/local_store_manager.py`) 使用 `data/local_store.json` 存放部署时间、Telemetry UUID 等，全租户共享会导致覆盖与信息泄露。
- 可迁移性：高度可迁移。应引入一个轻量的 `RuntimeState` 表（或 `key/value` 表），例如 `(tenant_id, agent_id, key, value_json, updated_at)`，以键值语义替代 `local_store.json`。
- 好处：迁移后统计渲染或遥测身份可以按租户隔离，历史记录可由 DB 管理并纳入 `tenant_context` 校验。
- 建议步骤：实现 `RuntimeState` 表与访问辅助函数、逐步把 `local_store_manager` 的读写替换为 ORM 操作，最后删除文件依赖；统计 HTML 输出也应改为 per-tenant 存储或 API 提供。
- 最新进展（2025-12-09）：`RuntimeState` 表及管理器已落地，`local_store_manager` 仅通过 DB 读写键值，不再创建 `data/local_store.json`；统计/遥测相关调用同步迁移。
- 后续事项：补充一次性导入脚本，把旧 `local_store.json` 中的键迁移进 DB；统计 HTML 仍共用 `maibot_statistics.html`，需在下一阶段拆分目录或改为 API。

## Telemetry（已移除）
- 变更：2025-12-09 删除 `src/common/remote.py`，`TelemetryHeartBeatTask` 不再存在，部署无需心跳上报。
- 风险消除：不再请求/缓存 `mmc_uuid`，`local_storage` 中相关字段也可逐步清理。
- 后续：若未来需要遥测，可基于 `RuntimeState`/HTTP API 重新设计，上报逻辑应遵循租户隔离要求。

## 迁移计划（不含图片/Emoji 模块）

### 1. Hippo 缓存 → DB（`HippoTopicCache` / `HippoBatch`）
1. **表结构设计**：
  - `hippo_topic_cache`：`tenant_id`、`agent_id`、`chat_id`、`topics_json`、`last_topic_check_time`、`updated_at`。
  - `hippo_batches`：`tenant_id`、`agent_id`、`chat_id`、`start_time`、`end_time`、`messages_json`。
  - 新表继承 `BaseModel` 以自动注入租户信息，并为 `(tenant_id, agent_id, chat_id)` 建唯一索引。
2. **数据迁移脚本**：扫描 `data/hippo_memorizer/*.json`，解析 `topics`/`current_batch`，在设置 `tenant_context` 的脚本中写入新表；记录无法解析的文件以人工确认。
3. **代码改造**：
  - `ChatHistorySummarizer` 的 `_persist_topic_cache` / `_load_topic_cache_from_disk` / `_load_batch_from_disk` 改为 ORM 读写；删除 `HIPPO_CACHE_DIR` 依赖，仅保留可选的 debug 导出。
  - 在 `__init__` 期间预加载 DB 状态，落盘逻辑改为事务写入，沿用既有锁。
4. **验证**：编写单测或脚本，对同一 `chat_id` 在不同 `tenant_id` 下运行学习流程，确认缓存互不覆盖；回归主题触发与批次恢复功能。
5. **发布**：部署前执行一次文件→DB 回填脚本并备份原目录，部署后开启仅 DB 模式并观察日志（确保不再写文件）。

### 2. 本地存储/统计 → RuntimeState 表
1. **统一存储抽象**：新增 `RuntimeState` Peewee 模型（`tenant_id`、`agent_id`、`key`、`value_json`、`updated_at`），并提供 `runtime_state.get/set/delete` 工具函数封装 JSON 序列化。
2. **迁移脚本**：
  - 读取 `data/local_store.json`，根据部署配置确定默认 `tenant_id/agent_id`，将所有键值写入 `RuntimeState`。
  - 若存在多租户文件，需要按约定映射后写入。
3. **代码替换**：
  - `local_store_manager.py` 改为调用 `RuntimeState`，保留原 API（`__getitem__` 等）但内部走 DB。
  - `StatisticOutputTask`、`OnlineTimeRecordTask` 读取/写入 `deploy_time`、统计配置时改为通过新 API；HTML 输出路径调整为 `maibot_statistics/<tenant>.html` 或直接写入 DB/API。
4. **清理与守护**：删除 `data/local_store.json` 文件生成逻辑；在启动自检中若检测到旧文件则提示迁移。
5. **验证**：
  - 单测覆盖：多租户并发读写 runtime key，无串扰。
  - 实机验证：运行统计任务，确认不同租户生成的报告/状态独立存在。

### 3. Telemetry（无需迁移）
- 由于心跳任务已彻底删除，Telemetry 不再写入磁盘，也无需迁移到 DB。
- 若需要追踪部署信息，可在实现 RuntimeState 表后引入新的可选 telemetry 记录，但不建议恢复旧心跳逻辑。

## 总体优先级建议
- 优先级高、迁移成本低：
  - Hippo 缓存、`local_store.json` 已完成 DB 化，需补完历史数据迁移与回收旧文件。
- 中期方案（需要评估）：
  - Emoji 与图片：租户目录已上线，下一步评估对象存储/清理策略。
  - 将后台周期任务（表情扫描、流自动保存等）纳入 `AsyncTaskManager` 的 per-tenant 调度，以确保在正确 `tenant_context` 下运行。

## 结论
- 对于大多数“元数据/缓存”类的磁盘落盘（如 Hippo、local_store、学到的表达快照等），优先将其迁移到数据库，收益高且实现工作量较小。 
- 对媒体二进制（图片、表情）要权衡性能/存储成本，可先采用按租户目录或对象存储再配合 DB 路径，必要时再考虑将小体积媒体直接写入 DB。

---

_生成时间：2025-12-08_
```