# **数据库架构与 SaaS 多租户迁移指南**

本文档描述了 AI SaaS 系统的数据库架构设计。核心目标是实现**控制面与数据面的分离**，并在**不修改单用户版本业务逻辑代码**的前提下，实现多租户数据隔离。

## **1\. 核心架构理念**

本系统采用 **"共享数据库 \+ 共享核心库"** 模式。

* **物理层**：所有服务连接同一个物理数据库（PostgreSQL/MySQL）。  
* **代码层**：通过一个统一的 Python 包 (ai\_project\_core) 定义所有数据模型。  
* **迁移策略**：对于遗留的单用户业务代码，采用 **"ORM 基座替换 (Infrastructure Replacement)"** 模式，通过替换基类定义实现多租户隔离。

## **2\. 统一 DB 核心库 (ai\_project\_core)**

所有新开发的微服务必须依赖此核心库，严禁在微服务内部单独定义数据模型。

### **2.1 目录结构**

ai\_project\_core/  
├── src/  
│   └── core/  
│       ├── database.py       \# 统一的 Peewee Database 实例配置  
│       ├── config.py         \# 环境变量读取 (DB\_HOST, PORT 等)  
│       └── models/  
│           ├── \_\_init\_\_.py  
│           ├── system.py     \# 控制面模型: User, Tenant, ApiKey, Agent  
│           └── business.py   \# 数据面模型: ChatHistory, Logs (包含 agent\_id)

### **2.2 职责范围**

1. **Single Source of Truth**：作为数据库表结构（Schema）的唯一真理来源。  
2. **Database Migrations**：数据库迁移脚本必须位于此库中，统一管理数据库版本变更。  
3. **Connection Pooling**：统一管理数据库连接池参数。

## **3\. 各模块与 DB 的关系**

| 模块 | 角色 | 访问方式 | 读写权限 | 数据隔离策略 |
| :---- | :---- | :---- | :---- | :---- |
| **Web 后端** | 控制面 | 引用 core.models | 读写 User/Tenant | 基于 API 鉴权，管理所有租户 |
| **配置后端** | 控制面 | 引用 core.models | 读写 Agent/Config/Key | 写入配置，生成 Key |
| **回复器 (新逻辑)** | 连接层 | 引用 core.models | 只读 AgentConfig | 通过 Key 提取 ID，读取特定配置 |
| **回复器 (旧逻辑)** | 业务层 | **ORM 替换层** | 读写 Chat/Log | **BaseModel 方法重写 (见下文)** |

## **4\. ORM 层替换设计指导 (Peewee 版)**

为了保留单用户版本的快速迭代能力，我们不修改其业务代码，而是替换其底层的 ORM 定义文件。

### **4.1 核心原理**

利用 Peewee 的 **基类继承** 和 **方法重写** 特性。

1. **文件替换**：在 SaaS 分支中，用 SaaS 版的 database\_model.py (包含修改过的 BaseModel) 覆盖旧项目的文件。  
2. **字段注入**：在 SaaS 版 BaseModel 中直接定义 agent\_id 字段。所有继承自它的业务模型（如 Messages）会自动获得该字段。  
3. **拦截代理**：  
   * **写入拦截**：重写 save() 方法，自动填入 agent\_id。  
   * **读取拦截**：重写 select() 方法，自动添加 .where(agent\_id=...)。

### **4.2 关键代码实现 (SaaS Replacement)**

在 SaaS 分支中，src/database\_model.py (或定义 BaseModel 的文件) 应被修改为：  
from peewee import Model, TextField  
from context\_manager import get\_current\_agent\_id  \# 假设的上下文管理模块

\# 1\. 定义 SaaS 专用的 BaseModel  
class BaseModel(Model):  
    \# 自动注入多租户字段  
    agent\_id \= TextField(index=True, null=True)

    class Meta:  
        \# 使用 SaaS 统一的数据库连接  
        database \= saas\_db\_instance 

    \# 2\. 写入拦截 (Write Proxy)  
    def save(self, \*args, \*\*kwargs):  
        \# 如果当前没有设置 agent\_id，尝试从上下文自动获取  
        if not hasattr(self, 'agent\_id') or not self.agent\_id:  
            current\_id \= get\_current\_agent\_id()  
            if current\_id:  
                self.agent\_id \= current\_id  
        return super().save(\*args, \*\*kwargs)

    \# 3\. 读取拦截 (Read Proxy)  
    @classmethod  
    def select(cls, \*fields):  
        query \= super().select(\*fields)  
          
        \# 仅当处于 SaaS 上下文且该模型有 agent\_id 字段时才过滤  
        current\_id \= get\_current\_agent\_id()  
        if current\_id and hasattr(cls, 'agent\_id'):  
            \# 自动追加 WHERE agent\_id \= '...'  
            query \= query.where(cls.agent\_id \== current\_id)  
              
        return query

    @classmethod  
    def create(cls, \*\*query):  
        \# 拦截 create 方法  
        current\_id \= get\_current\_agent\_id()  
        if current\_id and 'agent\_id' not in query:  
             query\['agent\_id'\] \= current\_id  
        return super().create(\*\*query)

### **4.3 Git 分支管理策略**

为了防止合并代码时覆盖 SaaS 特有的 ORM 文件，请配置 .gitattributes。

1. 在 SaaS 分支根目录创建 .gitattributes：  
   \# 保护定义 BaseModel 的文件不被覆盖  
   src/database\_model.py merge=ours

2. 启用 merge driver：  
   git config merge.ours.driver true

3. **效果**：当从 single-user-branch 合并代码到 saas-branch 时，Git 会自动忽略对 src/database\_model.py 的更改，始终保留 SaaS 版本的“魔法基类”。

## **5\. 开发与部署工作流**

### **5.1 数据库迁移 (Migrations)**

重要：严禁使用旧项目的迁移工具。  
所有数据库结构的变更（包括给旧表添加字段），都必须在 ai\_project\_core 项目中操作。

* 物理数据库表 **必须** 真实存在 agent\_id 列。  
* 虽然旧代码的 Messages 类定义里没有写 agent\_id，但因为它继承了 SaaS 版的 BaseModel，它在运行时会自动拥有这个字段。

### **5.2 新增业务表流程**

1. **单用户分支开发**：开发者在旧项目中添加 class Note(BaseModel): content=...。  
2. **SaaS 分支同步**：  
   * 将旧分支合并入 SaaS 分支。  
   * 在 ai\_project\_core 中创建迁移脚本，物理创建 notes 表并加上 agent\_id 列。  
3. **运行时**：  
   * SaaS 版启动。  
   * Note 类加载 \-\> 继承 SaaS 版 BaseModel \-\> 自动获得 agent\_id 属性。  
   * 用户保存 Note \-\> 触发重写后的 save() \-\> 自动写入 agent\_id。

## **6\. 总结架构图**

graph TD  
    subgraph "Infrastructure (ai\_project\_core)"  
        CoreModels\[核心模型定义\<br/\>System \+ Business Tables\]  
        CoreDB\[DB Connection\<br/\>& Config\]  
    end

    subgraph "SaaS Application"  
        subgraph "Control Plane"  
            WebBE\[Web后端\]  
            ConfigBE\[配置后端\]  
        end  
          
        subgraph "Data Plane (Responder)"  
            NewLogic\[新路由/鉴权逻辑\]  
              
            subgraph "Legacy Code Container"  
                LegacyLogic\[旧业务逻辑\]  
                MagicORM\[ORM 替换层\<br/\>(Peewee BaseModel)\]  
            end  
        end  
    end

    DB\[(PostgreSQL)\]

    %% 关系  
    WebBE \--\>|Import| CoreModels  
    ConfigBE \--\>|Import| CoreModels  
    NewLogic \--\>|Import| CoreModels  
      
    LegacyLogic \--\>|Inherits| MagicORM  
    MagicORM \-.-\>|Config Reference| CoreDB  
      
    %% 连接  
    WebBE \--\> DB  
    ConfigBE \--\> DB  
    MagicORM \--\>|Proxy Filter/Inject| DB  
