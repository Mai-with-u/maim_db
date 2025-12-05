# MaimDB SQLite默认启动指南

## 🚀 快速开始

MaimDB现在支持**开箱即用的SQLite**，无需任何配置即可启动！

### 默认行为

- **无需任何配置**：直接使用即可
- **自动创建数据库**：数据库文件位于 `data/MaiBot.db`
- **完整功能支持**：支持所有maim_db功能
- **零依赖启动**：不需要PostgreSQL或MySQL

## 📖 使用方法

### 1. 直接使用（推荐）

```python
from maim_db.src.core import get_database, init_database

# 获取数据库实例 - 自动使用SQLite
database = get_database()
print(f"数据库类型: {type(database).__name__}")  # SqliteDatabase

# 初始化连接
init_database()

# 使用数据库...
from maim_db.src.core.models import Tenant, Agent, ApiKey

# 创建租户
tenant = Tenant.create(
    id="tenant_demo",
    tenant_name="示例租户",
    tenant_type="personal"
)
```

### 2. 环境变量配置

虽然默认使用SQLite，但你仍然可以通过环境变量切换数据库：

```bash
# 使用PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"

# 使用MySQL
export DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/mydb"

# 明确指定SQLite
export DATABASE_URL="sqlite:///data/my_custom.db"
```

### 3. 配置文件

创建 `.env` 文件：

```env
# 默认SQLite（无需设置任何内容）
# DATABASE_URL=sqlite:///data/MaiBot.db

# 或者明确指定
# DATABASE_URL=postgresql://user:pass@localhost:5432/maimbot
# DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/maimbot
```

## 🔧 数据库文件位置

- **默认位置**：`data/MaiBot.db`
- **相对路径**：相对于项目根目录
- **自动创建**：如果目录不存在会自动创建
- **WAL模式**：启用WAL模式以提高并发性能

## 📊 特性支持

### ✅ 完全支持的功能

- 多租户模型（Tenant, Agent, ApiKey）
- 所有CRUD操作
- 关系查询
- 事务支持
- 索引优化
- 数据迁移

### 🔄 数据库切换

可以在不同数据库之间无缝切换：

```python
import os

# 切换到PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost:5432/db'
# 重新初始化即可切换
```

## 🧪 测试

运行SQLite启动测试：

```bash
# 完整测试
python scripts/test_sqlite_startup.py

# 简单测试
python scripts/simple_sqlite_test.py
```

## 🎯 优势

1. **零配置启动**：无需安装配置其他数据库
2. **开发友好**：本地开发无需数据库服务器
3. **快速原型**：快速验证想法和功能
4. **生产就绪**：支持升级到PostgreSQL/MySQL
5. **完全兼容**：与maimconfig完全集成

## 📝 配置示例

### 开发环境（默认SQLite）
```bash
# 无需任何配置，直接启动即可
python your_app.py
```

### 生产环境（PostgreSQL）
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/maimbot_prod"
python your_app.py
```

### 测试环境（MySQL）
```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/maimbot_test"
python your_app.py
```

## 🔍 故障排除

### 常见问题

1. **权限错误**：确保项目目录有写入权限
2. **文件不存在**：`data/` 目录会自动创建
3. **数据库锁定**：确保没有多个进程同时写入

### 调试信息

启用详细日志：

```python
from src.core import get_database
database = get_database()
# 会显示数据库类型和连接信息
```

## 📈 性能特性

- **WAL模式**：提高并发读写性能
- **连接池**：支持连接复用
- **事务支持**：完整的事务ACID特性
- **索引优化**：自动创建必要索引

---

🎉 **总结**：MaimDB现在真正实现了"开箱即用"，无需任何配置即可启动使用！