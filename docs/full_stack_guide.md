# MaiMBot 全栈开发与使用指南

本文档详细说明了 MaiMBot 多服务架构的开发环境搭建、配置管理及启动流程。

## 1. 架构概览

MaiMBot系统由以下五个核心仓库组成：

| 仓库名称           | 路径 (示例)               | 端口            | 说明                                                                      |
| :----------------- | :------------------------ | :-------------- | :------------------------------------------------------------------------ |
| **maim_db**        | `.../proj/maim_db`        | N/A             | **[核心]** 共享数据库模型、配置逻辑与公共库。所有服务均依赖此库。         |
| **MaiMBot**        | `.../proj/MaiMBot`        | 8081 / WS:18040 | **[核心]** AI 聊天机器人主服务，处理 WS 连接与消息分发。                  |
| **MaimConfig**     | `.../proj/MaimConfig`     | 8000            | **[配置]** 租户、Agent、API Key 管理的后端服务。                          |
| **MaimWebBackend** | `.../proj/MaimWebBackend` | 8880            | **[Web中间层]** 为前端提供接口，处理认证，并将配置请求转发给 MaimConfig。 |
| **MaimWeb**        | `.../proj/MaimWeb`        | 5173            | **[前端]** 基于 React/Vite 的可视化管理控制台。                           |

### 核心交互逻辑
1.  **数据库同步**：所有后端服务（MaiMBot, MaimConfig, MaimWebBackend）**必须连接同一个 SQLite 数据库文件**。
2.  **配置委托**：
    *   `MaimWebBackend` 处理用户登录/注册。
    *   `MaimWebBackend` 创建 Agent 时，会通过 HTTP 调用委托 `MaimConfig` 生成 API Key。
3.  **消息通信**：
    *   客户端（如 `test_api_client_connect.py`）使用生成的 API Key 连接 `MaiMBot` 的 WebSocket 端口。

---

## 2. 环境搭建

### 2.1 Python 环境 (Conda)
建议所有后端服务使用同一个 Conda 环境 (`maibot`)。

```bash
# 创建环境
conda create -n maibot python=3.12
conda activate maibot

# 安装依赖 (建议在各仓库根目录执行)
# 注意：首先必须安装 maim_db 库
cd ~/proj/maim_db
pip install -e .

# 然后安装各服务依赖
cd ~/proj/MaiMBot && pip install -r requirements.txt
cd ~/proj/MaimConfig && pip install -r requirements.txt
cd ~/proj/MaimWebBackend && pip install -r requirements.txt
```

### 2.2 Node.js 环境 (前端)
```bash
cd ~/proj/MaimWeb
npm install
```

---

## 3. 关键配置 (CRITICAL)

**系统正常运行的核心前提是所有服务共享同一个数据库。**

### 3.1 统一数据库路径
我们将数据库文件统一存放在 `maim_db` 仓库的 `data` 目录下：
*   **路径**: `/home/tcmofashi/proj/maim_db/data/MaiBot.db`

### 3.2 配置 .env 文件
请确保以下服务目录中均存在 `.env` 文件，并包含准确的 `DATABASE_URL`。

#### A. maim_db (作为源码库)
确保 `data/` 目录存在。库代码已打补丁，会自动优先使用环境变量，否则回退到 `src/data`。建议显式配置环境变量。

#### B. MaimConfig (`~/proj/MaimConfig/.env`)
```ini
# 使用异步驱动
DATABASE_URL=sqlite+aiosqlite:////home/tcmofashi/proj/maim_db/data/MaiBot.db
HOST=0.0.0.0
PORT=8000
```

#### C. MaimWebBackend (`~/proj/MaimWebBackend/.env`)
```ini
# 使用异步驱动
DATABASE_URL=sqlite+aiosqlite:////home/tcmofashi/proj/maim_db/data/MaiBot.db
PORT=8880
# 其他JWT密钥等配置...
```

#### D. MaiMBot (`~/proj/MaiMBot/.env`)
```ini
# 使用同步驱动 (Peewee) - 注意路径差异，MaiMBot可以使用同步URL
DATABASE_URL=sqlite:////home/tcmofashi/proj/maim_db/data/MaiBot.db
```

---

## 4. 启动流程

请按以下顺序启动服务，建议使用 4 个终端窗口。

### 终端 1: MaiMBot (机器人主服务)
```bash
cd ~/proj/MaiMBot
conda activate maibot
python bot.py
# 成功标志：Log显式 WebSocket server started on ...:18040
```

### 终端 2: MaimConfig (配置服务)
```bash
cd ~/proj/MaimConfig
conda activate maibot
python main.py
# 成功标志：Log显示 Uvicorn running on http://0.0.0.0:8000
```

### 终端 3: MaimWebBackend (Web 后端)
```bash
cd ~/proj/MaimWebBackend
conda activate maibot
./start_backend.sh
# 成功标志：Log显示 Uvicorn running on http://0.0.0.0:8880
```

### 终端 4: MaimWeb (前端)
```bash
cd ~/proj/MaimWeb
npm run dev
# 访问 http://localhost:5173
```

---

## 5. 开发指南

### 修改共享数据库模型
所有数据模型定义在 `maim_db/src/maim_db/maimconfig_models/models.py`。
*   **注意 ORM 兼容性**：系统同时使用了 `SQLAlchemy` (WebBackend) 和 `Peewee` (Config/Bot)。
*   **枚举处理**：请使用 `String` 类型存储枚举值，并在代码中进行校验，不要直接使用数据库层面的 Enum 类型，以避免大小写不一致导致的跨框架读取错误。
*   **时间戳**：WebBackend 使用 SQLAlchemy 写入时，需在代码中显式设置 `created_at` 和 `updated_at` (使用 `datetime.utcnow()`)，因为 SQLite 的 `server_default` 在某些异步驱动下可能不生效。

### 验证脚本
在 `MaimWebBackend` 目录下提供了验证脚本，用于测试全流程集成：
```bash
# 验证后端注册、Agent创建、Key生成全流程
python verify_backend_flow.py

# 验证生成的 Key 能否连接 Bot
python create_key.py  # 生成永久 Key
# 复制 Key 到 maim_message/others/test_api_client_connect.py
python ../maim_message/others/test_api_client_connect.py
```
