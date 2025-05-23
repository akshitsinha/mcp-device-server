from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Host to bind the server to")
    port: int = Field(default=8000, description="Port to bind the server to")

    enable_camera: bool = Field(default=True, description="Enable camera functionality")
    enable_printer: bool = Field(
        default=True, description="Enable printer functionality"
    )
    enable_audio: bool = Field(default=True, description="Enable audio functionality")
    enable_storage: bool = Field(
        default=True, description="Enable storage device functionality"
    )
    enable_screen: bool = Field(
        default=True, description="Enable screen capture functionality"
    )
    enable_usb: bool = Field(
        default=True, description="Enable USB device functionality"
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
