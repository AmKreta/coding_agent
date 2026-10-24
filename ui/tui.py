from rich.console import Console
from rich.rule import Rule
from rich.text import Text


class TUI:
    def __init__(self, console: Console) -> None:
        self._console = console
        self._assistant_stream_open = False

    def begin_assistant(self) -> None:
        self._assistant_stream_open = True
        self._console.print()
        self._console.print(Rule(Text("Assistent", style="assistant")))

    

    def stream_assistant_delta(self, content:str):
        self._console.print(content, end="", markup=False)

    def end_assistant(self) -> None:
        if self._assistant_stream_open:
            self._console.print()
        self._assistant_stream_open = False
