#!/bin/bash

# MaiMBot数据库启动脚本
# Linux/macOS可执行启动脚本

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "db_manager.py" ] || [ ! -f "start_db.py" ]; then
    echo "❌ 请在maim_db目录下运行此脚本"
    exit 1
fi

echo "🚀 MaiMBot数据库启动器"
echo "=================================="

# 解析命令行参数
FORCE_SQLITE=false
INFO_ONLY=false
CREATE_ENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --sqlite-only)
            FORCE_SQLITE=true
            shift
            ;;
        --info-only)
            INFO_ONLY=true
            shift
            ;;
        --create-env)
            CREATE_ENV=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --sqlite-only    强制使用SQLite模式"
            echo "  --info-only      仅显示数据库信息"
            echo "  --create-env     创建环境变量配置文件"
            echo "  -h, --help       显示帮助信息"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 构建Python命令参数
PYTHON_ARGS=""
if [ "$FORCE_SQLITE" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --sqlite-only"
fi

if [ "$INFO_ONLY" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --info-only"
fi

if [ "$CREATE_ENV" = true ]; then
    PYTHON_ARGS="$PYTHON_ARGS --create-env"
fi

# 执行Python启动脚本
if [ -n "$PYTHON_ARGS" ]; then
    python3 start_db.py $PYTHON_ARGS
else
    python3 start_db.py
fi