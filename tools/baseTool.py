from __future__ import annotations
import abc
from typing import Any
from pydantic import BaseModel, ValidationError
from pydantic.json_schema import model_json_schema

from tools.confirmation import ToolConfirmation
from .invocation import ToolInvocation
from .kind import ToolKind

class Tool(abc.ABC):
    name : str;
    description: str;
    kind: ToolKind;

    def __init__(self) -> None:
        pass

    @property
    def schema(self)->dict[str, Any] | type['BaseModel']:
        raise NotImplementedError("tool must define schema")
    
    @abc.abstractmethod
    async def execute(self, invocation: ToolInvocation):
        """defines what should happen when the tool is executed"""
        pass

    def validate_parameters(self, params: dict[str, Any]):
        if isinstance(self.schema, type) and issubclass(self.schema, BaseModel):
            try:
                self.schema(**params)
            except ValidationError as e:
                errors = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error.get("loc",[]))
                    errors.append(f"{field}: {error.get('msg')}")
                return errors
            except Exception as e:
                return [str(e)]
    
    def is_mutating(self):
        return self.kind in {
            ToolKind.WRITE,
            ToolKind.SHELL,
            ToolKind.NETWORK,
            ToolKind.MEMORY
        }

    async def get_confirmation(self, invocation: ToolInvocation) -> ToolConfirmation | None:
        if not self.is_mutating(invocation.params):
            return None
        return ToolConfirmation(
            tool_name = self.name,
            params = invocation.params,
            description = f"Execute {self.name}"
        )

    def to_openai_schema(self) -> dict[str, Any]:
        if isinstance(self.schema, type) and issubclass(self.schema, BaseModel):
            json_schema = model_json_schema(self.schema)
            return {
                "name": self.name,
                "description": self.description,
                "parameters" :{
                    "type": "object",
                    "properties": json_schema.get("properties",{}),
                    "required":  json_schema.get("required", [])
                } 
            }   
        if isinstance(self.schema, dict):
            return {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema.get("parameters") or self.schema
            }

        raise ValueError(f"schema format is not compatible with current implementation: {self.schema}")

        

