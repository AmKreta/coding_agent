from enum import Enum


class ToolKind(Enum):
    READ = "READ"
    WRITE = "WRITE"
    SHELL = "SHELL"
    NETWORK = "NETWORK"
    MEMORY = "MEMORY"
    MCP = "MCP"