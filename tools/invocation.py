from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ToolInvocation:
   cwd: str;
   params: dict[str, Any] = field(default_factory=dict)