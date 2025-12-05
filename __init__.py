"""
AI Project Core - 统一数据库核心库

本库提供了AI SaaS系统的统一数据库架构，支持多租户数据隔离。
主要特性：
- 控制面与数据面分离
- 多租户数据隔离（基于agent_id）
- ORM基座替换支持
- 统一的数据库连接管理
"""

from .src import *

__version__ = "1.0.0"
__author__ = "AI Project Team"
__description__ = "统一数据库核心库 - 支持多租户SaaS架构的数据模型和数据库管理"