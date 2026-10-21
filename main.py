from typing import Any
from llm.client import LLMClient
from asyncio import run
from dotenv import load_dotenv
from rich import print

load_dotenv(dotenv_path = ".env")

async def main():
    client= LLMClient()
    messages: list[dict[str, Any]] = [
        {
            "role" : "user",
            "content": "what's up"
        }
    ]
    async for event in client.chat_completion(messages):
        print(event)


run(main())