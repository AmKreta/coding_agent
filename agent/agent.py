from __future__ import annotations
from typing import Any, AsyncGenerator
from llm.client import StreamEventType
from llm.client import LLMClient
from agent.event import AgentEvent, AgentEventType

class Agent:
    def __init__(self) -> None:
        self.client = LLMClient()

    def run(self, message: str)->AsyncGenerator[AgentEvent]:
        return self.start(message)

    async def start(self, message: str)->AsyncGenerator[AgentEvent]:
        yield AgentEvent.agent_start(message);
        final_response: str | None = None
        try:
            async for event in self._agentic_loop(message):
                if event.type == AgentEventType.TEXT_COMPLETE:
                    final_response = event.data.get("content")
                yield event
            yield AgentEvent.agent_end(final_response)
        except Exception as e:
            yield AgentEvent.agent_error("Internal Agent Error", str(e))

    async def _agentic_loop(self, message: str)-> AsyncGenerator[AgentEvent]: 
        messages: list[dict[str, Any]] = [{"role" : "user", "content":message}]
        response_text = ""
        async for event in self.client.chat_completion(messages):
            if event.type == StreamEventType.TEXT_DELTA and event.text_delta.content:
                content = event.text_delta.content;
                response_text+=content;
                yield AgentEvent.text_delta(content)
            if event.type == StreamEventType.ERROR:
                error = event.error
                yield AgentEvent.agent_error(error or "Unknown error occured")
            if event.type == StreamEventType.MESSAGE_COMPLETE:
                yield AgentEvent.text_complete(response_text)

    async def __aenter__(self) -> Agent:
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        if self.client:
            await self.client.close()
            self.client = None