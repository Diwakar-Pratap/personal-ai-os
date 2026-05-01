"""
tools/file_tool.py - Reads and parses documents (PDFs, TXT, etc.).
"""
from __future__ import annotations

import os
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class FileTool(BaseTool):
    name = "read_file"
    description = "Reads text or parses PDF content from a local file path. Use this when the user asks you to read or summarize a specific document."

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
                            "description": "The absolute path to the file to read (e.g. C:\\path\\to\\file.txt or .pdf)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }

    async def run(self, input: ToolInput) -> ToolOutput:
        file_path = input.query.strip().strip("'").strip('"')
        
        if not os.path.exists(file_path):
            return ToolOutput.fail(f"File not found: {file_path}")
            
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                import PyPDF2
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    # Read first few pages to avoid massive payloads for now
                    for i in range(min(5, len(reader.pages))):
                        text += reader.pages[i].extract_text() + "\n"
                
                if len(reader.pages) > 5:
                    text += "\n... (Truncated to first 5 pages for context limits)"
                return ToolOutput.ok(text)
            else:
                # Fallback text reading
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(10000) # limit to 10k chars
                return ToolOutput.ok(text)
                
        except Exception as e:
            return ToolOutput.fail(f"Failed to read file: {str(e)}")
