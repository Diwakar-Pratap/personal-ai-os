"""
mcp/router.py — Tool registry and rule-based intent detection.
Phase 3 will upgrade intent detection to LLM function calling.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from tools.base_tool import BaseTool


class ToolRouter:
    """
    Maintains a registry of available tools.
    Detects which tool (if any) should handle a query.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        # Register Phase 3 tools
        from tools.web_search import WebSearchTool
        from tools.automation import AutomationTool
        from tools.memory_tool import MemoryTool
        from tools.file_tool import FileTool
        
        self.register(WebSearchTool())
        self.register(AutomationTool())
        self.register(MemoryTool())
        self.register(FileTool())

    def register(self, tool: BaseTool) -> None:
        """Register a tool by its name."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        return [t.get_schema() for t in self._tools.values()]

    async def detect_intent(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """
        Phase 3: LLM Intent detection using native tool calling.
        Returns (tool_name, tool_query_arg) or (None, None).
        """
        from llm.openai_client import get_client
        from config import settings
        import json
        
        client = get_client()
        tools = self.list_tools()
        
        try:
            # Fast pre-flight check to see if the LLM wants to use a tool
            response = await client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": "You are an intent detector. If the user's query requires a tool (web search, automation, explicit memory), call it. Otherwise, do not call any tool."},
                    {"role": "user", "content": query}
                ],
                tools=tools,
                tool_choice="auto",
                temperature=0.0,
                max_tokens=100
            )
            
            message = response.choices[0].message
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                return tool_name, args.get("query", query)
                
        except Exception as e:
            print(f"[TOOL ROUTER ERROR] {e}")
        return None, None

# Global instance used by the controller
tool_router = ToolRouter()
