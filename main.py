from __future__ import annotations
import asyncio
import sys

from agent.agent import Agent
from dotenv import load_dotenv
import click
from agent.event import AgentEventType
from ui.console import get_console
from ui.tui import TUI

load_dotenv(dotenv_path = ".env")

class CLI:
    def __init__(self) -> None:
        self.agent: Agent| None = None
        self.console = get_console()
        self.tui = TUI(self.console)

    async def run_single(self, message: str):
       async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def _process_message(self, message: str):
        if not self.agent:
            return None
        assistant_streaming = False
        final_response: str | None = None
        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming = True
                self.tui.stream_assistant_delta(content);
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False;
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error");
                details = event.data.get("details")
                self.console.print(f"\n[error]Error:{error}[/error]")
                if details:
                    self.console.print(f"[muted]{details}[/muted]", markup=True)
        return final_response

@click.command()
@click.argument("prompt", required = False)
def main(prompt: str):
    cli = CLI()
    res = asyncio.run(cli.run_single(prompt))
    if res is None:
        sys.exit(1)

main()