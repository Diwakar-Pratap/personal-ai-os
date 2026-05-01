"""
memory/short_term.py — Sliding window of the last N messages per session.
Loaded from DB on every request (fast with SQLite + async).
"""
from __future__ import annotations

from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Message
from config import settings

SYSTEM_PROMPT = """You are a highly capable personal AI assistant running on a private, secure system.

Your key traits:
- You have excellent memory of this conversation and can recall earlier context precisely.
- You are concise, accurate, and direct. Never pad responses with filler.
- When the user shares personal facts, preferences, or goals, acknowledge them and remember them.
- When asked to "remember" something, confirm you've stored it.
- You have access to a long-term memory system (active in Phase 2) that will give you relevant past knowledge.

Always prioritise accuracy and helpfulness over length."""


class ShortTermMemory:
    """
    Manages the in-session sliding window of messages.
    Loads the last `max_messages` turns from the DB and prepends the system prompt.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.max_messages = settings.max_short_term_messages

    async def get_context(self, db: AsyncSession) -> List[Dict]:
        """Return OpenAI-formatted message list: [system, ...last N messages]."""
        result = await db.execute(
            select(Message)
            .where(Message.session_id == self.session_id)
            .order_by(Message.timestamp.desc())
            .limit(self.max_messages)
        )
        messages: List[Message] = list(reversed(result.scalars().all()))

        formatted: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    async def add_message(self, db: AsyncSession, role: str, content: str) -> Message:
        """Persist a single message to the DB."""
        msg = Message(session_id=self.session_id, role=role, content=content)
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def get_message_count(self, db: AsyncSession) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Message.id)).where(Message.session_id == self.session_id)
        )
        return result.scalar() or 0
