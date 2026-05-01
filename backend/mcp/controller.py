"""
mcp/controller.py — The main MCP orchestrator.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from memory.short_term import ShortTermMemory
from memory.medium_term import MediumTermMemory
from memory.long_term import long_term_memory
from memory.importance import extract_memories
from llm.openai_client import chat_completion, stream_completion
from mcp.router import tool_router


class MCPController:
    """
    Orchestrates the full lifecycle of a single user query.
    Handles short-term memory, long-term semantic retrieval, and storage.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.memory = ShortTermMemory(session_id)
        self.medium_term = MediumTermMemory(session_id)

    def _inject_memories(self, messages: list[dict], memories: list[str], summary: str | None = None):
        """Injects retrieved memories and summary into the system prompt (first message)."""
        if not messages:
            return
            
        memory_block = ""
        if summary:
            memory_block += f"\n\nCONVERSATION SUMMARY:\n{summary}"
        if memories:
            memory_block += "\n\nRELEVANT PAST MEMORIES:\n- " + "\n- ".join(memories)
            
        if not memory_block:
            return
            
        # Ensure first message is system
        if messages[0]["role"] == "system":
            messages[0]["content"] += memory_block
        else:
            messages.insert(0, {"role": "system", "content": f"You are a Personal AI OS.{memory_block}"})

    async def _post_process_memory(self, user_msg: str, ai_msg: str):
        """
        Runs in background. Extracts facts from the exchange and stores them if important.
        """
        try:
            facts = await extract_memories(user_msg, ai_msg)
            for fact in facts:
                # Every extracted fact is considered important enough to store
                # since the extraction prompt already filters for 'important details'.
                await long_term_memory.add_memory(fact)
                print(f"[MEMORY] Stored: {fact}")
        except Exception as e:
            print(f"[MEMORY ERROR] Failed to store memory: {e}")

    # ── Public API ──────────────────────────────────────────

    async def process(self, user_message: str, db: AsyncSession) -> str:
        """Non-streaming: returns full response string."""
        await self.memory.add_message(db, "user", user_message)

        # 1. Search Long-Term Memory & Summary
        memories = await long_term_memory.search(user_message)
        summary = await self.medium_term.get_summary(db)
        
        # 2. Intent detection (LLM pre-flight)
        intent, query_arg = await tool_router.detect_intent(user_message)
        tool_result: str | None = None
        if intent:
            tool = tool_router.get(intent)
            if tool:
                from tools.base_tool import ToolInput
                output = await tool.run(ToolInput(query=query_arg))
                if output.success:
                    tool_result = str(output.result)

        # 3. Build Context
        messages = await self.memory.get_context(db)
        self._inject_memories(messages, memories, summary)

        if tool_result:
            messages.append({
                "role": "system",
                "content": f"[Tool result — {intent}]: {tool_result}",
            })

        # 4. Generate & Save
        response = await chat_completion(messages)
        await self.memory.add_message(db, "assistant", response)

        # 5. Background: Store new memories & Summarize
        asyncio.create_task(self._post_process_memory(user_message, response))
        msg_count = await self.memory.get_message_count(db)
        await self.medium_term.maybe_summarize(db, msg_count)

        return response

    async def process_stream(
        self, user_message: str, db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """Streaming: yields text chunks. Saves complete response after stream ends."""
        await self.memory.add_message(db, "user", user_message)

        # 1. Search Long-Term Memory & Summary
        memories = await long_term_memory.search(user_message)
        summary = await self.medium_term.get_summary(db)

        # 2. Intent detection (LLM pre-flight)
        intent, query_arg = await tool_router.detect_intent(user_message)
        tool_result: str | None = None
        if intent:
            tool = tool_router.get(intent)
            if tool:
                from tools.base_tool import ToolInput
                output = await tool.run(ToolInput(query=query_arg))
                if output.success:
                    tool_result = str(output.result)

        # 3. Build Context
        messages = await self.memory.get_context(db)
        self._inject_memories(messages, memories, summary)

        if tool_result:
            messages.append({
                "role": "system",
                "content": f"[Tool result — {intent}]: {tool_result}",
            })

        # 4. Stream Response
        full_response = ""
        async for chunk in stream_completion(messages):
            full_response += chunk
            yield chunk

        # 5. Save & Background Store Memory
        if full_response:
            await self.memory.add_message(db, "assistant", full_response)
            asyncio.create_task(self._post_process_memory(user_message, full_response))
            msg_count = await self.memory.get_message_count(db)
            await self.medium_term.maybe_summarize(db, msg_count)
