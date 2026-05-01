"""
memory/medium_term.py — Conversation summarization (Phase 2).
Every N messages, the LLM summarizes the conversation so far.
The summary is injected into the system prompt to extend effective context.
"""
from __future__ import annotations

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Message, Summary
from llm.openai_client import chat_completion


class MediumTermMemory:
    """
    Generates and stores rolling conversation summaries.
    Summaries are stored in the DB and injected into the system prompt.
    Triggered automatically every `summary_interval` messages.
    """

    summary_interval: int = 15  # summarize every 15 messages

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    async def maybe_summarize(self, db: AsyncSession, message_count: int) -> None:
        """Check if it's time to generate a new summary. Triggered in Phase 2."""
        if message_count == 0 or message_count % self.summary_interval != 0:
            return

        print(f"[SUMMARY] Generating new summary for {self.session_id}...")
        
        # Load last N messages to summarize
        result = await db.execute(
            select(Message)
            .where(Message.session_id == self.session_id)
            .order_by(Message.timestamp.desc())
            .limit(self.summary_interval)
        )
        messages = list(reversed(result.scalars().all()))
        
        history_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        
        prompt = f"""
        Provide a concise, detailed summary of the following conversation history.
        Focus on key decisions, personal facts shared by the user, and the current state of tasks.
        
        HISTORY:
        {history_text}
        
        SUMMARY:
        """
        
        try:
            summary_content = await chat_completion([{"role": "system", "content": prompt}])
            if summary_content:
                new_summary = Summary(session_id=self.session_id, content=summary_content)
                db.add(new_summary)
                await db.commit()
                print(f"[SUMMARY] New summary stored.")
        except Exception as e:
            print(f"[SUMMARY ERROR] {e}")

    async def get_summary(self, db: AsyncSession) -> str | None:
        """Retrieve the latest summary for this session. Activated in Phase 2."""
        result = await db.execute(
            select(Summary)
            .where(Summary.session_id == self.session_id)
            .order_by(Summary.timestamp.desc())
            .limit(1)
        )
        summary = result.scalar_one_or_none()
        return summary.content if summary else None
