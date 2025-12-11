"""
Agent配置模型
基于MaiMConfig的Agent配置字段完整说明和MaiMBot的config结构
使用关系模型替代JSON字段，提供结构化的配置管理
"""

import json
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
)

from ..database import get_database


class AgentConfigBaseModel(Model):
    """Agent配置基础模型"""
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        database = get_database()


class PersonalityConfig(AgentConfigBaseModel):
    """人格配置模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    # 核心人格字段
    personality = TextField(help_text="人格核心描述")
    reply_style = CharField(max_length=500, default="", help_text="回复风格")
    interest = CharField(max_length=500, default="", help_text="兴趣领域")
    plan_style = CharField(max_length=500, default="", help_text="群聊行为风格")
    private_plan_style = CharField(max_length=500, default="", help_text="私聊行为风格")
    visual_style = CharField(max_length=500, default="", help_text="视觉风格")

    # 状态系统字段
    states = TextField(default="[]", help_text="状态列表JSON数组")
    state_probability = FloatField(default=0.0, help_text="状态切换概率")

    class Meta:
        table_name = "personality_configs"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class BotConfigOverrides(AgentConfigBaseModel):
    """Bot基础配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    # 必需字段覆盖
    platform = CharField(max_length=50, default="", help_text="运行平台")
    qq_account = CharField(max_length=50, default="", help_text="QQ账号")
    nickname = CharField(max_length=100, default="", help_text="机器人昵称")

    # 扩展字段覆盖
    platforms = TextField(default="[]", help_text="其他支持平台JSON数组")
    alias_names = TextField(default="[]", help_text="别名列表JSON数组")

    class Meta:
        table_name = "bot_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class ChatConfigOverrides(AgentConfigBaseModel):
    """聊天配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    # 聊天配置字段
    max_context_size = IntegerField(default=18, help_text="上下文长度")
    interest_rate_mode = CharField(max_length=20, default="fast", help_text="兴趣计算模式")
    planner_size = FloatField(default=1.5, help_text="规划器大小")
    mentioned_bot_reply = BooleanField(default=True, help_text="提及回复")
    auto_chat_value = FloatField(default=1.0, help_text="主动聊天频率")
    enable_auto_chat_value_rules = BooleanField(default=True, help_text="动态聊天频率")
    at_bot_inevitable_reply = FloatField(default=1.0, help_text="@回复必然性")
    planner_smooth = FloatField(default=3.0, help_text="规划器平滑")
    talk_value = FloatField(default=1.0, help_text="思考频率")
    enable_talk_value_rules = BooleanField(default=True, help_text="动态思考频率")
    talk_value_rules = TextField(default="[]", help_text="思考频率规则JSON数组")
    auto_chat_value_rules = TextField(default="[]", help_text="聊天频率规则JSON数组")

    class Meta:
        table_name = "chat_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class ExpressionConfigOverrides(AgentConfigBaseModel):
    """表达配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    mode = CharField(max_length=20, default="classic", help_text="表达模式")
    learning_list = TextField(default="[]", help_text="表达学习配置JSON数组")
    expression_groups = TextField(default="[]", help_text="表达学习互通组JSON数组")

    class Meta:
        table_name = "expression_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class MemoryConfigOverrides(AgentConfigBaseModel):
    """记忆配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    max_memory_number = IntegerField(default=100, help_text="记忆最大数量")
    memory_build_frequency = IntegerField(default=1, help_text="记忆构建频率")

    class Meta:
        table_name = "memory_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class MoodConfigOverrides(AgentConfigBaseModel):
    """情绪配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    enable_mood = BooleanField(default=True, help_text="启用情绪系统")
    mood_update_threshold = FloatField(default=1.0, help_text="情绪更新阈值")
    emotion_style = CharField(max_length=200, default="", help_text="情感特征")

    class Meta:
        table_name = "mood_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class EmojiConfigOverrides(AgentConfigBaseModel):
    """表情包配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    emoji_chance = FloatField(default=0.6, help_text="表情包概率")
    max_reg_num = IntegerField(default=200, help_text="最大注册数量")
    do_replace = BooleanField(default=True, help_text="是否替换")
    check_interval = IntegerField(default=120, help_text="检查间隔")
    steal_emoji = BooleanField(default=True, help_text="偷取表情包")
    content_filtration = BooleanField(default=False, help_text="内容过滤")
    filtration_prompt = CharField(max_length=200, default="", help_text="过滤要求")

    class Meta:
        table_name = "emoji_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class ToolConfigOverrides(AgentConfigBaseModel):
    """工具配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    enable_tool = BooleanField(default=False, help_text="启用工具")

    class Meta:
        table_name = "tool_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class VoiceConfigOverrides(AgentConfigBaseModel):
    """语音配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    enable_asr = BooleanField(default=False, help_text="语音识别")

    class Meta:
        table_name = "voice_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class PluginConfigOverrides(AgentConfigBaseModel):
    """插件配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    enable_plugins = BooleanField(default=True, help_text="启用插件")
    tenant_mode_disable_plugins = BooleanField(default=True, help_text="租户模式禁用")
    allowed_plugins = TextField(default="[]", help_text="允许插件JSON数组")
    blocked_plugins = TextField(default="[]", help_text="禁止插件JSON数组")

    class Meta:
        table_name = "plugin_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class KeywordReactionConfigOverrides(AgentConfigBaseModel):
    """关键词反应配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    keyword_rules = TextField(default="[]", help_text="关键词规则JSON数组")
    regex_rules = TextField(default="[]", help_text="正则规则JSON数组")

    class Meta:
        table_name = "keyword_reaction_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


class RelationshipConfigOverrides(AgentConfigBaseModel):
    """关系配置覆盖模型"""

    id = CharField(primary_key=True, max_length=50, help_text="配置ID")
    agent_id = CharField(max_length=50, help_text="关联的Agent ID")

    enable_relationship = BooleanField(default=True, help_text="启用关系系统")

    class Meta:
        table_name = "relationship_config_overrides"
        indexes = (
            (('agent_id',), False),  # agent_id索引
        )


# 工具函数
def generate_config_id() -> str:
    """生成配置ID"""
    return f"config_{uuid.uuid4().hex[:12]}"


def parse_json_field(json_str: str, default=None):
    """解析JSON字段"""
    if not json_str:
        return default
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def serialize_json_field(obj) -> str:
    """序列化为JSON字段"""
    if not obj:
        return "[]"
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        return "[]"


# 配置模型列表
AGENT_CONFIG_MODELS = [
    PersonalityConfig,
    BotConfigOverrides,
    ChatConfigOverrides,
    ExpressionConfigOverrides,
    MemoryConfigOverrides,
    MoodConfigOverrides,
    EmojiConfigOverrides,
    ToolConfigOverrides,
    VoiceConfigOverrides,
    PluginConfigOverrides,
    KeywordReactionConfigOverrides,
    RelationshipConfigOverrides,
]

# 配置类型映射
CONFIG_TYPE_MAPPING = {
    "personality": PersonalityConfig,
    "bot_overrides": BotConfigOverrides,
    "chat": ChatConfigOverrides,
    "expression": ExpressionConfigOverrides,
    "memory": MemoryConfigOverrides,
    "mood": MoodConfigOverrides,
    "emoji": EmojiConfigOverrides,
    "tool": ToolConfigOverrides,
    "voice": VoiceConfigOverrides,
    "plugin": PluginConfigOverrides,
    "keyword_reaction": KeywordReactionConfigOverrides,
    "relationship": RelationshipConfigOverrides,
}

__all__ = [
    # 配置模型
    'PersonalityConfig',
    'BotConfigOverrides',
    'ChatConfigOverrides',
    'ExpressionConfigOverrides',
    'MemoryConfigOverrides',
    'MoodConfigOverrides',
    'EmojiConfigOverrides',
    'ToolConfigOverrides',
    'VoiceConfigOverrides',
    'PluginConfigOverrides',
    'KeywordReactionConfigOverrides',
    'RelationshipConfigOverrides',

    # 工具函数
    'generate_config_id',
    'parse_json_field',
    'serialize_json_field',

    # 常量
    'AGENT_CONFIG_MODELS',
    'CONFIG_TYPE_MAPPING',
]
