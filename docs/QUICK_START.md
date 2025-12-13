# MaiMBot数据库管理系统 - 快速开始

## 🚀 一键启动

### 方法1: 使用Python脚本
```bash
# 自动启动（PostgreSQL优先，SQLite回退）
python start_db.py

# 强制使用SQLite模式
python start_db.py --sqlite-only

# 仅查看数据库状态
python start_db.py --info-only

# 创建配置文件
python start_db.py --create-env
```

### 方法2: 使用Shell脚本
```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

## 📊 当前状态

✅ **SQLite模式**: 默认回退模式，零配置
✅ **PostgreSQL模式**: 容器化，支持多租户SaaS
✅ **自动切换**: 根据环境自动选择最适合的数据库
✅ **统一管理**: 所有数据库操作通过maim_db统一管理

## 🔧 配置选项

### 环境变量配置
```bash
# PostgreSQL配置（启用SaaS模式）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_saas
DB_USER=postgres
DB_PASSWORD=maimbot_2024
```

### 一键创建配置
```bash
python start_db.py --create-env
# 会生成 .env 文件，可根据需要修改
```

## 🎯 验证功能

### 1. 检查数据库状态
```bash
python db_manager.py status
```

### 2. 测试SQLite模式
```bash
python start_db.py --sqlite-only
```

### 3. 测试PostgreSQL模式（需要Docker）
```bash
# 配置环境变量后
python start_db.py
```

## 🔍 管理命令

```bash
# 数据库管理器
python db_manager.py --help

# 常用命令
python db_manager.py status    # 查看状态
python db_manager.py start      # 启动PostgreSQL
python db_manager.py stop       # 停止PostgreSQL
python db_manager.py init       # 初始化表结构
python db_manager.py backup     # 备份数据库
python db_manager.py restore    # 恢复数据库
```

## 📁 文件结构

```
maim_db/
├── db_manager.py          # 数据库管理器
├── start_db.py            # 一键启动脚本
├── start.sh               # Linux/macOS启动脚本
├── start.bat              # Windows启动脚本
├── .env.example           # 配置示例
├── README_DB.md           # 详细文档
├── QUICK_START.md         # 快速开始（本文件）
├── data/                  # 数据目录
│   └── MaiBot.db         # SQLite数据库
└── src/                   # 核心库代码
    └── core/              # 数据库模型和配置
```

## 🎉 成功标志

如果看到以下输出，说明系统已成功配置：

```
🎉 SQLite模式测试完全成功！
✅ SQLite数据库连接成功
✅ SQLite表结构创建成功
✅ 创建的表: 9个
   - agents
   - api_keys
   - chat_history
   - chat_logs
   - file_uploads
   - system_metrics
   - tenants
   - user_sessions
   - users
```

## 🔄 与MaiMBot集成

MaiMBot会自动检测并使用maim_db管理的数据库：

1. **自动连接**: 启动时自动连接到正确的数据库
2. **模式切换**: PostgreSQL可用时自动启用SaaS模式
3. **数据隔离**: 业务模型自动支持多租户数据隔离
4. **无缝切换**: 业务代码无需修改

## 💡 使用提示

- **开发环境**: 使用SQLite模式（零配置）
- **生产环境**: 使用PostgreSQL模式（完整多租户支持）
- **测试环境**: 可以随时切换模式进行测试
- **数据安全**: 支持备份和恢复功能

---

**MaiMBot数据库管理系统已就绪！** 🎉