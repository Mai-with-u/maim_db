# 🧪 maim_db 集成测试指南

本文档介绍了如何运行 `maim_db`、`MaimConfig` 和 `MaiMBot` 的联合集成测试。

## 1. 测试环境准备

### 1.1 依赖环境
确保已激活 `maibot` conda 环境：
```bash
conda activate maibot
```

### 1.2 端口清理
在启动服务前，建议先清理相关端口 (8000, 8081, 18040) 以避免冲突。
`maim_db` 根目录下提供了清理脚本：

```bash
python clean_ports.py
```

## 2. 启动服务

集成测试需要 `MaimConfig` (API服务) 和 `MaiMBot` (Bot服务) 同时运行。

### 2.1 启动 MaimConfig API
在 `/home/tcmofashi/proj/MaimConfig` 目录下运行：
```bash
# 进入目录
cd /home/tcmofashi/proj/MaimConfig

# 启动 (后台运行范例)
python main.py > api_server.log 2>&1 &
```
*   **端口**: 8000
*   **日志**: 查看 `api_server.log` 确认 "Application startup complete"

### 2.2 启动 MaiMBot
在 `/home/tcmofashi/proj/MaiMBot` 目录下运行：
```bash
# 进入目录
cd /home/tcmofashi/proj/MaiMBot

# 设置端口并启动
export PORT=8081
export MAIM_MESSAGE_PORT=18040
python -u bot.py > bot_server.log 2>&1 &
```
*   **HTTP端口**: 8081
*   **WebSocket端口**: 18040
*   **日志**: 查看 `bot_server.log`

## 3. 运行集成测试

测试脚本位于 `/home/tcmofashi/proj/maim_db/test/test_integration_maimconfig_maimbot.py`。

### 3.1 运行命令
需要设置 `PYTHONPATH` 以包含 `maim_db` 和 `MaimConfig` 的路径，并指定服务 URL。

```bash
# 设置环境变量 (根据实际路径调整)
export PYTHONPATH=$PYTHONPATH:/home/tcmofashi/proj/maim_db/test:/home/tcmofashi/proj/MaimConfig
export MAIMCONFIG_API_URL="http://127.0.0.1:8000/api/v2"
export MAIM_MESSAGE_WS_URL="ws://127.0.0.1:18040/ws"

# 运行测试
python /home/tcmofashi/proj/maim_db/test/test_integration_maimconfig_maimbot.py
```

### 3.2 一键运行 (参考)
可以将上述命令合并为一行运行：
```bash
env PYTHONPATH=$PYTHONPATH:/home/tcmofashi/proj/maim_db/test:/home/tcmofashi/proj/MaimConfig \
MAIMCONFIG_API_URL="http://127.0.0.1:8000/api/v2" \
MAIM_MESSAGE_WS_URL="ws://127.0.0.1:18040/ws" \
python /home/tcmofashi/proj/maim_db/test/test_integration_maimconfig_maimbot.py
```

## 4. 常见问题排查

*   **ConnectionRefusedError**: 
    *   检查 MaimConfig (8000) 或 MaiMBot (18040) 是否已启动。
    *   检查端口是否被占用 (使用 `clean_ports.py`)。
*   **Attribute %s missing**: 
    *   这是配置合并的已知 Bug，已在最新版代码 (ConfigMerger v26) 中修复。如果出现，请检查 `src/common/message/config_merger.py` 是否包含最新的 `_sanitize_recursive_copy` 和 `_apply_overrides_recursive` 修复。
*   **测试卡住**:
    *   测试脚本设置了 60秒 超时。如果卡住，可能是 Bot 响应慢或死锁。检查 Bot 日志。
