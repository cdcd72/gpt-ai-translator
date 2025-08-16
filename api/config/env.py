import os
from enum import Enum


class EnvironmentConfig:
    TESTING = False


class DevelopmentConfig(EnvironmentConfig):
    ENV = "development"
    DEBUG = True
    AUDIO_TEMP_PATH = os.path.join("data", "audio")


class ProductionConfig(EnvironmentConfig):
    ENV = "production"
    DEBUG = False
    AUDIO_TEMP_PATH = os.path.join("data", "audio")


class ProductionForVercelConfig(EnvironmentConfig):
    ENV = "production"
    DEBUG = False
    AUDIO_TEMP_PATH = "/tmp"


class Environment(Enum):
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"
    VERCEL = "VERCEL"
