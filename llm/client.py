from typing import Any, AsyncGenerator
from openai import AsyncOpenAI
import os
from openai.types.chat import ChatCompletion
from .response import EventType, StreamEvent, TextDelta, TokenUsage

class LLMClient:
    def __init__(self) -> None:
       self._client: AsyncOpenAI | None = None

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key = os.environ.get("AI_API_KEY"),
                base_url = os.environ.get("AI_BASE_URL")
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        stream: bool = True
    ) -> AsyncGenerator:
        # if stream:
        #     yield await self._stream_response()
        # else:
            client = self.get_client();
            kwargs = {
                "model":"cohere/north-mini-code:free",
                "messages": messages,
                "stream": stream
            }
            event = await self._non_stream_response(client, kwargs)
            yield event

    async def _stream_response(self):
        return

    async def _non_stream_response(self, client: AsyncOpenAI, kwargs:dict[str, Any]) -> StreamEvent:
        response: ChatCompletion = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        text_delta = None
        usage = None
        if message.content:
            text_delta = TextDelta(
                content = message.content
            )
        if response.usage:
            usage = TokenUsage(
                prompt_tokens = response.usage.prompt_tokens,
                total_tokens = response.usage.total_tokens,
                completion_tokens = response.usage.completion_tokens,
                cached_tokens = response.usage.prompt_tokens_details.cached_tokens
            )
        return StreamEvent(
            type = EventType.MESSAGE_COMPLETE,
            token_usage = usage,
            text_delta = text_delta,
            finish_reason = choice.finish_reason 
        )
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
