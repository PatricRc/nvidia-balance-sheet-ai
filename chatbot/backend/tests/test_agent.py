from app.agent import Agent, ChatRequest, build_messages
from app.tools import ToolExecutor

from .fakes import FakeAnthropic, text_turn, tool_turn


def make_agent(catalog, backend, settings, turns):
    client = FakeAnthropic(turns)
    return Agent(client, catalog, ToolExecutor(catalog, backend, False), settings), client


async def collect(agent, req):
    return [e async for e in agent.run(req)]


async def test_tool_loop_answers_from_model_and_verifies(catalog, backend, settings):
    agent, client = make_agent(catalog, backend, settings, [
        tool_turn(("query_measures", {"measures": ["Total Assets"], "periods": [{"fiscal_year": 2026, "fiscal_quarter": None}]})),
        text_turn("Total assets were $206.8B in FY2026."),
    ])
    events = await collect(agent, ChatRequest(question="What were total assets in FY2026?"))
    text = "".join(e["text"] for e in events if e["type"] == "text")
    done = events[-1]
    assert "$206.8B" in text
    assert done["type"] == "done" and done["grounding"]["status"] == "verified" and done["dax_queries"] == 1
    # second request carries the assistant tool_use turn and the matching tool_result
    second = client.requests[1]["messages"]
    assert second[-1]["content"][0]["tool_use_id"] == "toolu_0" and second[-1]["content"][0]["is_error"] is False
    # request shape: Opus 5.5, adaptive thinking, explicit effort, fallbacks beta, cached system
    p = client.requests[0]
    assert p["model"] == "claude-opus-5-5" and p["thinking"] == {"type": "adaptive"}
    assert p["output_config"] == {"effort": "medium"} and p["fallbacks"] == "default"
    assert p["system"][0]["cache_control"] == {"type": "ephemeral"}


async def test_invented_number_is_flagged(catalog, backend, settings):
    agent, _ = make_agent(catalog, backend, settings, [text_turn("Assets are $999.9B.")])
    events = await collect(agent, ChatRequest(question="assets?"))
    assert events[-1]["grounding"]["status"] == "unverified"


async def test_refusal_and_truncated_tool_calls_never_run_tools(catalog, backend, settings):
    refused = tool_turn(("query_measures", {"measures": ["Cash"], "periods": []}))
    refused["stop_reason"] = "refusal"
    agent, _ = make_agent(catalog, backend, settings, [refused])
    events = await collect(agent, ChatRequest(question="x"))
    assert events[-1]["type"] == "error" and backend.queries == []

    truncated = tool_turn(("query_measures", {"measures": ["Cash"], "periods": []}))
    truncated["stop_reason"] = "max_tokens"
    agent, _ = make_agent(catalog, backend, settings, [truncated])
    events = await collect(agent, ChatRequest(question="x"))
    assert events[-1]["type"] == "error" and backend.queries == []


async def test_unparseable_tool_json_reissues_turn(catalog, backend, settings):
    agent, client = make_agent(catalog, backend, settings, [
        {"raise": ValueError("bad json"), "text": "", "content": [], "stop_reason": "tool_use"},
        text_turn("No figures here."),
    ])
    events = await collect(agent, ChatRequest(question="x"))
    assert events[-1]["type"] == "done" and len(client.requests) == 2


def test_report_context_is_a_trailing_system_message():
    req = ChatRequest(question="How liquid is it?", history=[{"role": "assistant", "content": "hi"}],
                      report_context={"fiscal_year": 2027, "fiscal_quarter": 2, "page": "Liquidity"})
    msgs = build_messages(req, max_history_turns=8)
    assert msgs[0]["role"] == "user"  # leading assistant turn dropped
    assert msgs[-1]["role"] == "system" and "Q2 FY2027" in msgs[-1]["content"]
