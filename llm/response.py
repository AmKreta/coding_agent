from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class TextDelta:
    content: str = ""

    def __str__(self) -> str:
        return self.content

@dataclass
class ToolCallDelta:
    id: str | None
    index: int | None
    name: str | None
    arguments_delta: str | None

class StreamEventType(str, Enum):
    TEXT_DELTA = "text_delta"
    TOOLS_Delta = "tools_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"

@dataclass
class TokenUsage:
    prompt_tokens:int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0

    def __add__(self, other: TokenUsage):
        return TokenUsage(
            prompt_tokens = self.prompt_tokens + other.prompt_tokens,
            completion_tokens = self.completion_tokens + other.completion_tokens,
            total_tokens = self.total_tokens + other.total_tokens,
            cached_tokens = self.cached_tokens + other.cached_tokens
        )


@dataclass
class StreamEvent:
    type: StreamEventType
    text_delta: TextDelta | None = None
    tool_delta: list[ToolCallDelta] | None = None
    error: str | None = None
    finish_reason: str | None = None
    token_usage: TokenUsage | None = None
