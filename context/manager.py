from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Any
from llm.tokenizer import get_token_count
from prompts.role import Role
from prompts.system import get_system_prompt

@dataclass
class MessageItem:
    def __init__(self, role: Role, content: str, token_count: int, tool_call_id: str | None = None) -> None:
        self.role = role
        self.content = content
        self.token_count = token_count
        self.tool_call_id: str | None = tool_call_id
        self.tool_calls:list[dict[str, Any]] = []
    
    def to_dict(self):
        res = {
            "role": self.role.value,
            "content": self.content
        }
        if self.tool_call_id:
            res["tool_call_id"] = self.tool_call_id
        if len(self.tool_calls):
            res["tool_calls"] = self.tool_calls
        return res


class ContextManager:
    def __init__(self) -> None:
        self.system_prompt = get_system_prompt()
        self.messages: list[MessageItem] = []
        self.model = os.environ.get("AI_MODEL")

    def add_user_message(self, content: str):
        self._add_message(Role.USER, content)

    def add_assistant_message(self, content: str):
        self._add_message(Role.ASSISTANT, content)
    
    def add_tool_message(self, content: str, tool_call_id: str):
        item = MessageItem(
            role=Role.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            token_count=get_token_count(
                self.model,
                content or ""
            )
        )
        self.messages.append(item)

    def _add_message(self, role: Role, content: str):
        item = MessageItem(
            role = role,
            content = content,
            token_count = get_token_count(
                self.model,
                content or ""
            )
        )
        self.messages.append(item)

    def get_messages(self)->list[dict[str, Any]]:
        messages:list[dict[str, Any]] = []
        if self.system_prompt:
            messages.append({
                "role": Role.SYSTEM.value,
                "content": self.system_prompt
            })
        for message in self.messages:
            messages.append(message.to_dict())
        return messages