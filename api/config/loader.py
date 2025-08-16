from flask import Flask
from api.config.base import BaseConfig
from api.config.env import *
from api.config.key import ConfigKey


class ConfigLoader:
    def __init__(self):
        self.environment_map = {
            Environment.DEVELOPMENT: DevelopmentConfig,
            Environment.PRODUCTION: ProductionConfig,
            Environment.VERCEL: ProductionForVercelConfig,
        }
        self.environment = Environment[
            BaseConfig.get_str(ConfigKey.APP_ENVIRONMENT, Environment.VERCEL.value)
        ]

    def apply_to(self, app: Flask):
        app.config.from_object(self.environment_map.get(self.environment))
        app.config[ConfigKey.APP_NAME] = BaseConfig.get_str(
            ConfigKey.APP_NAME, "gpt-ai-translator"
        )
        app.config[ConfigKey.APP_PERSISTENT_USER_SETTINGS_ENABLED] = (
            BaseConfig.get_bool(ConfigKey.APP_PERSISTENT_USER_SETTINGS_ENABLED, False)
        )
        app.config[ConfigKey.APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED] = (
            BaseConfig.get_bool(ConfigKey.APP_PUSH_TRANSLATED_TEXT_AUDIO_ENABLED, False)
        )
