"""Runtime settings. Every value comes from the environment (or a local, git-ignored .env).

Secrets are never read from this repo: ANTHROPIC_API_KEY comes from Azure Key Vault in
production (see keyvault.py); the Power BI identity comes from azure-identity's
DefaultAzureCredential (managed identity, or AZURE_CLIENT_ID / AZURE_TENANT_ID /
AZURE_CLIENT_SECRET for a service principal).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Claude ---------------------------------------------------------------------------
    anthropic_model: str = "claude-opus-5-5"
    # Opus 5.5 defaults to "medium"; set it explicitly. Q&A over a handful of tools does well here.
    anthropic_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_max_tokens: int = 16000
    # Server-side refusal fallback (beta). "default" routes by refusal category; "" disables it.
    anthropic_fallbacks: Literal["default", ""] = "default"
    max_tool_turns: int = 8

    # --- Secrets --------------------------------------------------------------------------
    # Local dev may export ANTHROPIC_API_KEY directly. In Azure, leave it unset and set
    # AZURE_KEY_VAULT_NAME + AZURE_KEY_VAULT_SECRET_NAME (names match the repo .env.example).
    azure_key_vault_name: str | None = None
    azure_key_vault_secret_name: str = "anthropic-api-key"

    # --- Power BI / Fabric semantic model -------------------------------------------------
    powerbi_mode: Literal["live", "fixture"] = "live"
    fabric_workspace_id: str = ""          # Power BI "groupId"
    powerbi_dataset_id: str = ""           # semantic model (dataset) id of "NVIDIA Financials"
    powerbi_api_base: str = "https://api.powerbi.com/v1.0/myorg"
    powerbi_scope: str = "https://analysis.windows.net/powerbi/api/.default"
    # executeQueries allows 120 query requests per minute per user (service principal included).
    powerbi_queries_per_minute: int = 100
    powerbi_timeout_s: float = 60.0
    allow_freeform_dax: bool = False       # expose run_dax_query to Claude (read-only, capped)
    fixture_path: Path = Path(__file__).resolve().parent / "fixtures" / "fy2026.json"

    # --- Semantic catalog (retrieval index) -----------------------------------------------
    dax_dir: Path = REPO_ROOT / "dax"

    # --- Web / abuse controls -------------------------------------------------------------
    # The visual runs inside Power BI and cannot hold a secret (private visuals cannot use the
    # Power BI AAD token API), so the endpoint is protected by origin allow-list + rate limits
    # + a daily request budget. CHAT_API_TOKEN adds a shared token for non-public deployments.
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])
    chat_api_token: str | None = None
    trust_proxy_headers: bool = False      # true behind Azure Container Apps / App Service ingress
    rate_limit_per_minute: int = 6
    daily_request_budget: int = 500
    max_question_chars: int = 2000
    max_history_turns: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
