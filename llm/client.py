import asyncio
from typing import Any, AsyncGenerator
from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
import os
from openai.types.chat import ChatCompletion
from .response import StreamEventType, StreamEvent, TextDelta, TokenUsage

class LLMClient:
    def __init__(self) -> None:
       self._client: AsyncOpenAI | None = None
       self._maxRetries = 3;

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
    ) -> AsyncGenerator[StreamEvent, None]:
        client = self.get_client();
        kwargs = {
            "model":"cohere/north-mini-code:free",
            "messages": messages,
            "stream": stream
        }
        for attempt in range(self._maxRetries+1):
            try:
                if stream:
                    ev = self._stream_response(client, kwargs)
                    async for chunk in ev:
                        yield chunk
                else:
                    event = await self._non_stream_response(client, kwargs)
                    yield event
                return
            except (APIConnectionError, APIError, RateLimitError, Exception) as e:
                if attempt < self._maxRetries:
                    wait_time = 2**attempt
                    await asyncio.sleep(wait_time)
                else:
                    yield StreamEvent(
                        type = StreamEventType.ERROR,
                        error = str(getattr(e, "body", None) or e)
                    )


    async def _stream_response(self, client: AsyncOpenAI, kwargs:dict[str, Any])->AsyncGenerator[StreamEvent, None]:
        response: ChatCompletion = await client.chat.completions.create(**kwargs);
        usage: TokenUsage | None = None
        async for chunk in response:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if hasattr(chunk, "usage") and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens = chunk.usage.prompt_tokens,
                    total_tokens = chunk.usage.total_tokens,
                    completion_tokens = chunk.usage.completion_tokens,
                    cached_tokens = chunk.usage.prompt_tokens_details.cached_tokens
                )
                
            yield StreamEvent(
                type = StreamEventType.TEXT_DELTA if not choice.finish_reason else StreamEventType.MESSAGE_COMPLETE,
                token_usage = usage,
                text_delta = TextDelta(content=choice.delta.content),
                finish_reason = choice.finish_reason
            )
        

    async def _non_stream_response(self, client: AsyncOpenAI, kwargs:dict[str, Any]) -> StreamEvent:
        response: ChatCompletion = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        text_delta: TextDelta | None = None
        usage: TokenUsage | None = None
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
            type = StreamEventType.MESSAGE_COMPLETE,
            token_usage = usage,
            text_delta = text_delta,
            finish_reason = choice.finish_reason 
        )
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
