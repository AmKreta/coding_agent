from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ToolResult:
    success: bool
    output: str;
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False

    @classmethod
    def error_result(cls, error: str, output: str = "", **kwargs: Any):
        return cls(
            success = False,
            output = output,
            error = error,
            **kwargs
        )
    
    @classmethod
    def success_result(cls, output: str = "", **kwargs: Any):
        return cls(
            success = True,
            output = output,
            **kwargs
        )

    def to_model_output(self) -> str:
        if self.success:
            return self.output
        else:
            return f"Error: {self.error}\n\n {self.output}"

@dataclass
class ToolResultMessage:
    tool_call_id: str
    content: str
    is_error: str

    def to_openai_message(self)->dict[str, Any]:
        return {
            "role" : "tool",
            "tool_call_id": self.tool_call_id,
            "content": self.content
        }