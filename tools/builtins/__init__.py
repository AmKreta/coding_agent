from tools.baseTool import Tool
from tools.builtins.readFile import ReadFileTool

__all__:list[Tool] = [
    ReadFileTool
]

def get_all_builtin_tools():
    return __all__

