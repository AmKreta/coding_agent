from __future__ import annotations
from pathlib import Path
from typing import Any
from tools.baseTool import Tool
import logging

from tools.builtins import get_all_builtin_tools
from tools.invocation import ToolInvocation
from tools.result import ToolResult

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool):
        if self.tools.get(tool.name):
            logger.warning(f"{tool.name} is already registered")
            return
        self.tools[tool.name] = tool
        logger.debug(f"{tool.name} registered successfully")

    def unregister(self, tool: str):
        if tool in self.tools:
            del self.tools[tool]
        else:
            logger.warning(f"unable to unregister {tool}. Tool doesn't exist")
    
    def get(self, tool: str):
       if tool in self.tools:
            return self.tools[tool]
            

    def get_tools(self) -> list[Tool]:
        tools:list[Tool] = []
        for tool in self.tools.values():
            tools.append(tool)
        return tools
    
    def get_schemas(self):
        return [tool.to_openai_schema() for tool in self.get_tools()]

    async def invoke(self, name: str, params: dict[str, Any], cwd: Path | None, **kwargs):
        tool = self.get(name);
        if not tool:
            return ToolResult.error_result(
                error = f"tool doesn't exist: {name}",
                metadata = {"tool_name": name, "cwd": cwd}
            )
        params_invalid = tool.validate_parameters(params)
        if params_invalid:
            errors = "\n".join(params_invalid)
            return ToolResult.error_result(
                error = f"tool {name} called with invalid params: {errors}",
                metadata = {"tool_name": name, "params":params, "cwd": cwd, "error": errors}
            )
        
        invocation = ToolInvocation(
            cwd,
            params
        )
        try:
            return await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"tool {name} raised unexpected error")
            return ToolResult.error_result(
                error = f"tool {name} raised unexpected error: {e}",
                metadata = {"tool_name": name, "params":params, "cwd": cwd, "error": str(e)}
            )



def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry();
    for tool in get_all_builtin_tools():
        registry.register(tool())
    return registry