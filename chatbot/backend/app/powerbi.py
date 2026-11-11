"""Read-only access to the NVIDIA Financials semantic model through the Power BI REST API.

Endpoint (official docs, "Datasets - Execute Queries In Group"):
    POST {api}/groups/{groupId}/datasets/{datasetId}/executeQueries
    body: {"queries": [{"query": "<DAX>"}], "serializerSettings": {"includeNulls": true}}

Documented limits this client respects:
- one query and one result table per call
- 100,000 rows or 1,000,000 values per query, 15 MB per query
- 120 query requests per minute per user (service principals included)
- DAX only: INFO functions and DMVs are not supported -> the schema catalog comes from the repo
- Requires tenant setting "Dataset Execute Queries REST API", Read + Build on the model, and
  "Allow service principals to use Power BI APIs" for a service principal. Scope
  Dataset.Read.All is enough; the token audience is https://analysis.windows.net/powerbi/api.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Protocol

import httpx

from .config import Settings


class DaxError(RuntimeError):
    """The query reached the model but failed (bad DAX, missing measure, limits)."""


class QueryBackend(Protocol):
    async def execute_dax(self, query: str) -> list[dict[str, Any]]: ...
    async def aclose(self) -> None: ...


class _SlidingWindowLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._calls and now - self._calls[0] > 60:
                    self._calls.popleft()
                if len(self._calls) < self.per_minute:
                    self._calls.append(now)
                    return
                await asyncio.sleep(60 - (now - self._calls[0]) + 0.05)


def clean_column_name(name: str) -> str:
    """executeQueries returns 'Table[Column]' for model columns and '[Name]' for query columns."""
    if name.endswith("]") and "[" in name:
        return name[name.index("[") + 1 : -1]
    return name


class PowerBIClient:
    """Live backend: Entra ID token from DefaultAzureCredential, then executeQueries."""

    def __init__(self, settings: Settings):
        if not (settings.fabric_workspace_id and settings.powerbi_dataset_id):
            raise ValueError("FABRIC_WORKSPACE_ID and POWERBI_DATASET_ID are required in live mode")
        from azure.identity.aio import DefaultAzureCredential

        self._s = settings
        self._credential = DefaultAzureCredential()
        self._token: tuple[str, float] | None = None
        self._limiter = _SlidingWindowLimiter(settings.powerbi_queries_per_minute)
        self._http = httpx.AsyncClient(timeout=settings.powerbi_timeout_s)
        self._url = (
            f"{settings.powerbi_api_base}/groups/{settings.fabric_workspace_id}"
            f"/datasets/{settings.powerbi_dataset_id}/executeQueries"
        )

    async def _bearer(self) -> str:
        if self._token is None or self._token[1] - time.time() < 300:
            tok = await self._credential.get_token(self._s.powerbi_scope)
            self._token = (tok.token, float(tok.expires_on))
        return self._token[0]

    async def execute_dax(self, query: str) -> list[dict[str, Any]]:
        await self._limiter.acquire()
        resp = await self._http.post(
            self._url,
            headers={"Authorization": f"Bearer {await self._bearer()}"},
            json={"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}},
        )
        if resp.status_code == 400:
            raise DaxError(_error_text(resp))
        resp.raise_for_status()
        body = resp.json()
        result = (body.get("results") or [{}])[0]
        if result.get("error"):
            raise DaxError(json.dumps(result["error"])[:800])
        table = (result.get("tables") or [{}])[0]
        if table.get("error"):  # e.g. row limit hit: HTTP 200 with a partial table + error
            raise DaxError(json.dumps(table["error"])[:800])
        return [{clean_column_name(k): v for k, v in row.items()} for row in table.get("rows", [])]

    async def aclose(self) -> None:
        await self._http.aclose()
        await self._credential.close()


def _error_text(resp: httpx.Response) -> str:
    try:
        err = resp.json().get("error", {})
        details = err.get("pbi.error", {}).get("details", [])
        msg = "; ".join(d.get("detail", {}).get("value", "") for d in details) or err.get("message", "")
        return (msg or resp.text)[:800]
    except ValueError:
        return resp.text[:800]


class FixtureBackend:
    """Offline backend for UI work and tests: answers from a JSON file of canned query results.

    The file maps a short query signature to rows. Unknown queries return [] so the agent sees
    "no data" instead of invented numbers.
    """

    def __init__(self, path: Path):
        self._data: dict[str, list[dict[str, Any]]] = json.loads(path.read_text(encoding="utf-8"))
        self.queries: list[str] = []

    async def execute_dax(self, query: str) -> list[dict[str, Any]]:
        self.queries.append(query)
        for marker, rows in self._data.items():
            if marker in query:
                return rows
        return []

    async def aclose(self) -> None:
        return None


def build_backend(settings: Settings) -> QueryBackend:
    if settings.powerbi_mode == "fixture":
        return FixtureBackend(settings.fixture_path)
    return PowerBIClient(settings)
