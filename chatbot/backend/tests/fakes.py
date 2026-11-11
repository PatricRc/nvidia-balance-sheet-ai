"""Fake Anthropic streaming client: replays scripted turns, records every request."""
from __future__ import annotations

from types import SimpleNamespace


def text_turn(text: str) -> dict:
    return {"text": text, "content": [SimpleNamespace(type="text", text=text)], "stop_reason": "end_turn"}


def tool_turn(*calls: tuple[str, dict], text: str = "") -> dict:
    blocks = [SimpleNamespace(type="text", text=text)] if text else []
    blocks += [SimpleNamespace(type="tool_use", id=f"toolu_{i}", name=n, input=inp) for i, (n, inp) in enumerate(calls)]
    return {"text": text, "content": blocks, "stop_reason": "tool_use"}


class _Stream:
    def __init__(self, turn: dict):
        self.turn = turn

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        async def gen():
            if self.turn.get("raise"):
                raise self.turn["raise"]
            for word in self.turn["text"].split(" ") if self.turn["text"] else []:
                yield SimpleNamespace(type="text", text=word + " ")
        return gen()

    async def get_final_message(self):
        return SimpleNamespace(
            content=self.turn["content"], stop_reason=self.turn["stop_reason"], model="claude-opus-5-5",
            usage=SimpleNamespace(input_tokens=100, output_tokens=20, cache_read_input_tokens=80,
                                  cache_creation_input_tokens=0),
        )


class FakeAnthropic:
    def __init__(self, turns: list[dict]):
        self.turns = list(turns)
        self.requests: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        # snapshot messages: the agent keeps appending to the same list
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return _Stream(self.turns.pop(0))

    async def close(self):
        return None
