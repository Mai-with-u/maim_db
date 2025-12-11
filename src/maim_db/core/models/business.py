"""
数据面模型定义
包含 ChatHistory, Logs 等业务级数据模型，包含 agent_id 字段用于多租户隔离
"""
import uuid
from datetime import datetime

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    FloatField,
    IntegerField,
    Model,
    TextField,
    UUIDField,
)

from ..context_manager import get_current_agent_id
from ..database import get_database


class BusinessBaseModel(Model):
    """业务模型基类，强制要求 agent_id"""

    # 强制要求的多租户字段
    agent_id = CharField(max_length=255, index=True, null=False)

    class Meta:
        database = get_database()

    def save(self, *args, **kwargs):
        """写入拦截，自动填入 agent_id"""
        # 如果没有设置 agent_id，尝试从上下文自动获取
        if not hasattr(self, 'agent_id') or not self.agent_id:
            current_id = get_current_agent_id()
            if current_id:
                self.agent_id = current_id
            else:
                raise ValueError("业务模型必须设置 agent_id")
        return super().save(*args, **kwargs)

    @classmethod
    def select(cls, *fields):
        """查询拦截，自动添加 agent_id 过滤"""
        query = super().select(*fields)

        # 自动追加 WHERE agent_id = current_agent_id
        current_id = get_current_agent_id()
        if current_id and hasattr(cls, 'agent_id'):
            query = query.where(cls.agent_id == current_id)

        return query

    @classmethod
    def create(cls, **query):
        """拦截 create 方法，自动设置 agent_id"""
        current_id = get_current_agent_id()
        if current_id and 'agent_id' not in query:
            query['agent_id'] = current_id
        elif not current_id and 'agent_id' not in query:
            raise ValueError("业务模型创建时必须设置 agent_id")
        return super().create(**query)


class ChatHistory(BusinessBaseModel):
    """聊天历史记录模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    session_id = CharField(max_length=255, index=True)  # 会话ID
    user_message = TextField()
    assistant_message = TextField()
    user_id = CharField(max_length=255, index=True)  # 用户ID（外部系统）
    message_type = CharField(max_length=50, default='text')  # text, image, audio, etc.
    metadata = TextField(null=True)  # JSON 格式的额外信息
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'chat_history'
        database = get_database()
        indexes = (
            (('agent_id', 'session_id'), True),  # agent + session 复合索引
            (('agent_id', 'created_at'), False),  # agent + 时间索引，用于分页
        )


class ChatLogs(BusinessBaseModel):
    """聊天日志模型，用于审计和分析"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    session_id = CharField(max_length=255, index=True)
    request_type = CharField(max_length=50)  # chat, completion, embedding etc.
    request_content = TextField()
    response_content = TextField(null=True)
    status_code = IntegerField()  # HTTP状态码或业务状态码
    error_message = TextField(null=True)
    token_count = IntegerField(null=True)  # 消耗的token数量
    response_time = FloatField(null=True)  # 响应时间（秒）
    user_id = CharField(max_length=255, index=True)
    metadata = TextField(null=True)  # JSON 格式的额外信息
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'chat_logs'
        database = get_database()
        indexes = (
            (('agent_id', 'session_id'), True),
            (('agent_id', 'created_at'), False),
            (('agent_id', 'status_code'), False),
        )


class FileUpload(BusinessBaseModel):
    """文件上传记录模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    original_filename = CharField(max_length=255)
    stored_filename = CharField(max_length=255)
    file_path = CharField(max_length=500)
    file_size = IntegerField()
    mime_type = CharField(max_length=100)
    file_hash = CharField(max_length=64, index=True)  # SHA256哈希
    is_public = BooleanField(default=False)
    download_url = CharField(max_length=500, null=True)
    expires_at = DateTimeField(null=True)
    user_id = CharField(max_length=255, index=True)
    metadata = TextField(null=True)  # JSON 格式的额外信息
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'file_uploads'
        database = get_database()
        indexes = (
            (('agent_id', 'file_hash'), True),  # agent + 去重索引
            (('agent_id', 'user_id'), False),
        )


class UserSession(BusinessBaseModel):
    """用户会话模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    session_id = CharField(max_length=255, unique=True, index=True)
    user_id = CharField(max_length=255, index=True)
    is_active = BooleanField(default=True)
    last_activity = DateTimeField(default=datetime.utcnow)
    metadata = TextField(null=True)  # JSON 格式的会话信息
    created_at = DateTimeField(default=datetime.utcnow)
    expires_at = DateTimeField(null=True)

    class Meta:
        table_name = 'user_sessions'
        database = get_database()
        indexes = (
            (('agent_id', 'session_id'), True),
            (('agent_id', 'user_id'), False),
        )


class SystemMetrics(BusinessBaseModel):
    """系统指标模型"""

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    metric_name = CharField(max_length=100, index=True)
    metric_value = FloatField()
    metric_unit = CharField(max_length=20, null=True)  # count, bytes, seconds, percent
    tags = TextField(null=True)  # JSON 格式的标签
    created_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = 'system_metrics'
        database = get_database()
        indexes = (
            (('agent_id', 'metric_name', 'created_at'), True),
            (('agent_id', 'created_at'), False),
        )
