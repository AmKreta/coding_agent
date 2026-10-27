import json
import logging
from llm.response import ToolCallDelta
from tools.toolCall import ToolCall

logger = logging.getLogger(__name__)

class ToolCallBuffer:
    def __init__(self) -> None:
        self.tool_calls_bufffer: dict[int, ToolCallDelta] = {}

    def chunk(self, chunks: list[ToolCallDelta]):
        for chunk in chunks:
            if chunk.index not in self.tool_calls_bufffer:
                self.tool_calls_bufffer[chunk.index] = ToolCallDelta(
                    index = chunk.index,
                    id = chunk.id,
                    name = chunk.name,
                    arguments_delta=""
                )
            tool_call_buffer: ToolCallDelta = self.tool_calls_bufffer[chunk.index]
            if chunk.id:
                tool_call_buffer.id = chunk.id
            if chunk.name:
                tool_call_buffer.name = chunk.name
            tool_call_buffer.arguments_delta += chunk.arguments_delta or ""

    
    def clear(self):
        self.tool_calls_bufffer = {}

    def to_tool_calls(self) -> list[ToolCall]:
        res: list[ToolCall] = []
        for _, tool_call_buffer in self.tool_calls_bufffer.items():
            try:
                params = json.loads(tool_call_buffer.arguments_delta or "{}")
                res.append(ToolCall(
                    name = tool_call_buffer.name,
                    params = params,
                    call_id= tool_call_buffer.id
                ))
            except Exception as e:
                logging.error(f"unable to parse tool_call {tool_call_buffer}. {e}")
        return res

