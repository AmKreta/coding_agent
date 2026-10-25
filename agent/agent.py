from __future__ import annotations
from typing import Any, AsyncGenerator
from context.manager import ContextManager
from llm.client import StreamEventType
from llm.client import LLMClient
from agent.event import AgentEvent, AgentEventType
from tools.registry import create_default_registry

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
        async for event in self.client.chat_completion(
            self.context_manager.get_messages(),
            tools=tool_schemas if tool_schemas else None,
            stream=True
        ):
            if event.type == StreamEventType.TEXT_DELTA and event.text_delta.content:
                content = event.text_delta.content;
                response_text+=content;
                yield AgentEvent.text_delta(content)
            if event.type == StreamEventType.ERROR:
                error = event.error
                yield AgentEvent.agent_error(error or "Unknown error occured")
            if event.type == StreamEventType.MESSAGE_COMPLETE:
                self.context_manager.add_assistant_message(response_text)
                yield AgentEvent.text_complete(response_text)

    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        if self.client:
            await self.client.close()
            self.client = None