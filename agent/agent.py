from __future__ import annotations
from pathlib import Path
from typing import AsyncGenerator
from context.manager import ContextManager
from llm.client import StreamEventType
from llm.client import LLMClient
from agent.event import AgentEvent, AgentEventType
from tools.buffer import ToolCallBuffer
from tools.registry import create_default_registry
from tools.result import ToolResultMessage
from tools.toolCall import ToolCall

class Agent:
    def __init__(self) -> None:
        self.client = LLMClient()
        self.context_manager = ContextManager()
        self.tool_registry = create_default_registry()

    def run(self, message: str)->AsyncGenerator[AgentEvent]:
        return self.start(message)

    async def start(self, message: str)->AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message);
        self.context_manager.add_user_message(message)
        final_response: str | None = None
        try:
            async for event in self._agentic_loop():
                if event.type == AgentEventType.TEXT_COMPLETE:
                    final_response = event.data.get("content")
                yield event
            yield AgentEvent.agent_end(final_response)
        except Exception as e:
            yield AgentEvent.agent_error("Internal Agent Error", str(e))

    async def _agentic_loop(self)-> AsyncGenerator[AgentEvent]: 
        response_text = ""
        tool_schemas = self.tool_registry.get_schemas()
        tool_calls_buffer = ToolCallBuffer()
        async for event in self.client.chat_completion(
            self.context_manager.get_messages(),
            tools=tool_schemas if tool_schemas else None,
            stream=True
        ):
            if event.type == StreamEventType.TEXT_DELTA and event.text_delta.content:
                content = event.text_delta.content;
                response_text+=content;
                yield AgentEvent.text_delta(content)
            if event.type == StreamEventType.TOOLS_Delta and event.tool_delta:
                tool_calls_buffer.chunk(event.tool_delta)
            if event.type == StreamEventType.ERROR:
                error = event.error
                yield AgentEvent.agent_error(error or "Unknown error occured")
            if event.type == StreamEventType.MESSAGE_COMPLETE:
                self.context_manager.add_assistant_message(response_text)
                yield AgentEvent.text_complete(response_text)
            if event.finish_reason == "tool_calls":
                tool_calls = tool_calls_buffer.to_tool_calls()
                tool_calls_buffer.clear()
                async for tool_event in self._call_tools(tool_calls):
                    yield tool_event

    async def _call_tools(self, tool_calls: list[ToolCall])->AsyncGenerator[AgentEvent]:
        tool_call_results: list[ToolResultMessage] = []
        for tool_call in tool_calls:
            name = tool_call.name;
            tool = self.tool_registry.get(name);
            if not tool:
               print("tool not found", tool)
            else:
                yield AgentEvent.tool_call_start(
                    name = tool.name,
                    call_id = tool_call.call_id,
                    params = tool_call.params,
                    tool_kind = tool.kind.value.lower()
                )
                result = await self.tool_registry.invoke(
                    name = tool.name,
                    params = tool_call.params,
                    cwd = Path.cwd()
                )
                yield AgentEvent.tool_call_complete(
                    name = tool.name,
                    call_id = tool_call.call_id,
                    result=result,
                    tool_kind = tool.kind.value.lower()
                )
                tool_call_results.append(ToolResultMessage(
                    tool_call_id=tool_call.call_id,
                    content=result.to_model_output(),
                    is_error = not result.success
                ))
        for tool_call_result in tool_call_results:
            self.context_manager.add_tool_message(
                tool_call_result.content,
                tool_call_result.tool_call_id
            )


    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        if self.client:
            await self.client.close()
            self.client = None