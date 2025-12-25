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
    MessageReceiveConfigOverrides,
    MoodConfigOverrides,
    PersonalityConfig,
    PluginConfigOverrides,
    RelationshipConfigOverrides,
    ToolConfigOverrides,
    VoiceConfigOverrides,
    generate_config_id,
    parse_json_field,
    serialize_json_field,
    APIProviderModel,
    ModelInfoModel,
    ModelConfigOverrides,
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
        elif config_type == "message_receive":
            return self._create_message_receive_config_overrides(config_data)
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
            expression_groups=serialize_json_field(config_data.get('expression_groups', [])),
            reflect=config_data.get('reflect', False),
            reflect_operator_id=config_data.get('reflect_operator_id', ""),
            allow_reflect=serialize_json_field(config_data.get('allow_reflect', []))
        )

    def _create_memory_config_overrides(self, config_data: Dict[str, Any]) -> MemoryConfigOverrides:
        """创建记忆配置覆盖"""
        return MemoryConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            max_memory_number=config_data.get('max_memory_number', 100),
            memory_build_frequency=config_data.get('memory_build_frequency', 1),
            max_agent_iterations=config_data.get('max_agent_iterations', 5),
            enable_jargon_detection=config_data.get('enable_jargon_detection', True)
        )

    def _create_message_receive_config_overrides(self, config_data: Dict[str, Any]) -> MessageReceiveConfigOverrides:
        """创建消息接收配置覆盖"""
        return MessageReceiveConfigOverrides.create(
            id=generate_config_id(),
            agent_id=self.agent_id,
            ban_words=serialize_json_field(config_data.get('ban_words', [])),
            ban_msgs_regex=serialize_json_field(config_data.get('ban_msgs_regex', []))
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

    def get_all_configs(self, mask_secrets: bool = False) -> Dict[str, Any]:
        """
        获取所有配置并转换为JSON格式

        Args:
            mask_secrets: 是否掩盖敏感信息（如API Key）

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
        config_types = ["chat", "expression", "memory", "message_receive", "mood", "emoji", "tool", "voice", "plugin", "keyword_reaction", "relationship"]
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
                        "memory_build_frequency": overrides.memory_build_frequency,
                        "max_agent_iterations": overrides.max_agent_iterations,
                        "enable_jargon_detection": overrides.enable_jargon_detection
                    }
                elif config_type in ["expression"]:
                    config["config_overrides"][config_type] = {
                        "mode": overrides.mode,
                        "learning_list": parse_json_field(overrides.learning_list, []),
                        "expression_groups": parse_json_field(overrides.expression_groups, []),
                        "reflect": overrides.reflect,
                        "reflect_operator_id": overrides.reflect_operator_id,
                        "allow_reflect": parse_json_field(overrides.allow_reflect, [])
                    }
                elif config_type in ["message_receive"]:
                    config["config_overrides"][config_type] = {
                        "ban_words": parse_json_field(overrides.ban_words, []),
                        "ban_msgs_regex": parse_json_field(overrides.ban_msgs_regex, [])
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

                    config["config_overrides"][config_type] = {}
            
        # 获取模型配置 (新逻辑: 从关系表构建)
        model_config = {}
        
        # 1. API Providers
        providers = []
        try:
            provider_models = APIProviderModel.select().where(APIProviderModel.agent_id == self.agent_id)
            for pm in provider_models:
                p_data = {
                    "name": pm.name,
                    "client_type": pm.client_type,
                    "base_url": pm.base_url,
                    "api_key": pm.api_key,
                    "is_server_provider": pm.is_server_provider
                }
                if mask_secrets:
                    if p_data.get("api_key"):
                        p_data["api_key"] = "********"
                    if p_data.get("base_url"):
                        p_data["base_url"] = "********"
                providers.append(p_data)
        except Exception:
            pass
        model_config["api_providers"] = providers
        
        # 2. Model Infos
        models = []
        try:
            model_infos = ModelInfoModel.select().where(ModelInfoModel.agent_id == self.agent_id)
            for mi in model_infos:
                m_data = {
                    "name": mi.name,
                    "model_identifier": mi.model_identifier,
                    "api_provider": mi.provider_name,
                    "temperature": mi.temperature,
                    "price_in": mi.price_in,
                    "price_out": mi.price_out,
                    "extra_params": parse_json_field(mi.extra_params, {})
                }
                models.append(m_data)
        except Exception:
            pass
        model_config["models"] = models
        
        # 3. Model Task Config (Stored in ModelConfigOverrides)
        task_config = {}
        try:
            m_overrides = ModelConfigOverrides.get(ModelConfigOverrides.agent_id == self.agent_id)
            task_config = parse_json_field(m_overrides.model_task_config, {})
        except Exception:
            pass
        model_config["model_task_config"] = task_config
        
        config["config_overrides"]["model"] = model_config

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
        
        # 更新模型配置 (新逻辑)
        if "config_overrides" in config_json and "model" in config_json["config_overrides"]:
            self._update_model_config(config_json["config_overrides"]["model"])

    def _update_model_config(self, model_data: Dict[str, Any]):
        """更新模型配置（处理独立表）"""
        
        # 1. 更新 API Providers
        if "api_providers" in model_data:
            for p_data in model_data["api_providers"]:
                name = p_data.get("name")
                if not name: continue
                
                # Check for existing to handle masking
                existing = None
                try:
                    existing = APIProviderModel.get(
                        (APIProviderModel.agent_id == self.agent_id) & 
                        (APIProviderModel.name == name)
                    )
                except APIProviderModel.DoesNotExist:
                    pass
                
                api_key = p_data.get("api_key")
                base_url = p_data.get("base_url")
                
                # 如果前端发来掩码，且存在旧值，则保留旧值
                if api_key == "********" and existing:
                    api_key = existing.api_key
                if base_url == "********" and existing:
                    base_url = existing.base_url
                
                if existing:
                    existing.client_type = p_data.get("client_type", existing.client_type)
                    existing.base_url = base_url
                    existing.api_key = api_key # Use resolved key
                    existing.is_server_provider = p_data.get("is_server_provider", existing.is_server_provider)
                    existing.save()
                else:
                    APIProviderModel.create(
                        id=generate_config_id(),
                        agent_id=self.agent_id,
                        name=name,
                        client_type=p_data.get("client_type", "openai"),
                        base_url=base_url,
                        api_key=api_key,
                        is_server_provider=p_data.get("is_server_provider", False)
                    )

        # 2. 更新 Model Infos
        if "models" in model_data:
            for m_data in model_data["models"]:
                name = m_data.get("name")
                if not name: continue
                
                try:
                    existing = ModelInfoModel.get(
                        (ModelInfoModel.agent_id == self.agent_id) & 
                        (ModelInfoModel.name == name)
                    )
                    existing.model_identifier = m_data.get("model_identifier", existing.model_identifier)
                    existing.provider_name = m_data.get("api_provider", existing.provider_name)
                    existing.temperature = m_data.get("temperature", existing.temperature)
                    existing.price_in = m_data.get("price_in", existing.price_in)
                    existing.price_out = m_data.get("price_out", existing.price_out)
                    existing.extra_params = serialize_json_field(m_data.get("extra_params", {}))
                    existing.save()
                except ModelInfoModel.DoesNotExist:
                    ModelInfoModel.create(
                        id=generate_config_id(),
                        agent_id=self.agent_id,
                        name=name,
                        model_identifier=m_data.get("model_identifier", ""),
                        provider_name=m_data.get("api_provider", ""),
                        temperature=m_data.get("temperature"),
                        price_in=m_data.get("price_in", 0.0),
                        price_out=m_data.get("price_out", 0.0),
                        extra_params=serialize_json_field(m_data.get("extra_params", {}))
                    )

        # 3. 更新 Task Config (存入 ModelConfigOverrides)
        if "model_task_config" in model_data:
            try:
                mo_existing = ModelConfigOverrides.get(ModelConfigOverrides.agent_id == self.agent_id)
                mo_existing.model_task_config = serialize_json_field(model_data["model_task_config"])
                mo_existing.save()
            except ModelConfigOverrides.DoesNotExist:
                ModelConfigOverrides.create(
                    id=generate_config_id(),
                    agent_id=self.agent_id,
                    model_task_config=serialize_json_field(model_data["model_task_config"])
                )

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
                MessageReceiveConfigOverrides,
                MoodConfigOverrides,
                EmojiConfigOverrides,
                ToolConfigOverrides,
                VoiceConfigOverrides,
                PluginConfigOverrides,
                KeywordReactionConfigOverrides,
                RelationshipConfigOverrides,
                ModelConfigOverrides,
                APIProviderModel,
                ModelInfoModel,
            ]:
                try:
                    configs = config_model.select().where(config_model.agent_id == self.agent_id)
                    for config in configs:
                        config.delete_instance()
                except Exception:
                    continue
        except Exception:
            pass
