from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolConfirmation:
    tool_name: str
    params: dict[str, Any]
    description: str
