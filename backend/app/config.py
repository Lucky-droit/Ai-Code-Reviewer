import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _parse_cors_origins(value: str) -> list[str]:
    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or ["*"]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model_provider: str = os.getenv("MODEL_PROVIDER", "openai").strip().lower()
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "2"))
    max_code_lines: int = int(os.getenv("MAX_CODE_LINES", "500"))
    max_code_chars: int = int(os.getenv("MAX_CODE_CHARS", "25000"))
    mock_mode: bool = _parse_bool(os.getenv("MOCK_MODE", "false"))
    cors_origins: list[str] = field(
        default_factory=lambda: _parse_cors_origins(os.getenv("CORS_ORIGINS", "*"))
    )


settings = Settings()