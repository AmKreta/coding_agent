from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from llm.response import TokenUsage
from tools.result import ToolResult


class AgentEventType(str, Enum):
    # agent lifecycle
    AGENT_START = "AGENT_START"
    AGENT_END = "AGENT_END"
    AGENT_ERROR = "AGENT_ERROR"

    #text response
    TEXT_DELTA = "TEXT_DELTA"
    TEXT_COMPLETE = "TEXT_COMPLETE"

    #tools
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_COMPLETE = "TOOL_CALL_COMPLETE"

@dataclass
class AgentEvent:
    type: AgentEventType
    data:dict[str, Any] = field(default_factory=dict)

    @classmethod
    def agent_start(cls, message: str) -> AgentEvent :
        return cls(
            type = AgentEventType.AGENT_START,
            data = {"message": message}
        )
    
    @classmethod
    def agent_end(
        cls, 
        response: str | None = None, 
        usage: TokenUsage | None = None
    ) -> AgentEvent :
        return cls(
            type = AgentEventType.AGENT_END,
            data = {"response": response, "usage": usage}
        )

    @classmethod
    def agent_error(cls, error: str, details: str | Any = None) -> AgentEvent :
        return cls(
            type = AgentEventType.AGENT_ERROR,
            data = {"error": error, "details": details}
        )

    @classmethod
    def text_delta(cls, content: str) -> AgentEvent :
        return cls(
            type = AgentEventType.TEXT_DELTA,
            data = {"content": content}
        )
    
    @classmethod
    def text_complete(cls, content: str) -> AgentEvent :
        return cls(
            type = AgentEventType.TEXT_COMPLETE,
            data = {"content": content}
        )
    
    @classmethod
    def tool_call_start(cls, name: str, call_id: str, params: dict[str, Any], tool_kind: str | None = None) -> AgentEvent:
        return cls(
            type=AgentEventType.TOOL_CALL_START,
            data= {
                "name": name,
                "tool_kind": tool_kind,
                "call_id":call_id,
                "params": params
            }
        )

    @classmethod
    def tool_call_complete(cls, name: str, call_id: str, result: ToolResult, tool_kind: str | None = None)->AgentEvent:
        return cls(
            type = AgentEventType.TOOL_CALL_COMPLETE,
            data = {
                "call_id": call_id,
                "name": name,
                "tool_kind": tool_kind,
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "metadata": result.metadata,
                "truncated": result.truncated
            }
        )