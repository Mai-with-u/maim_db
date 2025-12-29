#!/bin/bash

# 全局初始化：确保所有数据库表已创建 (Unified Init via Ad-Hoc Script)
echo "Initializing Databases (Ad-Hoc Mode)..."

# Create a temporary init script that uses the CONTAINER'S code
cat <<EOF > /workspace/ad_hoc_init.py
import sys
import os

# Add paths to find MaiMBot and maim_db
sys.path.append("/workspace/MaiMBot")
sys.path.append("/workspace/maim_db/src") # Just in case

try:
    from maim_db.core.database import db_manager
    # Try importing models from MaiMBot (where they currently live in the container image)
    from src.common.database.database_model import MODELS as MAIMBOT_MODELS
    
    # Try importing models from maim_db (V2 models)
    try:
        from maim_db.core.models import ALL_MODELS as MAIMDB_MODELS
    except ImportError:
        MAIMDB_MODELS = []
        
    ALL_MODELS = list(set(MAIMBOT_MODELS + MAIMDB_MODELS))
    
    print(f"Loaded {len(ALL_MODELS)} models.")
    
    db_manager.connect()
    db_manager.create_tables(ALL_MODELS)
    db_manager.close()
    print("Tables created successfully.")
    
except Exception as e:
    print(f"Init failed: {e}")
    import traceback
    traceback.print_exc()
    # Don't exit 1, try to proceed? 
    # No, strict failure is better to debug.
    sys.exit(1)
EOF

# 1. Initialize Shared DB (MaiBot.db)
echo "Step 1: Initializing Shared DB (MaiBot.db)..."
mkdir -p /workspace/data/shared
export DATABASE_URL="sqlite+aiosqlite:////workspace/data/shared/MaiBot.db"
# 设置 MaiMBot 需要的环境变量以正确加载模型
export SAAS_MODE="false" 
python3 /workspace/ad_hoc_init.py

# 2. Initialize Web DB (maim_web.db)
echo "Step 2: Initializing Web DB (maim_web.db)..."
mkdir -p /workspace/data/web
export DATABASE_URL="sqlite+aiosqlite:////workspace/data/web/maim_web.db"
python3 /workspace/ad_hoc_init.py

echo "Database Initialization Complete."

# 启动 MaimConfig (Port 8000)
echo "Starting MaimConfig..."
cd /workspace/MaimConfig
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

# 旧的初始化逻辑已移除，统一由顶部的 python3 -m maim_db.init_db 处理

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
# Removed hardcoded exports to allow .env loading or Docker -e flags

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
