"""
api/routes/chat.py — All HTTP endpoints for the Personal AI OS.

Endpoints:
  POST   /api/sessions                       → create session
  GET    /api/sessions                       → list all sessions
  PATCH  /api/sessions/{id}/title            → rename session
  DELETE /api/sessions/{id}                  → delete session
  GET    /api/sessions/{id}/messages         → load full history
  POST   /api/chat                           → send message (streaming SSE)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Session, Message
from mcp.controller import MCPController

router = APIRouter(prefix="/api")


# ── Request / Response schemas ──────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str = "New Chat"


class ChatRequest(BaseModel):
    session_id: str
    message: str
    stream: bool = True


class TitleUpdateRequest(BaseModel):
    title: str


# ── Session endpoints ───────────────────────────────────────

@router.post("/sessions", status_code=201)
async def create_session(
    req: CreateSessionRequest, db: AsyncSession = Depends(get_db)
):
    session = Session(id=str(uuid.uuid4()), title=req.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).order_by(Session.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]


@router.patch("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    req: TitleUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_or_404(session_id, db)
    session.title = req.title
    await db.commit()
    return {"status": "updated"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await _get_session_or_404(session_id, db)
    await db.delete(session)
    await db.commit()
    return {"status": "deleted"}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    await _get_session_or_404(session_id, db)
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp,
        }
        for m in messages
    ]


# ── Chat endpoint ───────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    session = await _get_session_or_404(req.session_id, db)
    controller = MCPController(req.session_id)

    # Auto-title the session from the first message
    if session.title == "New Chat":
        title = req.message[:50].strip()
        session.title = title if title else "New Chat"

    session.updated_at = datetime.utcnow()
    await db.commit()

    if req.stream:
        async def generate():
            try:
                async for chunk in controller.process_stream(req.message, db):
                    # Encode newlines so each SSE "data:" line stays on one line
                    safe_chunk = chunk.replace("\\", "\\\\").replace("\n", "\\n")
                    yield f"data: {safe_chunk}\n\n"
            except Exception as e:
                # Send error to client as a special SSE event so UI can display it
                yield f"data: [ERROR] {str(e)}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )
    else:
        response = await controller.process(req.message, db)
        return {"response": response, "session_id": req.session_id}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    import os
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    return {"status": "success", "file_path": file_path, "filename": file.filename}


# ── Helpers ─────────────────────────────────────────────────

async def _get_session_or_404(session_id: str, db: AsyncSession) -> Session:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session
