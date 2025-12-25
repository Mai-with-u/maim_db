#!/bin/bash

# 启动 MaimConfig (Port 8000)
echo "Starting MaimConfig..."
cd /workspace/MaimConfig
mkdir -p data  # Fix: Ensure data directory exists for sqlite
# 设置环境变量
export MAIMCONFIG_DB_PATH=${MAIMCONFIG_DB_PATH:-"/workspace/data/maimconfig.db"}
# 确保数据库存在，或者让其自动创建
python main.py &

# 启动 MaimWebBackend (Port 8880)
echo "Starting MaimWebBackend..."
cd /workspace/MaimWebBackend
# 需要设置正确的 DATABASE_URL 等环境变量，建议在运行时传入或在此处设置默认值
export DATABASE_URL=${DATABASE_URL:-"sqlite+aiosqlite:////workspace/data/maim_web.db"}
# 临时修复：确保数据目录存在
mkdir -p /workspace/data

# 初始化数据库 (Create Tables)
echo "Initializing Backend Database..."
cat <<EOF > /workspace/init_db.py
import asyncio
import os
# Ensure environment variable is set for the script context as well
os.environ["DATABASE_URL"] = "${DATABASE_URL}"
from maim_db.maimconfig_models.models import create_tables

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
mkdir -p data # Ensure data dir exists
mkdir -p config
if [ ! -f config/bot_config.toml ]; then
    echo "Copying default bot config..."
    cp template/bot_config_template.toml config/bot_config.toml
fi
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
