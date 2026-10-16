# conf/conf.py
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

ENV_FILE = Path(__file__).parents[1] / ".env"

class Settings(BaseSettings):
    # LLM 配置
    LLM_MODEL: str
    LLM_BASE_URL: str
    LLM_API_KEY: SecretStr  # 密钥用SecretStr，打印不会明文泄露

    # 业务API
    COMMERCE_API_BASE_URL: str

    # 数据库
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # 服务监听
    APP_HOST: str
    APP_PORT: int

    # 加载 .env 文件
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # 忽略.env里面没有定义在类里的多余变量，防止报错
    )


# lru_cache 单例，全局只加载一次.env，避免重复读取
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# 全局配置实例，项目其他地方直接 import 使用
settings = get_settings()

if __name__ == "__main__":
    print(settings.APP_HOST)


