# SaaS Plugin System Refactoring: Factory Pattern & Isolation Design

## 1. Overview
This document details the design for refactoring the MaiMBot plugin system into a **SaaS-compliant Factory Pattern**.
The core goal is to enable per-tenant plugin activation, configuration, and execution isolation.

## 2. Core Concepts

### 2.1. Factory Pattern & Lifecycle
Instead of loading plugins as global singletons, the system will treat `Plugin` classes as **Factories**.

- **Registration Phase (Startup)**:
  - `PluginManager` scans directories.
  - Registers `Plugin` **Classes** (not instances) and their metadata (Manifest).
  - Registers Component **Classes** (Command, Action, etc.) into `ComponentRegistry`.

- **Execution Phase (Per Request)**:
  1. **Context**: Message arrives -> `TenantContext` is established.
  2. **Activation Check**: System retrieves "Enabled Plugins List" for the current `(tenant_id, agent_id)`.
  3. **Configuration**: System fetches plugin configuration for the current tenant.
  4. **Instantiation**:
     - The `Plugin` class is instantiated: `plugin = PluginClass(context, config)`.
     - `plugin.setup()` is called.
  5. **Component Execution**:
     - Appropriate component (Command/Action) is instantiated, receiving the `plugin` instance or its config.
     - `component.execute()`.
  6. **Destruction**:
     - `plugin.teardown()` is called.
     - Instance is discarded.

### 2.2. Isolation Analysis

To answer the specific request: *"Analyze the isolation needed in this process"*:

#### A. State Isolation
- **Requirement**: Execution A (Tenant 1) must not affect Execution B (Tenant 2).
- **Solution**:
  - **Instance State**: Since `Plugin` and `Component` instances are created fresh per request, `self.variable` is strictly local to the request.
  - **Class/Global State**: Developers must be forbidden from using module-level global variables or Class attributes (`MyPlugin.shared_data`) for mutable state.
    - *Enforcement*: Review guidelines; potentially use static analysis tools.

#### B. Configuration Isolation
- **Requirement**: Tenant 1 configures "Frequency=10", Tenant 2 configures "Frequency=5".
- **Solution**:
  - Configuration is stored in `MaimConfig` (Database/Service), keyed by `(tenant_id, plugin_name)`.
  - At instantiation, `PluginClass` receives **only** the dict corresponding to the active tenant.
  - The Plugin instance does not know about other tenants' configs.

#### C. Resource Isolation (Files & DB)
- **Requirement**: Plugins writing files must not overwrite other tenants' data.
- **Solution**:
  - **File System**: Plugin must use `context.get_data_dir(plugin_name)` provided by the framework, which resolves to `data/tenants/{tenant_id}/plugins/{plugin_name}/`.
  - **Database**: All ORM queries in plugins must automatically or explicitly include `.where(TenantID == context.tenant_id)`.

#### D. Dependency Isolation
- **Requirement**: If Plugin A depends on Plugin B, both must be enabled for the tenant.
- **Solution**: `PluginManager`'s resolution logic during "Activation Check" must verify consistency. If A is enabled but B is not, A fails to load (or B is auto-loaded).

## 3. Implementation Details

### 3.1. `PluginBase` Restructuring
```python
class PluginBase(ABC):
    def __init__(self, context: TenantContext, config: Dict[str, Any]):
        self.context = context
        self.config = config
        self.storage_path = context.get_plugin_storage_path(self.plugin_name)

    def setup(self):
        """Request-level initialization"""
        pass

    def teardown(self):
        """Request-level cleanup"""
        pass
```

### 3.2. `PluginManager` Changes
- Remove `load_all_plugins` (global instantiation).
- Add `get_plugin_class(name) -> Type[PluginBase]`.
- Add `register_plugin_class(cls)`.

### 3.3. `ChatBot` Workflow (`_process_commands`)
```python
# 1. Resolve Command Class
command_class, ..., info = registry.find_command_by_text(text)
plugin_name = info.plugin_name

# 2. Check Activation
active_plugins = config_service.get_active_plugins(current_tenant_id)
if plugin_name not in active_plugins:
    return  # Command unknown/disabled for this tenant

# 3. Instantiate Plugin
plugin_cls = manager.get_plugin_class(plugin_name)
plugin_config = config_service.get_plugin_config(current_tenant_id, plugin_name)
plugin_instance = plugin_cls(context, plugin_config)

try:
    plugin_instance.setup()
    
    # 4. Execute Command
    command = command_class(message, plugin_instance) # Pass plugin instance
    await command.execute()

finally:
    # 5. Cleanup
    plugin_instance.teardown()
```

## 4. Migration Strategy
1.  **Refactor Base**: Update `PluginBase` signature.
2.  **Update Built-ins**: Modify built-in plugins to accept new `__init__`.
3.  **Refactor Manager**: Change loading logic.
4.  **Refactor Bot**: Implement the lifecycle loop in `bot.py`.
