import os
from typing import Optional


class BaseConfig:
    @staticmethod
    def get_str(key: str, default: Optional[str] = None) -> Optional[str]:
        value = os.getenv(key)
        return value if value is not None else default

    @staticmethod
    def get_required(key: str) -> str:
        value = BaseConfig.get_str(key)
        if value is None or value.strip() == "":
            raise EnvironmentError(f"缺少必要的環境變數：{key}")
        return value

    @staticmethod
    def get_int(key: str, default: Optional[int] = None) -> int:
        value = BaseConfig.get_str(key)
        if value is None:
            if default is None:
                raise EnvironmentError(f"找不到整數型環境變數：{key}")
            return default
        try:
            return int(value)
        except ValueError:
            raise TypeError(f"環境變數 {key} 必須是整數")

    @staticmethod
    def get_float(key: str, default: Optional[float] = None) -> float:
        value = BaseConfig.get_str(key)
        if value is None:
            if default is None:
                raise EnvironmentError(f"找不到浮點數型環境變數：{key}")
            return default
        try:
            return float(value)
        except ValueError:
            raise TypeError(f"環境變數 {key} 必須是浮點數")

    @staticmethod
    def get_bool(key: str, default: Optional[bool] = None) -> bool:
        value = BaseConfig.get_str(key)
        if value is None:
            if default is None:
                raise EnvironmentError(f"找不到布林值型環境變數：{key}")
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")
