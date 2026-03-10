"""Configuration for Multimodal Spec Navigator."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    text_embedding_model: str = "all-MiniLM-L6-v2"
    clip_model: str = "openai/clip-vit-base-patch32"
    demo_mode: bool = True
    log_level: str = "INFO"
    
    ui_port: int = 7860
    ui_share: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
