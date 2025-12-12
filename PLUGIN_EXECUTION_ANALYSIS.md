# Plugin Execution & Tenant Isolation Analysis

## 1. Overview
This document analyzes the execution path of plugins (Commands, Actions, Event Handlers) in MaiMBot's multi-tenant architecture. The goal is to determine if plugin code is consistently executed within a `TenantContext`, ensuring isolation of state and resources.

## 2. Execution Entry Points

### 2.1. API Gateway (WebSocket Server)
- **Path:** `src/common/message/api.py` -> `message_handler`
- **Mechanism:**
  1. `message_handler` extracts API Key from metadata.
  2. Calls `parse_api_key` to resolve `tenant_id` and `agent_id`.
  3. Enters `async with tenant_context_async(tenant_id, agent_id):`.
  4. Calls `ChatBot.message_process`.
- **Status:** **SECURE**. Messages arriving via the standard API are properly wrapped in a tenant context.

### 2.2. WebUI (Local Chat)
- **Path:** `src/webui/chat_routes.py` -> `websocket_chat`
- **Mechanism:**
  1. Receives message from WebSocket.
  2. Constructs `message_data`.
  3. Calls `await chat_bot.message_process(message_data)` **DIRECTLY**.
- **Status:** **BROKEN / INSECURE**.
  - No `TenantContext` is established.
  - `ChatBot.message_process` eventually calls `get_chat_manager().get_or_create_stream()`.
  - `ChatManager` attempts to generate `stream_id` using `get_current_tenant_id()`.
  - **Outcome:** `RuntimeError: chat_id 生成需要有效的租户和代理上下文`. The WebUI chat will crash in multi-tenant mode.

### 2.3. System Startup (ON_START)
- **Path:** `src/main.py` -> `MainSystem._init_components`
- **Mechanism:**
  1. Calls `await events_manager.handle_mai_events(event_type=EventType.ON_START)`.
- **Status:** **GLOBAL / INSECURE**.
  - `ON_START` events run in the global application context (no tenant).
  - Plugins initializing state here (e.g., creating global variables, opening files) will do so globally.
  - **Risk:** Setup logic intended for a specific tenant will be applied globally or fail.

## 3. Propagation to Plugins

### 3.1. Commands and Event Handlers
- **Flow:** `ChatBot.message_process` -> `Command.execute()` / `EventHandler.execute()`
- **Context:**
  - Since `message_process` runs in `TenantContext` (via API path), the `await` calls and `asyncio.create_task` calls propagate this context.
  - `Command.execute()` is awaited: **Inherits Context**.
  - `EventHandler.execute()` is spawned as task: **Inherits Context** (Python 3.7+ feature).
- **Conclusion:** If the entry point is wrapped, these components are wrapped.

### 3.2. Actions (Heartflow / Planner)
- **Flow:** `HeartFChatting._main_chat_loop` -> `_loopbody` -> `ActionPlanner.plan` -> `Action.execute`
- **Context:**
  - `_main_chat_loop` is an infinite background task spawned during `HeartFChatting` initialization (`start()`).
  - Initialization usually happens on first message receipt (`get_or_create_heartflow_chat`).
  - **Scenario A (Correct):** First message comes via API. `TenantContext` is active. `_main_chat_loop` task is created inheriting this context. All subsequent `Action` executions in this loop inherit the context.
  - **Scenario B (Broken):** First message comes via WebUI. Crash occurs before loop start.
  - **Risk:** If a "System" message or some other non-API trigger starts a chat *without* context, the loop will run context-less forever.

## 4. Critical Gaps & Recommendations

### 4.1. Fix WebUI Context
- **Issue:** WebUI bypasses `tenant_context`.
- **Fix:** In `src/webui/chat_routes.py`, `websocket_chat` must determine which tenant/agent the WebUI session represents (currently it seems to assume a "local" or "admin" mode).
- **Proposals:**
  1. **Implicit Local Tenant:** Wrap WebUI calls in a special "local" or "admin" tenant context.
  2. **User Selection:** WebUI must allow selecting a tenant context if acting as an admin debugging a specific tenant.

### 4.2. Secure ON_START
- **Issue:** `ON_START` is global.
- **Fix:** Deprecate `ON_START` for tenant-specific logic. Introduce `ON_TENANT_LOAD` or similar event.
- **Mitigation:** Ensure `ON_START` handlers only do truly global init (e.g., registering classes), and do *not* touch resources or config.

### 4.3. Hardened ChatManager
- **Issue:** `ChatManager` enforces context for ID generation, causing crashes if context is missing.
- **Fix:** This is actually **GOOD**. It acts as a safety gate. We should verify all entry points (like Timers, Background Tasks) ensure they set context before touching ChatManager.

### 4.4. Plugin API Isolation
- **Issue:** Even with `TenantContext` active, many Plugin APIs (analyzed in `PLUGIN_API_ANALYSIS.md`) do not *read* this context. They just use global `streams` or `config`.
- **Fix:** Refactor `src.plugin_system.apis` to:
  1. Retrieve `current_tenant_id()` from context.
  2. Filter global dictionaries/DB queries using this ID.
  3. Raise error if accessed without context.

## 5. Next Steps
1. **Refactor WebUI:** Wrap `message_process` calls in `chat_routes.py` with a default/admin tenant context.
2. **Refactor APIs:** Modify `ChatManager` and key APIs (`chat_api`, `config_api`) to be context-aware (read `contextvar` instead of global only).
