from __future__ import annotations
from pathlib import Path
import os
import re
from typing import Any
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from llm.tokenizer import truncate_text
from utils.path import display_path_rel_to_cwd


class TUI:
    def __init__(self, console: Console) -> None:
        self._console = console
        self._assistant_stream_open = False
        self.tool_call_arguments_record:dict[str, Any] = {}
        self.cwd = Path.cwd()
        self._max_block_tokens = 2000

    def begin_assistant(self) -> None:
        self._assistant_stream_open = True
        self._console.print()
        self._console.print(Rule(Text("Assistent", style="assistant")))

    def end_assistant(self)->None:
        if self._assistant_stream_open:
            self._console.print()
        self._assistant_stream_open = False

    def stream_assistant_delta(self, content:str):
        self._console.print(content, end="", markup="false")

    def _ordered_arguments(self, tool_name: str, args: dict[str, Any])->list[tuple]:
        _PREFERED_ORDER = {
            "read_file":["path", "offset", "limit"]
        }
        preferred_order = _PREFERED_ORDER.get(tool_name,[])
        ordered:list[tuple[str, any]] = []
        seen:set[str] = set([])
        for key in preferred_order:
            if key in args and key not in seen:
                ordered.append((key, args[key]))
                seen.add(key)
        remaining_keys = set(args.keys()) - seen
        ordered.extend((key, args[key]) for key in remaining_keys)
        return ordered
        


    def _render_args_table(self, tool_name:str, args: dict[str, Any])->Table:
        table = Table.grid(padding=(0,1))
        table.add_column(style="muted", justify="right", no_wrap=True)
        table.add_column(style="code", overflow="fold")
        for key, value in self._ordered_arguments(tool_name, args):
            table.add_row(key, value if isinstance(value, str) else repr(value))
        return table
    
    def tool_call_start(self, call_id: str, name: str, arguments: dict[str, Any], tool_kind: str)->None:
        border_style = ("tool."+tool_kind) if tool_kind else "tool"
        title = Text.assemble(
            ("*", "muted"),
            (name, "tool"),
            ("  ", "muted"),
            ("#"+call_id[:8], "muted")
        )
        display_args = dict(arguments)
        for key in ('path','cwd'):
            val = display_args.get(key)
            if isinstance(val, str) and self.cwd:
                display_args[key] = str(display_path_rel_to_cwd(val, self.cwd))
        
        panel = Panel(
            self._render_args_table(name, display_args) if display_args else Text("no arguments"), 
            title=title, 
            style="muted", 
            padding=(1,2), 
            box = box.ROUNDED,
            subtitle=Text("running", style="muted"),
            title_align="left",
            subtitle_align="right",
            border_style= border_style
        )
        self._console.print()
        self._console.print(panel)

    def _extract_read_file_code(self, text: str) -> tuple[int, str] | None:
        body = text
        header_match = re.match(r"^showing lines (\d+) - (\d+) of total (\d+) lines\n\n", text)

        if header_match:
            body = text[header_match.end() :]

        code_lines: list[str] = []
        start_line: int | None = None

        for line in body.splitlines():
            m = re.match(r"^\s*(\d+): ?(.*)$", line)
            if not m:
                return None
            line_no = int(m.group(1))
            if start_line is None:
                start_line = line_no
            code_lines.append(m.group(2))

        if start_line is None:
            return None

        return start_line, "\n".join(code_lines)

    def _guess_language(self, path: str | None) -> str:
        if not path:
            return "text"
        suffix = Path(path).suffix.lower()
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".toml": "toml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "bash",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".kt": "kotlin",
            ".swift": "swift",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".hpp": "cpp",
            ".css": "css",
            ".html": "html",
            ".xml": "xml",
            ".sql": "sql",
        }.get(suffix, "text")


    def tool_call_end(self, tool_kind: str ,call_id: str, name: str, output: str, success: bool, error: str | None, metadata: dict[str, Any], truncated: bool):
        border_style = ("tool."+tool_kind) if tool_kind else "tool"
        status_icon = "✅" if success else "❌"
        status_style = "success" if success else "error"

        title = Text.assemble(
            (f"{status_icon}", status_style),
            (name, "tool"),
            ("  ", "muted"),
            ("#"+call_id[:8], "muted")
        )

        primary_path = None
        blocks = []
        if isinstance(metadata, dict) and isinstance(metadata.get("path"), (str, Path)):
            primary_path = str(metadata.get("path"))

        if not success:
            blocks.append(Text(error or "tool failed", style="error"))
        elif name == "read_file":
            extracted = self._extract_read_file_code(output) if primary_path else None
            if extracted:
                start_line, code = extracted

                shown_start = metadata.get("read_start_idx")
                shown_end = metadata.get("read_end_idx")
                total_lines = metadata.get("total_lines")
                pl = self._guess_language(primary_path)

                header_parts = [str(display_path_rel_to_cwd(primary_path, self.cwd))]
                header_parts.append(" • ")

                if shown_start and shown_end and total_lines:
                    header_parts.append(
                        f"lines {shown_start}-{shown_end} of {total_lines}"
                    )

                header = "".join(header_parts)
                blocks.append(Text(header, style="muted"))
                blocks.append(
                    Syntax(
                        code,
                        pl,
                        theme="monokai",
                        line_numbers=True,
                        start_line=start_line,
                        word_wrap=False,
                    )
                )
            else:
                output_display = truncate_text(
                    output,
                    os.environ.get("AI_MODEL"),
                    self._max_block_tokens,
                    preserve_lines=True
                )
                blocks.append(
                    Syntax(
                        output_display,
                        "text",
                        theme="monokai",
                        word_wrap=False,
                    )
                )

        if truncated:
            blocks.append(Text("note: tool output was truncated", style="warning"))

        panel = Panel(
            Group(
                *blocks,
            ),
            title=title,
            title_align="left",
            subtitle=Text("done" if success else "failed", style=status_style),
            subtitle_align="right",
            border_style=border_style,
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self._console.print()
        self._console.print(panel)

