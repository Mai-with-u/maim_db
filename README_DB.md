# MaiMBot统一数据库管理系统

## 概述

MaiMBot统一数据库管理系统提供PostgreSQL和SQLite数据库的统一管理、启动、迁移和维护功能。支持一键启动，自动配置，无缝切换。

## 🚀 快速开始

### 一键启动数据库

```bash
# Linux/macOS
./start.sh

# Windows
start.bat

# 或使用Python直接启动
python start_db.py
```

### 环境配置

```bash
# 创建配置文件
python start_db.py --create-env

# 编辑配置文件
vim .env
```

## 📋 功能特性

### ✅ 自动检测和启动
- 自动检测Docker环境
- 优先启动PostgreSQL（支持多租户SaaS）
- 自动回退到SQLite（单用户模式）
- 一键初始化数据库表结构

### ✅ 统一管理
- 统一的数据库连接配置
- 自动环境变量管理
- 数据库状态监控
- 备份和恢复功能

### ✅ 容器化部署
- Docker Compose配置
- PostgreSQL容器化运行
- 数据持久化存储
- 健康检查机制

## 🔧 使用方法

### 命令行工具

#### 数据库管理器
```bash
python db_manager.py --help
```

**可用命令：**

```bash
# 查看数据库状态
python db_manager.py status

# 启动PostgreSQL数据库
python db_manager.py start
python db_manager.py start --port 5433 --password mypassword

# 停止数据库
python db_manager.py stop

# 重置数据库（删除所有数据）
python db_manager.py reset --confirm

# 初始化表结构
python db_manager.py init

# 备份数据库
python db_manager.py backup
python db_manager.py backup --path /path/to/backup

# 恢复数据库
python db_manager.py restore /path/to/backup/file
```

#### 一键启动脚本
```bash
# 自动启动（PostgreSQL优先）
python start_db.py

# 强制使用SQLite
python start_db.py --sqlite-only

# 仅显示状态
python start_db.py --info-only

# 创建配置文件
python start_db.py --create-env
```

### Shell脚本

#### Linux/macOS
```bash
# 基本启动
./start.sh

# 强制SQLite模式
./start.sh --sqlite-only

# 显示状态
./start.sh --info-only

# 创建配置文件
./start.sh --create-env

# 帮助信息
./start.sh --help
```

#### Windows
```cmd
# 基本启动
start.bat

# 强制SQLite模式
start.bat --sqlite-only

# 显示状态
start.bat --info-only

# 创建配置文件
start.bat --create-env
```

## 📊 数据库模式

### PostgreSQL模式（推荐）
- **用途**: 生产环境、多租户SaaS
- **特性**: 完整多租户支持、高并发、数据隔离
- **配置**: 通过环境变量或.env文件
- **启动**: 自动Docker容器化部署

### SQLite模式（默认）
- **用途**: 开发环境、单用户、快速测试
- **特性**: 零配置、文件数据库、本地运行
- **文件位置**: `data/MaiBot.db`
- **回退**: PostgreSQL不可用时自动使用

## 🔒 环境配置

### 环境变量
```bash
# PostgreSQL配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_saas
DB_USER=postgres
DB_PASSWORD=maimbot_2024

# 可选配置
DB_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=30
DB_TIMEZONE=UTC
```

### .env文件
```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
vim .env
```

## 📁 目录结构

```
maim_db/
├── db_manager.py          # 数据库管理器主程序
├── start_db.py            # 一键启动脚本
├── start.sh               # Linux/macOS启动脚本
├── start.bat              # Windows启动脚本
├── .env.example           # 环境变量示例
├── README_DB.md           # 数据库管理文档
├── config/                # 配置文件目录
│   ├── docker-compose.yml # Docker Compose配置
│   └── postgres.json       # PostgreSQL配置
├── scripts/               # 脚本目录
│   └── init-postgres.sql  # PostgreSQL初始化脚本
├── data/                  # 数据目录
│   └── MaiBot.db         # SQLite数据库文件
└── src/                   # 核心库代码
    └── core/              # 核心模块
```

## 🐳 Docker配置

### PostgreSQL容器
- **镜像**: postgres:15
- **容器名**: maimbot-postgres
- **数据卷**: maimbot_postgres_data
- **健康检查**: 自动检测数据库状态
- **性能优化**: 预配置的生产级参数

### Docker Compose配置
```yaml
services:
  postgres:
    image: postgres:15
    container_name: maimbot-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ai_saas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: maimbot_2024
    ports:
      - "5432:5432"
    volumes:
      - maimbot_postgres_data:/var/lib/postgresql/data
```

## 🔄 数据迁移

### SQLite到PostgreSQL
```bash
# 1. 启动PostgreSQL
python db_manager.py start

# 2. 备份SQLite数据
python db_manager.py backup

# 3. 恢复到PostgreSQL
python db_manager.py restore backup/sqlite/MaiBot.db
```

### PostgreSQL到SQLite
```bash
# 1. 备份PostgreSQL数据
python db_manager.py backup

# 2. 停止PostgreSQL
python db_manager.py stop

# 3. 恢复到SQLite（需要手动转换格式）
```

## 📈 监控和维护

### 状态监控
```bash
# 查看数据库状态
python db_manager.py status

# 输出示例
{
  "mode": "postgres",
  "status": "运行中",
  "type": "PostgreSQL",
  "host": "localhost",
  "port": "5432",
  "database": "ai_saas",
  "user": "postgres",
  "container_running": true
}
```

### 定期备份
```bash
# 创建定时备份任务
crontab -e

# 添加每日备份
0 2 * * * cd /path/to/maim_db && python db_manager.py backup
```

### 日志管理
```bash
# 查看PostgreSQL日志
docker logs maimbot-postgres

# 查看数据库管理日志
tail -f logs/db_manager.log
```

## 🛠️ 故障排除

### 常见问题

#### 1. PostgreSQL启动失败
```bash
# 检查Docker状态
docker --version
docker-compose --version

# 检查容器状态
docker ps -a | grep maimbot-postgres

# 查看容器日志
docker logs maimbot-postgres

# 重启容器
docker restart maimbot-postgres
```

#### 2. 端口冲突
```bash
# 使用不同端口
python db_manager.py start --port 5433

# 或杀死占用端口的进程
lsof -i :5432
kill -9 <PID>
```

#### 3. 权限问题
```bash
# 检查目录权限
ls -la data/

# 修复权限
chmod 755 data/
chmod 644 data/MaiBot.db
```

#### 4. 数据库连接失败
```bash
# 检查环境变量
env | grep DB_

# 测试连接
docker exec -it maimbot-postgres psql -U postgres -d ai_saas -c "SELECT 1"
```

### 调试模式
```bash
# 启用详细日志
export DB_DEBUG=1
python start_db.py

# 查看详细错误信息
python db_manager.py status
```

## 🔗 与MaiMBot集成

### 自动配置
MaiMBot启动时会自动检测数据库配置：

1. **环境变量优先**: 读取`.env`文件中的数据库配置
2. **PostgreSQL优先**: 如果PostgreSQL可用，自动使用SaaS模式
3. **SQLite回退**: 如果PostgreSQL不可用，自动使用SQLite模式
4. **无缝切换**: 业务代码无需修改，ORM基座自动适配

### 使用示例
```python
# 在MaiMBot中使用
from src.common.database.database_model import BaseModel, Messages

# 自动适配当前数据库模式
message = Messages.create(
    chat_id="test_chat",
    processed_text="Hello World"
)

# 如果是PostgreSQL模式，自动添加agent_id
# 如果是SQLite模式，正常工作
```

## 📞 支持

如有问题，请：
1. 查看本文档的故障排除部分
2. 检查GitHub Issues
3. 联系开发团队

---

**注意**: 本数据库管理系统是为MaiMBot多租户SaaS架构专门设计的，确保数据安全和隔离性。