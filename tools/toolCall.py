from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolCall:
    name: str
    call_id: str
    params: dict[str, Any]