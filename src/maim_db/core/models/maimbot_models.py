"""
MaiMBot 核心数据模型
迁移自 MaiMBot/src/common/database/database_model.py
"""
from datetime import datetime
from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    DoubleField,
    FloatField,
    IntegerField,
    TextField,
)
from .business import BusinessBaseModel


class ChatStreams(BusinessBaseModel):
    """
    用于存储流式记录数据的模型
    """
    # agent_id 由 BusinessBaseModel 提供

    # stream_id: "a544edeb1a9b73e3e1d77dff36e41264"
    stream_id = TextField(unique=True, index=True)
    create_time = DoubleField()
    
    # group_info
    group_platform = TextField(null=True)
    group_id = TextField(null=True)
    group_name = TextField(null=True)

    last_active_time = DoubleField()
    platform = TextField()

    # user_info 字段
    user_platform = TextField()
    user_id = TextField()
    user_nickname = TextField()
    user_cardname = TextField(null=True)

    class Meta:
        table_name = "chat_streams"


class LLMUsage(BusinessBaseModel):
    """
    用于存储 API 使用日志数据的模型。
    """
    model_name = TextField(index=True)
    model_assign_name = TextField(null=True)
    model_api_provider = TextField(null=True)
    user_id = TextField(index=True)
    request_type = TextField(index=True)
    endpoint = TextField()
    prompt_tokens = IntegerField()
    completion_tokens = IntegerField()
    total_tokens = IntegerField()
    cost = DoubleField()
    time_cost = DoubleField(null=True)
    status = TextField()
    timestamp = DateTimeField(index=True)

    class Meta:
        table_name = "llm_usage"


class Emoji(BusinessBaseModel):
    """表情包"""
    full_path = TextField(unique=True, index=True)
    format = TextField()
    emoji_hash = TextField(index=True)
    description = TextField()
    query_count = IntegerField(default=0)
    is_registered = BooleanField(default=False)
    is_banned = BooleanField(default=False)
    emotion = TextField(null=True)
    record_time = FloatField()
    register_time = FloatField(null=True)
    usage_count = IntegerField(default=0)
    last_used_time = FloatField(null=True)

    class Meta:
        table_name = "emoji"


class Messages(BusinessBaseModel):
    """
    用于存储消息数据的模型。
    """
    message_id = TextField(index=True)
    time = DoubleField()
    chat_id = TextField(index=True)  # 对应的 ChatStreams stream_id
    reply_to = TextField(null=True)

    interest_value = DoubleField(null=True)
    key_words = TextField(null=True)
    key_words_lite = TextField(null=True)

    is_mentioned = BooleanField(null=True)
    is_at = BooleanField(null=True)
    reply_probability_boost = DoubleField(null=True)
    
    # Flat fields from chat_info
    chat_info_stream_id = TextField()
    chat_info_platform = TextField()
    chat_info_user_platform = TextField()
    chat_info_user_id = TextField()
    chat_info_user_nickname = TextField()
    chat_info_user_cardname = TextField(null=True)
    chat_info_group_platform = TextField(null=True)
    chat_info_group_id = TextField(null=True)
    chat_info_group_name = TextField(null=True)
    chat_info_create_time = DoubleField()
    chat_info_last_active_time = DoubleField()

    # Flat fields from user_info (sender)
    user_platform = TextField(null=True)
    user_id_ = TextField(column_name='user_id', null=True)
    user_nickname = TextField(null=True)
    user_cardname = TextField(null=True)

    processed_plain_text = TextField(null=True)
    display_message = TextField(null=True)

    priority_mode = TextField(null=True)
    priority_info = TextField(null=True)

    additional_config = TextField(null=True)
    is_emoji = BooleanField(default=False)
    is_picid = BooleanField(default=False)
    is_command = BooleanField(default=False)
    intercept_message_level = IntegerField(default=0)
    is_notify = BooleanField(default=False)

    selected_expressions = TextField(null=True)

    class Meta:
        table_name = "messages"


class ActionRecords(BusinessBaseModel):
    """
    用于存储动作记录数据的模型。
    """
    action_id = TextField(index=True)
    time = DoubleField()
    action_reasoning = TextField(null=True)
    action_name = TextField()
    action_data = TextField()
    action_done = BooleanField(default=False)
    action_build_into_prompt = BooleanField(default=False)
    action_prompt_display = TextField()
    chat_id = TextField(index=True)
    chat_info_stream_id = TextField()
    chat_info_platform = TextField()

    class Meta:
        table_name = "action_records"


class Images(BusinessBaseModel):
    """
    用于存储图像信息的模型。
    """
    image_id = TextField(default="")
    emoji_hash = TextField(index=True)
    description = TextField(null=True)
    path = TextField(unique=True)
    count = IntegerField(default=1)
    timestamp = FloatField()
    type = TextField()
    vlm_processed = BooleanField(default=False)

    class Meta:
        table_name = "images"


class ImageDescriptions(BusinessBaseModel):
    """
    用于存储图像描述信息的模型。
    """
    type = TextField()
    image_description_hash = TextField(index=True)
    description = TextField()
    timestamp = FloatField()

    class Meta:
        table_name = "image_descriptions"


class EmojiDescriptionCache(BusinessBaseModel):
    """
    存储表情包的详细描述和情感标签缓存
    """
    emoji_hash = TextField(unique=True, index=True)
    description = TextField()
    emotion_tags = TextField(null=True)
    timestamp = FloatField()

    class Meta:
        table_name = "emoji_description_cache"


class RuntimeState(BusinessBaseModel):
    """跨进程运行时状态存储"""
    state_key = TextField(index=True)
    state_value = TextField(null=True)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "runtime_state"
        indexes = ((("agent_id", "state_key"), True),)


class HippoTopicCache(BusinessBaseModel):
    """Hippo 话题缓存"""
    chat_id = TextField(index=True)
    topics_payload = TextField(null=True)
    last_topic_check_time = FloatField(default=0.0)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "hippo_topic_cache"
        indexes = ((("agent_id", "chat_id"), True),)


class HippoBatchState(BusinessBaseModel):
    """Hippo 当前批次状态"""
    chat_id = TextField(index=True)
    start_time = DoubleField(null=True)
    end_time = DoubleField(null=True)
    updated_at = DateTimeField(default=datetime.utcnow)

    class Meta:
        table_name = "hippo_batch_state"
        indexes = ((("agent_id", "chat_id"), True),)


class OnlineTime(BusinessBaseModel):
    """在线时长记录"""
    timestamp = TextField(default=str(datetime.now()))
    duration = IntegerField()
    start_timestamp = DateTimeField(default=datetime.now)
    end_timestamp = DateTimeField(index=True)

    class Meta:
        table_name = "online_time"


class PersonInfo(BusinessBaseModel):
    """
    用于存储个人信息数据的模型。
    """
    is_known = BooleanField(default=False)
    person_id = TextField(unique=True, index=True)
    person_name = TextField(null=True)
    name_reason = TextField(null=True)
    platform = TextField()
    user_id = TextField(index=True)
    nickname = TextField(null=True)
    group_nick_name = TextField(null=True)
    memory_points = TextField(null=True)
    know_times = FloatField(null=True)
    know_since = FloatField(null=True)
    last_know = FloatField(null=True)

    class Meta:
        table_name = "person_info"


class GroupInfo(BusinessBaseModel):
    """
    用于存储群组信息数据的模型。
    """
    group_id = TextField(unique=True, index=True)
    group_name = TextField(null=True)
    platform = TextField()
    group_impression = TextField(null=True)
    member_list = TextField(null=True)
    topic = TextField(null=True)
    create_time = FloatField(null=True)
    last_active = FloatField(null=True)
    member_count = IntegerField(null=True, default=0)

    class Meta:
        table_name = "group_info"


class Expression(BusinessBaseModel):
    """
    用于存储表达风格的模型。
    """
    situation = TextField()
    style = TextField()
    context = TextField(null=True)
    content_list = TextField(null=True)
    count = IntegerField(default=1)
    last_active_time = FloatField()
    chat_id = TextField(index=True)
    create_date = FloatField(null=True)
    checked = BooleanField(default=False)
    rejected = BooleanField(default=False)

    class Meta:
        table_name = "expression"


class Jargon(BusinessBaseModel):
    """
    用于存储俚语的模型
    """
    content = TextField()
    raw_content = TextField(null=True)
    meaning = TextField(null=True)
    chat_id = TextField(index=True)
    is_global = BooleanField(default=False)
    count = IntegerField(default=0)
    is_jargon = BooleanField(null=True)
    last_inference_count = IntegerField(null=True)
    is_complete = BooleanField(default=False)
    inference_with_context = TextField(null=True)
    inference_content_only = TextField(null=True)

    class Meta:
        table_name = "jargon"


class ChatHistorySummary(BusinessBaseModel):
    """
    用于存储聊天历史概括的模型 (Renamed from ChatHistory to avoid conflict)
    """
    chat_id = TextField(index=True)
    start_time = DoubleField()
    end_time = DoubleField()
    original_text = TextField()
    participants = TextField()
    theme = TextField()
    keywords = TextField()
    summary = TextField()
    key_point = TextField(null=True)
    count = IntegerField(default=0)
    forget_times = IntegerField(default=0)

    class Meta:
        table_name = "chat_history_summary"


class ThinkingBack(BusinessBaseModel):
    """
    用于存储记忆检索思考过程的模型
    """
    chat_id = TextField(index=True)
    question = TextField()
    context = TextField(null=True)
    found_answer = BooleanField(default=False)
    answer = TextField(null=True)
    thinking_steps = TextField(null=True)
    create_time = DoubleField()
    update_time = DoubleField()

    class Meta:
        table_name = "thinking_back"


MAIMBOT_MODELS = [
    ChatStreams,
    LLMUsage,
    Emoji,
    Messages,
    Images,
    ImageDescriptions,
    EmojiDescriptionCache,
    RuntimeState,
    HippoTopicCache,
    HippoBatchState,
    OnlineTime,
    PersonInfo,
    GroupInfo,
    Expression,
    Jargon,
    ChatHistorySummary,
    ThinkingBack,
]
