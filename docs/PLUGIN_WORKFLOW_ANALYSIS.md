# 现有插件工作流程及隔离风险分析

本文档基于对 `src/plugins` 目录下典型插件（`plugin_management`, `emoji_plugin`）的代码分析，总结了当前插件系统的工作流程，并识别了关键的隔离风险点。

## 1. 通用工作流程

当前插件遵循以下标准生命周期和交互模式：

### 1.1 注册与加载
*   **代码位置**: `plugin.py` 中使用 `@register_plugin` 装饰器。
*   **流程**:
    1.  插件类继承自 `BasePlugin`，定义元数据（名称、版本、依赖）。
    2.  `get_plugin_components` 方法返回插件包含的组件列表（Commands, Actions, EventHandlers）。
    3.  系统启动时，`PluginManager` 扫描目录，加载所有插件类到**全局字典**中。
*   **风险**:
    *   **代码共享**: 所有租户共享同一份类定义。如果类中包含类变量（Class Variables）用于存储状态，这些状态将在所有租户间共享。
    *   **配置加载**: 插件通常自带 `config.toml`。目前配置加载机制似乎是单例的，无法轻易为不同租户加载不同的配置值。

### 1.2 组件激活与执行
*   **代码位置**: `emoji.py` 或 `plugin.py` 中的组件类（如 `ManagementCommand`, `EmojiAction`）。
*   **流程**:
    1.  **Command**: 只有在用户发送的消息匹配正则表达式时触发。`execute` 方法被调用。
    2.  **Action**: 由 `ActionPlanner` 或规则引擎触发。`execute` 方法被调用。
    3.  **Context**: 组件实例通常能获取到 `self.message` 或 `self.chat_stream`，其中包含 `chat_id` 和 `stream_id`。
*   **风险**:
    *   **上下文信任**: 组件虽然能获取 `stream_id`，但它调用的下游服务（如下述 API）往往不校验该 `stream_id` 是否属于当前调用链的租户。

### 1.3 下游服务调用
插件通过 `src.plugin_system.apis` 模块调用系统功能。这是**风险最集中**的环节。

*   **API 调用模式**:
    *   `send_api.text_to_stream(..., stream_id)`
    *   `emoji_api.get_random()`
    *   `llm_api.generate_with_model(...)`
*   **风险**:
    *   **隐式全局依赖**: API 内部直接查找全局单例（`ChatManager`, `EmojiManager`）。
    *   **越权访问**: 一个恶意的或有 Bug 的插件，只需传入其他租户的 `stream_id`，即可通过 `send_api` 向其发送消息，或通过 `message_api` 读取其历史记录。

---

## 2. 典型插件案例分析

### 2.1 案例一：`plugin_management` (管理插件)
*   **功能**: 列出、加载、卸载插件。
*   **流程**:
    1.  解析命令 `/pm plugin list`。
    2.  调用 `plugin_manage_api.list_loaded_plugins()`。
    3.  调用 `send_api` 发送结果。
*   **隔离风险**:
    *   **全局可见性**: `list_loaded_plugins` 返回的是**进程级**的已加载插件列表。某租户管理员执行此命令，可以看到（甚至可能操作）系统级的插件状态，而非仅限于该租户订阅的插件。
    *   **全局操作**: `load/unload` 命令直接修改全局 `plugin_manager` 状态，影响**所有**租户。一个租户卸载了插件，所有租户都不可用了。

### 2.2 案例二：`emoji_plugin` (业务插件)
*   **功能**: 发送表情包。
*   **流程**:
    1.  `EmojiAction` 被触发。
    2.  调用 `emoji_api.get_random()` 获取表情。
    3.  调用 `llm_api` 分析情感。
    4.  调用 `send_api` 发送图片。
*   **隔离风险**:
    *   **全局资源池**: `emoji_api` 从全局目录读取表情。所有租户共享同一套表情库。无法实现“租户A有独占的二次元表情包，租户B有独占的商务表情包”。
    *   **全局模型配置**: `llm_api` 使用全局 `model_config`。所有租户使用相同的 LLM 模型和 Key，无法分账或隔离配额。
    *   **Prompt 注入/泄露**: 若 `Action` 中包含 System Prompt，该 Prompt 是硬编码在代码中的，所有租户一致。

---

## 3. 核心风险点总结

| 风险维度     | 问题描述                                                                     | 影响等级 |
| :----------- | :--------------------------------------------------------------------------- | :------- |
| **状态隔离** | 插件通过类变量或全局模块变量存储状态，导致跨租户数据串扰。                   | **高**   |
| **配置隔离** | 插件读取 `config.toml` 或 `global_config`，无法针对租户进行差异化配置。      | **高**   |
| **资源隔离** | 插件访问文件系统（如表情包、图片）时未通过租户虚拟路径，导致资源共享或覆盖。 | **中**   |
| **执行隔离** | 管理类命令（如卸载插件）直接作用于全局进程，导致单点故障扩散至所有租户。     | **极高** |
| **API 鉴权** | 插件调用系统 API 时，系统未校验 `context.tenant_id` 与目标资源的归属关系。   | **极高** |

## 4. 改进建议

1.  **插件实例化**: 插件不应是单例。每当为一个 Tenant 启用插件时，应创建一个新的 Plugin Instance，并注入该 Tenant 的 Context 和 Config。
2.  **API 代理**: 插件不应直接 import `apis` 模块。应由宿主环境传递一个 `HostAPI` 对象给插件，该对象自动绑定了当前的 Tenant Context，确保插件只能访问自己租户的数据。
3.  **资源沙盒**: 插件文件读写应限制在 `data/tenants/<id>/plugins/<name>/` 目录下。
4.  **管理权限分离**: `plugin_management` 只能管理**当前租户**的插件订阅状态，而非系统级的代码加载状态。
