"""FastAPI service: POST /api/chat streams a grounded answer as Server-Sent Events.

Run locally:
    cd chatbot/backend && uvicorn app.main:app --reload
"""
from __future__ import annotations

import json
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agent import Agent, ChatRequest
from .catalog import Catalog
from .config import Settings, get_settings
from .keyvault import resolve_anthropic_api_key
from .powerbi import build_backend
from .tools import ToolExecutor

STATIC_DIR = Path(__file__).resolve().parent / "static"


class AbuseGuard:
    """Per-client sliding-window rate limit + a global daily request budget (single replica).

    For several replicas, move both counters to a shared store (e.g. Azure Cache for Redis).
    """

    def __init__(self, per_minute: int, daily_budget: int):
        self.per_minute = per_minute
        self.daily_budget = daily_budget
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._day = date.today()
        self._used_today = 0

    def check(self, client_id: str) -> None:
        now = time.monotonic()
        if date.today() != self._day:
            self._day, self._used_today = date.today(), 0
        if self._used_today >= self.daily_budget:
            raise HTTPException(429, "Daily question budget reached. Try again tomorrow.")
        q = self._hits[client_id]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            raise HTTPException(429, "Too many questions - wait a minute.")
        q.append(now)
        self._used_today += 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    catalog = Catalog.from_repo(settings.dax_dir)
    backend = build_backend(settings)
    api_key = await resolve_anthropic_api_key(settings)
    client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else anthropic.AsyncAnthropic()
    app.state.agent = Agent(client, catalog, ToolExecutor(catalog, backend, settings.allow_freeform_dax), settings)
    app.state.guard = AbuseGuard(settings.rate_limit_per_minute, settings.daily_request_budget)
    app.state.catalog = catalog
    try:
        yield
    finally:
        await backend.aclose()
        await client.close()


app = FastAPI(title="NVIDIA Balance Sheet - Claude analyst", lifespan=lifespan)
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization"],
)


def client_id(request: Request) -> str:
    # Behind Azure Container Apps / App Service the client IP is the first X-Forwarded-For hop.
    # Only trust that header when TRUST_PROXY_HEADERS=true, or clients could spoof it to dodge limits.
    if get_settings().trust_proxy_headers:
        fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if fwd:
            return fwd
    return request.client.host if request.client else "unknown"


def require_token(request: Request, settings: Settings = Depends(get_settings)) -> None:
    if not settings.chat_api_token:
        return
    auth = request.headers.get("authorization", "")
    if not secrets.compare_digest(auth, f"Bearer {settings.chat_api_token}"):
        raise HTTPException(401, "Missing or invalid token")


@app.get("/api/health")
async def health(request: Request) -> dict:
    s = get_settings()
    return {"status": "ok", "model": s.anthropic_model, "powerbi_mode": s.powerbi_mode,
            "measures": len(request.app.state.catalog.measures)}


@app.post("/api/chat", dependencies=[Depends(require_token)])
async def chat(req: ChatRequest, request: Request) -> StreamingResponse:
    request.app.state.guard.check(client_id(request))
    agent: Agent = request.app.state.agent

    async def events():
        try:
            async for event in agent.run(req):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception:  # never leak internals to the browser
            yield f"data: {json.dumps({'type': 'error', 'message': 'Unexpected server error.'})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
