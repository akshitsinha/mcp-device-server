from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    enable_camera: bool = Field(default=True, description="Enable camera functionality")
    enable_printer: bool = Field(
        default=True, description="Enable printer functionality"
    )
    enable_audio: bool = Field(default=True, description="Enable audio functionality")
    enable_screen: bool = Field(
        default=True, description="Enable screen capture functionality"
    )

    model_config = {
        "env_prefix": "MCP_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_settings() -> Settings:
    return Settings()
