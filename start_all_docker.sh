#!/bin/bash

# 启动 MaimConfig (Port 8000)
echo "Starting MaimConfig..."
cd /workspace/MaimConfig
mkdir -p /workspace/data/shared  # Shared DB directory
# 设置环境变量: 指向共享数据库
export MAIMCONFIG_DB_PATH=${MAIMCONFIG_DB_PATH:-"/workspace/data/shared/MaiBot.db"}
# Explicitly set DATABASE_URL for MaimConfig ensuring it is a valid URI (4 slashes for absolute path)
export DATABASE_URL="sqlite+aiosqlite:///${MAIMCONFIG_DB_PATH}"
export MAIMCONFIG_URL="http://127.0.0.1:8000"
# 确保数据库存在，或者让其自动创建
python main.py &

# 启动 MaimWebBackend (Port 8880)
echo "Starting MaimWebBackend..."
cd /workspace/MaimWebBackend
mkdir -p /workspace/data/web  # Specific subdir for Web Backend
# 需要设置正确的 DATABASE_URL 等环境变量
# 注意：使用特定子目录，与 Bot/Config 分开
export DATABASE_URL="sqlite+aiosqlite:////workspace/data/web/maim_web.db"

# 初始化数据库 (Create Tables)
echo "Initializing Backend Database..."
echo "--- DEBUG INFO ---"
python3 -c "import maim_db; print(f'maim_db path: {maim_db.__file__}'); import os; print(f'maim_db dir contents: {os.listdir(os.path.dirname(maim_db.__file__))}')"
echo "Checking maimconfig_models contents:"
ls -R $(python3 -c "import maim_db, os; print(os.path.join(os.path.dirname(maim_db.__file__), 'maimconfig_models'))")
echo "--- END DEBUG ---"
cat <<EOF > /workspace/init_db.py
import asyncio
import os
import sys
import importlib.util

# Ensure environment variable is set for the script context as well
os.environ["DATABASE_URL"] = "${DATABASE_URL}"

print(f"DEBUG: sys.path: {sys.path}", flush=True)

try:
    import maim_db
    print(f"DEBUG: maim_db imported from {maim_db.__file__}", flush=True)
    
    # Try finding spec for subpackage
    spec = importlib.util.find_spec("maim_db.maimconfig_models")
    print(f"DEBUG: find_spec('maim_db.maimconfig_models'): {spec}", flush=True)

    # Try explicit import
    import maim_db.maimconfig_models.models as models
    print(f"DEBUG: successfully imported models from {models.__file__}", flush=True)
    create_tables = models.create_tables
except ImportError as e:
    print(f"CRITICAL ERROR importing maim_db models: {e}", flush=True)
    # List directory of maim_db again just to be sure
    if 'maim_db' in locals():
        print(f"maim_db dir: {os.listdir(os.path.dirname(maim_db.__file__))}", flush=True)
        pkg_path = os.path.join(os.path.dirname(maim_db.__file__), 'maimconfig_models')
        if os.path.exists(pkg_path):
             print(f"maimconfig_models dir content: {os.listdir(pkg_path)}", flush=True)
    raise

async def main():
    print("Creating tables...", flush=True)
    await create_tables()
    print("Tables created.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
EOF
python /workspace/init_db.py

python -m uvicorn src.main:app --host 0.0.0.0 --port 8880 &

# 启动 MaiMBot
echo "Starting MaiMBot..."
cd /workspace/MaiMBot
mkdir -p config
if [ ! -f config/bot_config.toml ]; then
    echo "Copying default bot config..."
    cp template/bot_config_template.toml config/bot_config.toml
fi
# 使用环境变量指定数据库路径 (适配 env_loader.py)
# 使用环境变量指定数据库路径 (适配 env_loader.py)
# 指向与 MaimConfig 相同的共享数据库
export DATABASE_URL="sqlite:////workspace/data/shared/MaiBot.db"

# MaiMBot Message Config (From .env migration)
export MAIM_MESSAGE_HOST="127.0.0.1"
export MAIM_MESSAGE_PORT="8090"
export MAIM_MESSAGE_MODE="ws"
export MAIM_MESSAGE_USE_WSS="false"

# 如果配置文件不存在，跳过 MaiMBot 启动
if [ -f "config/bot_config.toml" ]; then
    python bot.py &
else
    echo "MaiMBot config not found, skipping MaiMBot startup"
fi

# 启动 MaimWeb (Frontend) - 开发模式或预览模式
echo "Starting MaimWeb..."
cd /workspace/MaimWeb
# 使用 host 0.0.0.0 暴露给外部
npm run dev -- --host 0.0.0.0 &

# 保持容器运行
wait
