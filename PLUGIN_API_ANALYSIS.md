# MaiMBot 插件接口分析报告

本文档详细分析了 `MaiMBot/src/plugin_system/apis/` 目录下暴露给插件的所有接口，梳理了其背后的调用链及依赖关系。

> **注意**: 当前所有接口设计均基于单租户/单机模式，大量依赖全局单例（Global Singletons），在 SaaS 多租户环境下存在严重的数据隔离风险。

---

## 1. 核心功能 API

### `send_api.py` (消息发送)
负责向聊天流发送文本、表情、图片、语音等消息。

*   **调用链**:
    *   插件调用 `send_api.text_to_stream(text, stream_id)`
    *   `send_api._send_to_target`
    *   **依赖**: `src.chat.message_receive.chat_stream.get_chat_manager().get_stream(stream_id)` (全局 ChatManager 查找流)
    *   **依赖**: `src.chat.message_receive.uni_message_sender.UniversalMessageSender` (消息发送器)
    *   **依赖**: `src.config.config.global_config` (获取机器人 Bot ID)
*   **关键风险**: `get_chat_manager()` 可访问所有租户的流；`global_config` 只能获取默认 Bot 身份。

### `llm_api.py` (模型交互)
提供 LLM 生成能力。

*   **调用链**:
    *   插件调用 `llm_api.generate_with_model(prompt, model_config)`
    *   `src.llm_models.utils_model.LLMRequest` (构建请求)
    *   **依赖**: `src.config.config.model_config` (全局模型配置单例)
*   **关键风险**: 插件获取的 `model_config` 是全局配置，无法针对租户应用不同的模型策略或配额。

### `database_api.py` (数据库操作)
提供 ORM 风格的数据库 CRUD 操作。

*   **调用链**:
    *   插件调用 `database_api.db_query(ModelClass, ...)`
    *   直接调用 `ModelClass.select()`, `ModelClass.create()` 等 Peewee 方法。
    *   **依赖**: 传入的 `peewee.Model` 类 (如 `ActionRecords`)。
*   **关键风险**: 如果传入的 Model 类没有配置 TenantContext 过滤器，插件可查询全表数据。

### `config_api.py` (配置获取)
获取全局配置和用户 ID。

*   **调用链**:
    *   插件调用 `config_api.get_global_config(key)`
    *   **依赖**: `src.config.config.global_config` (直接读取全局对象)
*   **关键风险**: 暴露底层全局配置，无租户隔离。

---

## 2. 业务功能 API

### `emoji_api.py` (表情包)
表情包的查询、获取、注册和删除。

*   **调用链**:
    *   插件调用 `emoji_api.get_by_description(desc)`
    *   **依赖**: `src.chat.emoji_system.emoji_manager.get_emoji_manager()` (全局单例)
    *   **依赖**: `data/emoji` 目录 (物理文件存储)
*   **关键风险**: 所有租户共享同一个 `EmojiManager` 和文件目录，容易导致表情包数据混淆或覆盖。

### `person_api.py` (用户信息)
获取用户画像信息（昵称、印象等）。

*   **调用链**:
    *   插件调用 `person_api.get_person_value(person_id, field)`
    *   **依赖**: `src.person_info.person_info.Person` 类
    *   `Person` 内部初始化时访问数据库和全局配置。
*   **关键风险**: `Person` 对象未显式绑定租户上下文。

### `mood_api.py` (情绪系统)
查询聊天的情绪值。

*   **调用链**:
    *   插件调用 `mood_api.get_mood_by_chat_id(chat_id)`
    *   **依赖**: `src.mood.mood_manager.mood_manager` (全局单例)
*   **关键风险**: 情绪状态存储在全局管理器中，跨租户可能通过 `chat_id` 碰撞访问。

### `auto_talk_api.py` (主动发言)
设置主动发言概率。

*   **调用链**:
    *   插件调用 `auto_talk_api.set_question_probability_multiplier(chat_id, val)`
    *   **依赖**: `src.chat.heart_flow.heartflow.heartflow_chat_list` (全局心流字典)
*   **关键风险**: 直接操作全局内存中的心流对象，无租户隔离。

### `generator_api.py` (回复生成器)
获取回复器并生成回复。

*   **调用链**:
    *   插件调用 `generator_api.generate_reply(...)`
    *   **依赖**: `src.chat.replyer.replyer_manager.replyer_manager` (全局回复器管理器)
    *   `replyer_manager` 查找或创建 `DefaultReplyer`。
*   **关键风险**: 回复器实例可能被缓存复用，且依赖全局配置。

---

## 3. 插件管理与注册 API

### `component_manage_api.py` (组件管理)
查询、启用、禁用组件（Action, Command, Tool 等）。

*   **调用链**:
    *   插件调用 `get_all_plugin_info()` / `globally_disable_component(...)`
    *   **依赖**: `src.plugin_system.core.component_registry.component_registry` (全局组件注册表)
    *   **依赖**: `src.plugin_system.core.global_announcement_manager.global_announcement_manager` (局部禁用管理)
*   **关键风险**: 所有组件注册在全局注册表中；局部禁用配置也是全局管理的。

### `plugin_manage_api.py` (插件生命周期)
列出、加载、卸载插件。

*   **调用链**:
    *   插件调用 `list_loaded_plugins()`
    *   **依赖**: `src.plugin_system.core.plugin_manager.plugin_manager` (全局插件管理器)
*   **关键风险**: 插件加载/卸载影响整个进程，无法针对单一租户操作。

### `plugin_register_api.py` (装饰器注册)
提供 `@register_plugin` 装饰器。

*   **调用链**:
    *   `@register_plugin`
    *   **依赖**: `src.plugin_system.core.plugin_manager.plugin_manager` (记录插件类和路径)
*   **关键风险**: 将插件类直接注册到全局字典。

### `tool_api.py` (工具获取)
获取工具实例或定义。

*   **调用链**:
    *   插件调用 `get_tool_instance(name)`
    *   **依赖**: `src.plugin_system.core.component_registry` (查找工具类)
*   **关键风险**: 工具配置从全局插件配置中读取。

---

## 总结

当前插件 API 体系完全建立在**单实例单租户**的假设之上。几乎每个 API 模块都最终指向一个全局单例管理器（`Manager`）或全局配置对象（`global_config`）。在多租户改造完成前，这些接口无法安全地对外开放。
