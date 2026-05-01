"""
tools/memory_tool.py - Explicitly store or recall facts from long term memory.
"""
from __future__ import annotations

from tools.base_tool import BaseTool, ToolInput, ToolOutput
from memory.long_term import long_term_memory

class MemoryTool(BaseTool):
    name = "memory_tool"
    description = "Explicitly stores or retrieves information from long-term memory. Use when the user asks you to 'remember this' or 'do you remember'."

    async def run(self, input: ToolInput) -> ToolOutput:
        query = input.query.lower()
        try:
            # If the user says "remember X", we store it.
            if query.startswith("remember ") or query.startswith("save "):
                fact = query.replace("remember ", "").replace("save ", "").strip()
                await long_term_memory.add_memory(fact)
                return ToolOutput.ok(f"Successfully remembered: {fact}")
            else:
                # Retrieve
                results = await long_term_memory.search(input.query)
                if not results:
                    return ToolOutput.ok("No relevant memories found.")
                return ToolOutput.ok("Found memories:\n- " + "\n- ".join(results))
        except Exception as e:
            return ToolOutput.fail(f"Memory operation failed: {str(e)}")
