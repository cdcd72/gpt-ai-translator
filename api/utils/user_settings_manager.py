from api.storage.cache import MultiTierCacheAdapter


class UserSettingsManager:
    def __init__(self, cache: MultiTierCacheAdapter, app_name: str):
        self.cache = cache
        self.app_name = app_name

    def set_settings(self, user_id: str, settings: dict) -> None:
        key = f"{self.app_name}.{user_id}.settings"
        current_settings = self.cache.get(key) or {}
        updated_settings = {**current_settings, **settings}
        self.cache.set(key, updated_settings)

    def get_settings(self, user_id: str) -> dict:
        key = f"{self.app_name}.{user_id}.settings"
        return self.cache.get(key) or {}
