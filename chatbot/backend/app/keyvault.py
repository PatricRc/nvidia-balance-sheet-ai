"""Resolve the Anthropic API key without ever storing it in the repo, DAX, report or HTML.

Order: ANTHROPIC_API_KEY env var (local dev only) -> Azure Key Vault secret
(AZURE_KEY_VAULT_NAME / AZURE_KEY_VAULT_SECRET_NAME) read with DefaultAzureCredential.
"""
from __future__ import annotations

import os

from .config import Settings


async def resolve_anthropic_api_key(settings: Settings) -> str | None:
    """Return the key, or None to let the SDK resolve credentials itself (e.g. `ant auth login`)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return None  # the SDK reads it from the environment
    if not settings.azure_key_vault_name:
        return None

    from azure.identity.aio import DefaultAzureCredential
    from azure.keyvault.secrets.aio import SecretClient

    vault_url = f"https://{settings.azure_key_vault_name}.vault.azure.net"
    async with DefaultAzureCredential() as credential:
        async with SecretClient(vault_url=vault_url, credential=credential) as client:
            secret = await client.get_secret(settings.azure_key_vault_secret_name)
            return secret.value
