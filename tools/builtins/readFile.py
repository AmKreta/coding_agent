from __future__ import annotations
import os
from pydantic import Field
from pydantic import BaseModel
from typing import Optional

from llm.tokenizer import get_token_count, truncate_text
from tools.baseTool import Tool
from tools.invocation import ToolInvocation
from tools.result import ToolResult
from utils.path import is_binary_file, resolve_path
from utils.storage import byte_to_mega_byte

MAX_FILE_SIZE = 1024 * 1024 * 10
MAX_TOKEN_COUNT = 25000

class ReadFileParameters(BaseModel):
    path: str = Field(
        ..., description="location of the file to read in working the directory or absolute path of the file to read"
    )
    offset: int = Field(1, ge = 1, description="line number to start reading from (1 based), defaults to one" )
    limit: Optional[int] = Field(None, ge = 1, description="maximum number of lines to read in the file")

class ReadFileTool(Tool):
    name="read_file"
    description="""
        Read the file content of a text file. Returns the file content with line numbers.
        For large files use offset and limit to read specific portions.
        Cannot read binary files like images, audio, video, executables etc.
    """
    schema = ReadFileParameters

    async def execute(self, invocation: ToolInvocation):
        params = ReadFileParameters(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)

        if not path.exists():
            return ToolResult.error_result(f"file not found : {path}")

        if not path.is_file():
            return ToolResult.error_result(f"path is not a file : {path}")

        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return ToolResult.error_result(f"file too large ({byte_to_mega_byte(file_size):.1f} MB). Max supported is {byte_to_mega_byte(MAX_FILE_SIZE):.0f} MB")

        if is_binary_file(path):
            return ToolResult.error_result(f"cannot read binary file {path} with size {byte_to_mega_byte(file_size):.1f} MB")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        lines = content.splitlines()

        num_lines = len(lines)
        if num_lines == 0:
            return ToolResult.success_result("", metadata = {
                "lines":0
            })

        try:
            start_idx = max(0, params.offset-1)
            end_idx = min(start_idx + (params.limit or num_lines), num_lines)
            selected_lines = lines[start_idx:end_idx]
            formattedLines: list[str] = []
            for index, line in enumerate(selected_lines):
                formattedLines.append(f"{(start_idx+index+1):6}: {line}")
            output = "\n".join(formattedLines)
            token_count = get_token_count(os.environ.get("AI_MODEL"), output)

            truncated = False
            if token_count > MAX_TOKEN_COUNT:
                output = truncate_text(
                    text = output, 
                    max_tokens=MAX_TOKEN_COUNT, 
                    preserve_lines=True,
                    suffix=f"\n...*[TRUNCATED] total {num_lines} lines*\n",
                    model=os.environ.get("AI_MODEL")
                )
                truncated = True
            metadata_lines = []
            if start_idx > 0 or end_idx < num_lines:
                metadata_lines.append(f"showing lines {start_idx+1} - {end_idx} of total {num_lines} lines")
            
            if len(metadata_lines):
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output
            
            return ToolResult.success_result(
                output=output,
                metadata = {
                    "path": path,
                    "read_start_idx": start_idx+1,
                    "read_end_idx": end_idx,
                    "total_lines": num_lines
                },
                truncated = truncated
            )
        except Exception as e:
            return ToolResult.error_result(f"failed to read file {path}. {e}")
        
