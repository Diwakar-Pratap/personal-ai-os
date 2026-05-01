"""
main.py — FastAPI application entry point.
Handles app creation, CORS (for Next.js + phone access), and startup lifecycle.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from api.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB tables on startup."""
    await init_db()
    print("[OK] Database initialized (stored in OneDrive)")
    yield
    print("[BYE] Shutting down Personal AI OS")


app = FastAPI(
    title="Personal AI OS",
    description="Your private AI assistant with long-term memory and MCP tools",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — open for localhost dev + ngrok tunnel + phone access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
