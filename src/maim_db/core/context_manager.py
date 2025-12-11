"""
上下文管理模块
负责多租户环境下的 agent_id 管理和上下文传递
"""
import threading
from contextlib import contextmanager
from typing import Optional


class AgentContext:
    """Agent上下文管理器"""

    def __init__(self):
        # 使用线程本地存储来保存当前线程的 agent_id
        self._local = threading.local()

    def set_current_agent_id(self, agent_id: str):
        """设置当前线程的 agent_id"""
        self._local.agent_id = agent_id

    def get_current_agent_id(self) -> Optional[str]:
        """获取当前线程的 agent_id"""
        return getattr(self._local, 'agent_id', None)

    def clear_current_agent_id(self):
        """清除当前线程的 agent_id"""
        if hasattr(self._local, 'agent_id'):
            delattr(self._local, 'agent_id')

    @contextmanager
    def agent_context(self, agent_id: str):
        """Agent上下文管理器，用于临时设置 agent_id"""
        old_agent_id = self.get_current_agent_id()
        try:
            self.set_current_agent_id(agent_id)
            yield
        finally:
            if old_agent_id is not None:
                self.set_current_agent_id(old_agent_id)
            else:
                self.clear_current_agent_id()


# 全局上下文管理器实例
agent_context = AgentContext()


def get_current_agent_id() -> Optional[str]:
    """获取当前 agent_id 的便捷函数"""
    return agent_context.get_current_agent_id()


def set_current_agent_id(agent_id: str):
    """设置当前 agent_id 的便捷函数"""
    agent_context.set_current_agent_id(agent_id)


def clear_current_agent_id():
    """清除当前 agent_id 的便捷函数"""
    agent_context.clear_current_agent_id()


def agent_context_manager(agent_id: str):
    """获取 agent 上下文管理器的便捷函数"""
    return agent_context.agent_context(agent_id)
