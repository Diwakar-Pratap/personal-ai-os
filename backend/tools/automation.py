"""
tools/automation.py - Runs Python scripts for automation tasks (e.g. calculation, formatting).
"""
from __future__ import annotations

import sys
import io
import contextlib
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class AutomationTool(BaseTool):
    name = "python_automation"
    description = "Executes python code to perform calculations, data processing, or generate script outputs. Use this when you need exact math or programmatic logic."

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
                            "description": "The python code to execute. Must be valid python code."
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def run(self, input: ToolInput) -> ToolOutput:
        code = input.query
        
        # Simple sandbox capturing stdout
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                # We use a restricted dictionary for safety, but it's a personal OS.
                exec(code, {"__builtins__": __builtins__}, {})
            
            result = output.getvalue()
            if not result:
                result = "Code executed successfully with no print output."
            return ToolOutput.ok(result)
        except Exception as e:
            return ToolOutput.fail(f"Python error: {str(e)}\nPartial output: {output.getvalue()}")
