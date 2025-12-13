"""
maim_db - MaiM 数据平面与模型库

本库提供MaiM多租户SaaS的统一数据库架构，支持基于 agent_id 的数据隔离。
主要特性：
- 控制面与数据面分离
- 多租户数据隔离（基于 agent_id）
- ORM 基座替换支持
- 统一的数据库连接管理
"""

from .src import *

__version__ = "1.0.0"
__author__ = "MaiM Team"
__description__ = "maim_db - 多租户数据平面与数据库模型库"
