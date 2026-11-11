"""Claude tool-use loop over the semantic model, streamed as events for the chat UI.

Event stream (each item is a dict sent as one SSE `data:` line):
    {"type": "status", "text": "..."}                     tool progress for the UI
    {"type": "text", "text": "..."}                       answer tokens
    {"type": "evidence", "items": [...]}                  SEC facts retrieved this turn
    {"type": "done", "grounding": {...}, "usage": {...}, "model": "..."}
    {"type": "error", "message": "..."}

Design notes (Claude API docs, Python SDK 2.x):
- Manual async loop with client.beta.messages.stream (beta namespace for server-side refusal
  fallbacks: betas=["server-side-fallback-2026-07-01"], fallbacks="default").
- Client tools set eager_input_streaming; inputs are validated with pydantic before running, a
  turn that stops on max_tokens / refusal never runs its tools, and a ValueError from the stream
  iterator (unparseable tool JSON) re-issues the turn, bounded.
- System prompt + catalog + tools are byte-stable and cached (cache_control on the system block).
- Report context (slicer state from the visual) arrives as a mid-conversation system message, so
  it never edits the cached prefix and stays on the operator channel.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import anthropic
from pydantic import BaseModel, Field

from .catalog import Catalog
from .config import Settings
from .grounding import check_grounding
from .tools import ToolExecutor, ToolLedger, tool_definitions

FALLBACK_BETA = "server-side-fallback-2026-07-01"

SYSTEM_PROMPT = """You are the analyst assistant inside the Power BI report "NVIDIA - Behind the Balance Sheet".
You answer questions about NVIDIA's financial position using ONLY the "NVIDIA Financials" semantic model
(SEC EDGAR companyfacts -> Fabric gold tables -> Direct Lake model), which you reach through tools.

How to work
1. Find the right measures with search_semantic_model (or the catalog below), then get numbers with
   query_measures or get_trend. For "where does this number come from", call get_sec_evidence.
2. Every figure you state must come from a tool result in this conversation. Do not compute new
   figures yourself (no subtracting, averaging or growth math): use the model's measures instead
   (for example Revenue YoY %, Net Income QoQ %, TTM Revenue, Revenue CAGR 3Y). If no measure answers
   the question, say what is missing.
3. If a value comes back null/BLANK, say it is not available and why if the catalog explains it
   (for example Marketable Securities is not tagged by NVIDIA from FY2026, so Quick Ratio and
   Net Cash are blank; Net Cash (Cash Only) is the conservative alternative).
4. Use fiscal labels only (Q2 FY2027, FY2026) - never calendar years. Quote the Period Label for
   the period you report. NVIDIA's fiscal year ends on the last Sunday of January.
5. Cash-flow figures on a 10-Q are year-to-date; say so when you report them.
6. Abstain when the data cannot answer: say so plainly instead of guessing. You are not an equity
   analyst: no investment advice, price targets or forecasts.

How to answer
- Lead with the answer in one or two sentences, then the supporting figures as a short list.
- Format money as $206.8B / $8,468M, ratios as 58.3% or 2.40x, matching the measure format.
- When you used get_sec_evidence, end with "Sources:" and one line per evidence_id you relied on.
- Keep it under ~180 words unless the user asks for more detail.

Data notes: companyfacts is a structured XBRL extract, not the full 10-K/10-Q narrative. Values are
as originally reported in each period's own filing.

# Semantic model catalog
"""


class ChatTurn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=8000)


class ReportContext(BaseModel):
    fiscal_year: int | None = Field(default=None, ge=2005, le=2100)
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    page: str | None = Field(default=None, max_length=80)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    report_context: ReportContext | None = None


def build_system(catalog: Catalog) -> list[dict]:
    return [{
        "type": "text",
        "text": SYSTEM_PROMPT + catalog.prompt_digest(),
        "cache_control": {"type": "ephemeral"},
    }]


def context_note(ctx: ReportContext | None) -> str | None:
    if ctx is None or (ctx.fiscal_year is None and not ctx.page):
        return None
    parts = []
    if ctx.page:
        parts.append(f"The user is on report page '{ctx.page}'.")
    if ctx.fiscal_year is not None:
        period = f"Q{ctx.fiscal_quarter} FY{ctx.fiscal_year}" if ctx.fiscal_quarter else f"FY{ctx.fiscal_year}"
        parts.append(
            f"The report's slicers are set to {period}. Unless the user names another period, answer for "
            f"fiscal_year={ctx.fiscal_year}, fiscal_quarter={ctx.fiscal_quarter if ctx.fiscal_quarter else 'null'}."
        )
    return "Report context: " + " ".join(parts)


def build_messages(req: ChatRequest, max_history_turns: int) -> list[dict]:
    history = req.history[-2 * max_history_turns:]
    # The API requires the first message to be from the user.
    while history and history[0].role != "user":
        history = history[1:]
    messages: list[dict] = [{"role": t.role, "content": t.content} for t in history]
    messages.append({"role": "user", "content": req.question})
    note = context_note(req.report_context)
    if note:
        # Mid-conversation system message: follows a user message and is the last entry.
        messages.append({"role": "system", "content": note})
    return messages


class Agent:
    def __init__(self, client: anthropic.AsyncAnthropic, catalog: Catalog, executor: ToolExecutor,
                 settings: Settings):
        self.client = client
        self.catalog = catalog
        self.executor = executor
        self.s = settings
        self.system = build_system(catalog)
        self.tools = tool_definitions(settings.allow_freeform_dax)

    def _params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.s.anthropic_model,
            "max_tokens": self.s.anthropic_max_tokens,
            "system": self.system,
            "tools": self.tools,
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": self.s.anthropic_effort},
        }
        if self.s.anthropic_fallbacks:
            params["betas"] = [FALLBACK_BETA]
            params["fallbacks"] = self.s.anthropic_fallbacks
        return params

    async def run(self, req: ChatRequest) -> AsyncIterator[dict]:
        messages = build_messages(req, self.s.max_history_turns)
        ledger = ToolLedger()
        answer_parts: list[str] = []
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
                 "cache_creation_input_tokens": 0}
        model_used = self.s.anthropic_model
        json_retries = 0
        turns = 0

        while True:
            turns += 1
            if turns > self.s.max_tool_turns + 1:
                yield {"type": "error", "message": "Stopped after too many tool steps. Try a narrower question."}
                return
            turn_text: list[str] = []
            try:
                async with self.client.beta.messages.stream(**self._params(), messages=messages) as stream:
                    async for event in stream:
                        if event.type == "text":
                            turn_text.append(event.text)
                            yield {"type": "text", "text": event.text}
                    response = await stream.get_final_message()
                json_retries = 0
            except ValueError:
                # Tool input JSON the SDK could not parse at all: no tool_use_id to answer, so re-issue.
                json_retries += 1
                if json_retries > 2:
                    yield {"type": "error", "message": "The model produced an unreadable tool call. Please retry."}
                    return
                continue
            except anthropic.RateLimitError:
                yield {"type": "error", "message": "The assistant is busy (rate limited). Try again in a minute."}
                return
            except anthropic.APIStatusError as e:
                yield {"type": "error", "message": f"Claude API error ({e.status_code})."}
                return
            except anthropic.APIConnectionError:
                yield {"type": "error", "message": "Could not reach the Claude API."}
                return

            answer_parts.extend(turn_text)
            model_used = response.model
            u = response.usage
            for k in usage:
                usage[k] += getattr(u, k, 0) or 0

            if response.stop_reason == "refusal":
                yield {"type": "error", "message": "The assistant declined this request."}
                return
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                break
            if response.stop_reason == "max_tokens":
                yield {"type": "error", "message": "The answer was cut off (max_tokens). Ask a narrower question."}
                return

            for b in tool_uses:
                yield {"type": "status", "text": _status_text(b.name, b.input)}
            results = await asyncio.gather(*(self.executor.run(b.name, b.input, ledger) for b in tool_uses))
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": content, "is_error": is_error}
                for b, (content, is_error) in zip(tool_uses, results)
            ]})

        if ledger.evidence:
            yield {"type": "evidence", "items": list(ledger.evidence.values())}
        yield {
            "type": "done",
            "grounding": check_grounding("".join(answer_parts), ledger.numbers),
            "usage": usage,
            "model": model_used,
            "dax_queries": len(ledger.queries),
        }


def _status_text(name: str, tool_input: Any) -> str:
    inp = tool_input if isinstance(tool_input, dict) else {}
    if name == "search_semantic_model":
        return f"Searching the model for “{str(inp.get('query', ''))[:60]}”"
    if name == "query_measures":
        return "Querying " + ", ".join(map(str, inp.get("measures", [])[:4]))
    if name == "get_trend":
        return f"Building {inp.get('grain', '')} trend of {inp.get('measure', '')}"
    if name == "get_sec_evidence":
        return "Fetching SEC evidence for " + ", ".join(map(str, inp.get("concepts", [])[:4]))
    if name == "run_dax_query":
        return "Running a DAX query"
    return json.dumps(name)
