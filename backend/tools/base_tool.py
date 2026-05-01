"""
tools/base_tool.py — Abstract base class for all MCP tools.
Every tool (Memory, File, Automation, WebSearch) implements this interface.
The MCPController calls tools via this contract.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Standard input payload for all tools."""
    query: str
    context: Dict[str, Any] = {}


class ToolOutput(BaseModel):
    """Standard response from any tool."""
    success: bool
    result: Any = None
    error: str = ""

    @classmethod
    def ok(cls, result: Any) -> "ToolOutput":
        return cls(success=True, result=result)

    @classmethod
    def fail(cls, error: str) -> "ToolOutput":
        return cls(success=False, error=error)


class BaseTool(ABC):
    """
    All MCP tools extend this class.
    Register tools with the ToolRouter; the MCPController dispatches to them.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def run(self, input: ToolInput) -> ToolOutput: ...

    def get_schema(self) -> Dict:
        """OpenAI function-calling compatible schema (Phase 3)."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The tool query"},
                    },
                    "required": ["query"],
                },
            }
        }
