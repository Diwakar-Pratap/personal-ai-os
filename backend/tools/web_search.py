"""
tools/web_search.py - Uses duckduckgo-search for live web searching.
"""
from __future__ import annotations

import json
from ddgs import DDGS
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Searches the web for up-to-date information, news, or facts that the AI doesn't know."

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The precise search query to look up on the web"
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def run(self, input: ToolInput) -> ToolOutput:
        try:
            # We can run it synchronously in a thread, but DDGS is fast enough.
            # duckduckgo_search is synchronous.
            with DDGS() as ddgs:
                results = list(ddgs.text(input.query, max_results=3))
            
            if not results:
                return ToolOutput.ok("No results found on the web.")
            
            # Format results
            formatted = []
            for r in results:
                formatted.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nSource: {r.get('href')}")
            
            return ToolOutput.ok("\n\n".join(formatted))
        except Exception as e:
            return ToolOutput.fail(f"Web search failed: {str(e)}")
