from __future__ import annotations

from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    - Uses pydantic-settings v2 style config (model_config).
    - Forbids unknown env keys (helps catch typos).
    - Supports CORS_ORIGINS as a comma-separated string or JSON list.
    """

    # pydantic-settings v2 config
    model_config = SettingsConfigDict(
        env_file=".env",  # load from .env (plus actual environment)
        extra="forbid",  # complain about unknown keys
        str_strip_whitespace=True,
    )

    # === Core API keys / tokens ===
    entsoe_api_token: str = Field(default="", env="ENTSOE_API_TOKEN")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")

    # === App settings ===
    entsoe_base_url: str = Field(
        default="https://web-api.tp.entsoe.eu/api", env="ENTSOE_BASE_URL"
    )
    use_mock_data: bool = Field(default=False, env="USE_MOCK_DATA")

    # CORS origins: can be a JSON list or a comma-separated string
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS",
    )

    # === Mock data controls (added to avoid extra_forbidden) ===
    mock_source: Optional[str] = Field(default=None, env="MOCK_SOURCE")
    mock_data_dir: Optional[str] = Field(default=None, env="MOCK_DATA_DIR")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(
            cls, v: Union[str, List[str], None]
    ) -> List[str]:
        """
        Accept either:
        - JSON list: '["http://a","http://b"]'
        - Comma-separated: 'http://a,http://b'
        - Python list
        """
        if v is None:
            return []
        if isinstance(v, list):
            return [s.strip() for s in v if isinstance(s, str)]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # If it looks like JSON list, let pydantic parse it (it already tried).
            # Otherwise treat as comma-separated.
            if v.startswith("[") and v.endswith("]"):
                # Let pydantic raise if malformed JSON; otherwise user can switch to comma-separated
                import json
                parsed = json.loads(v)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS must be a list or comma-separated string")
                return [str(s).strip() for s in parsed]
            return [part.strip() for part in v.split(",") if part.strip()]
        raise ValueError("Unsupported type for CORS_ORIGINS")


# Instantiate once and import elsewhere
settings = Settings()
