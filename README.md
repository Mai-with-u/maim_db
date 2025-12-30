# maim_db — 多用户麦麦api后端核心

`maim_db` 是 MaiM 全栈的统一数据平面，提供 Peewee 模型、多租户（基于 agent_id）上下文隔离、连接管理与迁移入口。所有服务共享这里的模型与迁移，其他仓库只消费，不自建表。

## 🚀 极速一键启动 (Docker)

无需配置复杂的本地环境，使用我们的一键脚本启动包含所有服务（Config, Bot, Web, Backend）的开发环境：

```bash
# 1. 确保已安装 Docker
# 2. 运行交互式启动脚本
python scripts/run_docker_interactive.py
```

脚本会自动：
- 🐳 **启动所有服务**：在一个容器内同时运行 Bot, Config, Web前端, Web后端。
- 📂 **挂载配置**：自动挂载或生成本地配置文件（`config/*.toml`, `.env`），修改即时生效。
- 💾 **数据持久化**：挂载本地 `data/` 目录，数据库文件不随容器丢失。
- 🌐 **自动网络配置**：已预配置端口映射与 `0.0.0.0` 绑定，开箱即用。

**服务访问地址：**
- **WebUI (前端页面)**: [http://localhost:5173](http://localhost:5173)
- **MaimConfig (配置中心 API)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MaimWebBackend (后端 API)**: [http://localhost:8880/docs](http://localhost:8880/docs)
- **MaiMBot (WebSocket)**: `ws://localhost:8090/api/message/v1`

## 仓库关系与职责

- `maim_db`（本仓库）：模型与迁移的唯一来源，提供 `db_manager`、BaseModel 及上下文隔离工具。
- `MaimConfig`：控制面 API（FastAPI），负责创建/更新租户、Agent、密钥等，并写入 `maim_db`。
- `MaiMBot`：运行时，按 Agent 配置执行业务/插件，读写 `maim_db`（会话、日志、指标）。
- `maim_message`：消息网关（WS/HTTP），桥接客户端与运行时。
- `MaimWebBackend` / `MaimWeb`：后台与前端，从 `maim_db` 读取数据做可视化与管理。

## 工作流（api-server 版本）

1) 控制面：`MaimConfig` 提供 API，写入 `maim_db`（租户/Agent/密钥/策略/插件配置）。
2) 接入：客户端经 `maim_message` 建立连接，向 `MaiMBot` 投递消息。
3) 运行时：`MaiMBot` 读取 `maim_db` 中的 Agent 配置与插件 → 执行对话/插件 → 结果（会话、日志、指标）写回 `maim_db`。
4) 展示：`MaimWebBackend` 读取 `maim_db` 数据，前端呈现会话、日志、活跃度等。

## 快速开始（开发）

```bash
pip install -e .
```

然后参考 `docs/QUICK_START.md` 完成环境变量、数据库准备与建表。

## 核心能力

- 多租户隔离：上下文管理器自动注入/过滤 `agent_id`，读写安全隔离。
- 统一模型面：系统模型（租户/用户/Agent/API Key）与业务模型（会话、日志、上传等）。
- 可复用基座：业务模型继承 BaseModel 可直接获得隔离能力，便于改造遗留表。
- 迁移单一入口：所有表结构与迁移在此维护，服务共享同一契约。

## 文档导航（docs/）

- 模型参考：[docs/DATABASE_MODELS.md](docs/DATABASE_MODELS.md)
- **[推荐] 全栈开发与使用指南：[docs/full_stack_guide.md](docs/full_stack_guide.md)**
- Agent/ID 规则：[docs/AGENT_ID_GUIDE.md](docs/AGENT_ID_GUIDE.md)
- 多租户迁移方案：[docs/MULTI_TENANT_MIGRATION_STRATEGY.md](docs/MULTI_TENANT_MIGRATION_STRATEGY.md)
- 进度与验证：[docs/MULTI_TENANT_PROGRESS_2025-12-06.md](docs/MULTI_TENANT_PROGRESS_2025-12-06.md)、[docs/MULTI_TENANT_VERIFICATION_2025-12-06.md](docs/MULTI_TENANT_VERIFICATION_2025-12-06.md)
- 数据库操作：[docs/README_DB.md](docs/README_DB.md)、[docs/README_SQLITE.md](docs/README_SQLITE.md)
- 快速上手：[docs/QUICK_START.md](docs/QUICK_START.md)
- 测试指南：[docs/TEST_GUIDE.md](docs/TEST_GUIDE.md)
- 其他专题（插件、聊天流分析、重构记录、存储迁移等）：参见 [docs/](docs/) 目录全部文件。

## 协作与修改约定

- 仅在 `maim_db` 内新增/修改表与迁移；下游仓库通过包引用使用。
- 添加新业务表时，继承提供的 Business BaseModel，获得 agent 隔离。
- 控制面与运行时代码留在各自仓库，持久化与租户逻辑集中在此。

## 许可证

MIT License
