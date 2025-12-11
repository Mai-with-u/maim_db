"""
Agent配置管理器
提供Agent配置的创建、更新、查询和转换功能
"""

from typing import Any, Dict, Optional

from .models import (
    CONFIG_TYPE_MAPPING,
    BotConfigOverrides,
    ChatConfigOverrides,
    EmojiConfigOverrides,
    ExpressionConfigOverrides,
    KeywordReactionConfigOverrides,
    MemoryConfigOverrides,
    MoodConfigOverrides,
    PersonalityConfig,
    PluginConfigOverrides,
    RelationshipConfigOverrides,
    ToolConfigOverrides,
    VoiceConfigOverrides,
    generate_config_id,
    parse_json_field,
    serialize_json_field,
)


class AgentConfigManager:
    """Agent配置管理器"""

    def __init__(self, agent_id: str):
        """
        初始化配置管理器

        Args:
            agent_id: Agent ID
        """
        self.agent_id = agent_id

    def create_personality_config(self, persona_data: Dict[str, Any]) -> PersonalityConfig:
        """
        创建人格配置

        Args:
            persona_data: 人格数据字典

        Returns:
            PersonalityConfig: 创建的人格配置实例
        """
        states = persona_data.get('states', [])
        if isinstance(states, list):
            states_str = serialize_json_field(states)
        else:
            states_str = "[]"

        return PersonalityConfig.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            personality=persona_data.get('personality', ''),
            reply_style=persona_data.get('reply_style', ''),
            interest=persona_data.get('interest', ''),
            plan_style=persona_data.get('plan_style', ''),
            private_plan_style=persona_data.get('private_plan_style', ''),
            visual_style=persona_data.get('visual_style', ''),
            states=states_str,
            state_probability=persona_data.get('state_probability', 0.0)
        )

    def create_bot_config_overrides(self, bot_overrides_data: Dict[str, Any]) -> BotConfigOverrides:
        """
        创建Bot配置覆盖

        Args:
            bot_overrides_data: Bot覆盖数据字典

        Returns:
            BotConfigOverrides: 创建的Bot配置覆盖实例
        """
        platforms = bot_overrides_data.get('platforms', [])
        alias_names = bot_overrides_data.get('alias_names', [])

        return BotConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            platform=bot_overrides_data.get('platform', ''),
            qq_account=bot_overrides_data.get('qq_account', ''),
            nickname=bot_overrides_data.get('nickname', ''),
            platforms=serialize_json_field(platforms),
            alias_names=serialize_json_field(alias_names)
        )

    def create_config_overrides(self, config_type: str, config_data: Dict[str, Any]):
        """
        创建配置覆盖

        Args:
            config_type: 配置类型
            config_data: 配置数据字典

        Returns:
            创建的配置覆盖实例
        """
        config_class = CONFIG_TYPE_MAPPING.get(config_type)
        if not config_class:
            raise ValueError(f"不支持的配置类型: {config_type}")

        # 根据配置类型创建特定的配置
        if config_type == "chat":
            return self._create_chat_config_overrides(config_data)
        elif config_type == "expression":
            return self._create_expression_config_overrides(config_data)
        elif config_type == "memory":
            return self._create_memory_config_overrides(config_data)
        elif config_type == "mood":
            return self._create_mood_config_overrides(config_data)
        elif config_type == "emoji":
            return self._create_emoji_config_overrides(config_data)
        elif config_type == "tool":
            return self._create_tool_config_overrides(config_data)
        elif config_type == "voice":
            return self._create_voice_config_overrides(config_data)
        elif config_type == "plugin":
            return self._create_plugin_config_overrides(config_data)
        elif config_type == "keyword_reaction":
            return self._create_keyword_reaction_config_overrides(config_data)
        elif config_type == "relationship":
            return self._create_relationship_config_overrides(config_data)
        else:
            raise ValueError(f"不支持的配置类型: {config_type}")

    def _create_chat_config_overrides(self, config_data: Dict[str, Any]) -> ChatConfigOverrides:
        """创建聊天配置覆盖"""
        return ChatConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            max_context_size=config_data.get('max_context_size', 18),
            interest_rate_mode=config_data.get('interest_rate_mode', 'fast'),
            planner_size=config_data.get('planner_size', 1.5),
            mentioned_bot_reply=config_data.get('mentioned_bot_reply', True),
            auto_chat_value=config_data.get('auto_chat_value', 1.0),
            enable_auto_chat_value_rules=config_data.get('enable_auto_chat_value_rules', True),
            at_bot_inevitable_reply=config_data.get('at_bot_inevitable_reply', 1.0),
            planner_smooth=config_data.get('planner_smooth', 3.0),
            talk_value=config_data.get('talk_value', 1.0),
            enable_talk_value_rules=config_data.get('enable_talk_value_rules', True),
            talk_value_rules=serialize_json_field(config_data.get('talk_value_rules', [])),
            auto_chat_value_rules=serialize_json_field(config_data.get('auto_chat_value_rules', []))
        )

    def _create_expression_config_overrides(self, config_data: Dict[str, Any]) -> ExpressionConfigOverrides:
        """创建表达配置覆盖"""
        return ExpressionConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            mode=config_data.get('mode', 'classic'),
            learning_list=serialize_json_field(config_data.get('learning_list', [])),
            expression_groups=serialize_json_field(config_data.get('expression_groups', []))
        )

    def _create_memory_config_overrides(self, config_data: Dict[str, Any]) -> MemoryConfigOverrides:
        """创建记忆配置覆盖"""
        return MemoryConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            max_memory_number=config_data.get('max_memory_number', 100),
            memory_build_frequency=config_data.get('memory_build_frequency', 1)
        )

    def _create_mood_config_overrides(self, config_data: Dict[str, Any]) -> MoodConfigOverrides:
        """创建情绪配置覆盖"""
        return MoodConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            enable_mood=config_data.get('enable_mood', True),
            mood_update_threshold=config_data.get('mood_update_threshold', 1.0),
            emotion_style=config_data.get('emotion_style', '')
        )

    def _create_emoji_config_overrides(self, config_data: Dict[str, Any]) -> EmojiConfigOverrides:
        """创建表情包配置覆盖"""
        return EmojiConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            emoji_chance=config_data.get('emoji_chance', 0.6),
            max_reg_num=config_data.get('max_reg_num', 200),
            do_replace=config_data.get('do_replace', True),
            check_interval=config_data.get('check_interval', 120),
            steal_emoji=config_data.get('steal_emoji', True),
            content_filtration=config_data.get('content_filtration', False),
            filtration_prompt=config_data.get('filtration_prompt', '')
        )

    def _create_tool_config_overrides(self, config_data: Dict[str, Any]) -> ToolConfigOverrides:
        """创建工具配置覆盖"""
        return ToolConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            enable_tool=config_data.get('enable_tool', False)
        )

    def _create_voice_config_overrides(self, config_data: Dict[str, Any]) -> VoiceConfigOverrides:
        """创建语音配置覆盖"""
        return VoiceConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            enable_asr=config_data.get('enable_asr', False)
        )

    def _create_plugin_config_overrides(self, config_data: Dict[str, Any]) -> PluginConfigOverrides:
        """创建插件配置覆盖"""
        return PluginConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            enable_plugins=config_data.get('enable_plugins', True),
            tenant_mode_disable_plugins=config_data.get('tenant_mode_disable_plugins', True),
            allowed_plugins=serialize_json_field(config_data.get('allowed_plugins', [])),
            blocked_plugins=serialize_json_field(config_data.get('blocked_plugins', []))
        )

    def _create_keyword_reaction_config_overrides(self, config_data: Dict[str, Any]) -> KeywordReactionConfigOverrides:
        """创建关键词反应配置覆盖"""
        return KeywordReactionConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            keyword_rules=serialize_json_field(config_data.get('keyword_rules', [])),
            regex_rules=serialize_json_field(config_data.get('regex_rules', []))
        )

    def _create_relationship_config_overrides(self, config_data: Dict[str, Any]) -> RelationshipConfigOverrides:
        """创建关系配置覆盖"""
        return RelationshipConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            enable_relationship=config_data.get('enable_relationship', True)
        )

    def get_personality_config(self) -> Optional[PersonalityConfig]:
        """获取人格配置"""
        try:
            return PersonalityConfig.get(PersonalityConfig.agent_id == self.agent_id)
        except PersonalityConfig.DoesNotExist:
            return None

    def get_config_overrides(self, config_type: str):
        """获取特定类型的配置覆盖"""
        config_class = CONFIG_TYPE_MAPPING.get(config_type)
        if not config_class:
            raise ValueError(f"不支持的配置类型: {config_type}")

        try:
            return config_class.get(config_class.agent_id == self.agent_id)
        except Exception:
            return None

    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置并转换为JSON格式

        Returns:
            Dict[str, Any]: 包含所有配置的字典，格式与原来的JSON配置一致
        """
        config = {
            "persona": {},
            "bot_overrides": {},
            "config_overrides": {}
        }

        # 获取人格配置
        personality_config = self.get_personality_config()
        if personality_config:
            config["persona"] = {
                "personality": personality_config.personality,
                "reply_style": personality_config.reply_style,
                "interest": personality_config.interest,
                "plan_style": personality_config.plan_style,
                "private_plan_style": personality_config.private_plan_style,
                "visual_style": personality_config.visual_style,
                "states": parse_json_field(personality_config.states, []),
                "state_probability": personality_config.state_probability
            }

        # 获取Bot配置覆盖
        bot_config = self.get_config_overrides("bot_overrides")
        if bot_config:
            config["bot_overrides"] = {
                "platform": bot_config.platform,
                "qq_account": bot_config.qq_account,
                "nickname": bot_config.nickname,
                "platforms": parse_json_field(bot_config.platforms, []),
                "alias_names": parse_json_field(bot_config.alias_names, [])
            }

        # 获取其他配置覆盖
        config_types = ["chat", "expression", "memory", "mood", "emoji", "tool", "voice", "plugin", "keyword_reaction", "relationship"]
        for config_type in config_types:
            overrides = self.get_config_overrides(config_type)
            if overrides:
                if config_type in ["chat"]:
                    config["config_overrides"][config_type] = {
                        "max_context_size": overrides.max_context_size,
                        "interest_rate_mode": overrides.interest_rate_mode,
                        "planner_size": overrides.planner_size,
                        "mentioned_bot_reply": overrides.mentioned_bot_reply,
                        "auto_chat_value": overrides.auto_chat_value,
                        "enable_auto_chat_value_rules": overrides.enable_auto_chat_value_rules,
                        "at_bot_inevitable_reply": overrides.at_bot_inevitable_reply,
                        "planner_smooth": overrides.planner_smooth,
                        "talk_value": overrides.talk_value,
                        "enable_talk_value_rules": overrides.enable_talk_value_rules,
                        "talk_value_rules": parse_json_field(overrides.talk_value_rules, []),
                        "auto_chat_value_rules": parse_json_field(overrides.auto_chat_value_rules, [])
                    }
                elif config_type in ["plugin"]:
                    config["config_overrides"][config_type] = {
                        "enable_plugins": overrides.enable_plugins,
                        "tenant_mode_disable_plugins": overrides.tenant_mode_disable_plugins,
                        "allowed_plugins": parse_json_field(overrides.allowed_plugins, []),
                        "blocked_plugins": parse_json_field(overrides.blocked_plugins, [])
                    }
                elif config_type in ["emoji"]:
                    config["config_overrides"][config_type] = {
                        "emoji_chance": overrides.emoji_chance,
                        "max_reg_num": overrides.max_reg_num,
                        "do_replace": overrides.do_replace,
                        "check_interval": overrides.check_interval,
                        "steal_emoji": overrides.steal_emoji,
                        "content_filtration": overrides.content_filtration,
                        "filtration_prompt": overrides.filtration_prompt
                    }
                elif config_type in ["memory"]:
                    config["config_overrides"][config_type] = {
                        "max_memory_number": overrides.max_memory_number,
                        "memory_build_frequency": overrides.memory_build_frequency
                    }
                elif config_type in ["mood"]:
                    config["config_overrides"][config_type] = {
                        "enable_mood": overrides.enable_mood,
                        "mood_update_threshold": overrides.mood_update_threshold,
                        "emotion_style": overrides.emotion_style
                    }
                else:
                    # 其他配置类型的通用处理
                    config["config_overrides"][config_type] = {}

        return config

    def update_config_from_json(self, config_json: Dict[str, Any]):
        """
        从JSON配置更新Agent配置

        Args:
            config_json: JSON配置字典
        """
        # 更新人格配置
        if "persona" in config_json:
            persona_data = config_json["persona"]
            existing = self.get_personality_config()
            if existing:
                # 更新现有配置
                existing.personality = persona_data.get('personality', existing.personality)
                existing.reply_style = persona_data.get('reply_style', existing.reply_style)
                existing.interest = persona_data.get('interest', existing.interest)
                existing.plan_style = persona_data.get('plan_style', existing.plan_style)
                existing.private_plan_style = persona_data.get('private_plan_style', existing.private_plan_style)
                existing.visual_style = persona_data.get('visual_style', existing.visual_style)
                existing.states = serialize_json_field(persona_data.get('states', []))
                existing.state_probability = persona_data.get('state_probability', existing.state_probability)
                existing.save()
            else:
                # 创建新配置
                self.create_personality_config(persona_data)

        # 更新Bot配置覆盖
        if "bot_overrides" in config_json:
            bot_data = config_json["bot_overrides"]
            existing = self.get_config_overrides("bot_overrides")
            if existing:
                # 更新现有配置
                existing.platform = bot_data.get('platform', existing.platform)
                existing.qq_account = bot_data.get('qq_account', existing.qq_account)
                existing.nickname = bot_data.get('nickname', existing.nickname)
                existing.platforms = serialize_json_field(bot_data.get('platforms', []))
                existing.alias_names = serialize_json_field(bot_data.get('alias_names', []))
                existing.save()
            else:
                # 创建新配置
                self.create_bot_config_overrides(bot_data)

        # 更新其他配置覆盖
        if "config_overrides" in config_json:
            config_data = config_json["config_overrides"]
            for config_type, overrides_data in config_data.items():
                try:
                    existing = self.get_config_overrides(config_type)
                    if existing:
                        # 删除现有配置并创建新的
                        existing.delete_instance()
                    self.create_config_overrides(config_type, overrides_data)
                except ValueError:
                    # 跳过不支持的配置类型
                    continue

    def delete_all_configs(self):
        """删除Agent的所有配置"""
        try:
            # 删除人格配置
            personality = self.get_personality_config()
            if personality:
                personality.delete_instance()

            # 删除所有配置覆盖
            for config_model in [
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
            ]:
                try:
                    configs = config_model.select().where(config_model.agent_id == self.agent_id)
                    for config in configs:
                        config.delete_instance()
                except Exception:
                    continue
        except Exception:
            pass
