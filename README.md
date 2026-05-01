# Personal AI OS

A private, self-hosted AI operating system featuring a modular architecture, comprehensive memory systems, and tool-use capabilities.

## Architecture

The system is split into two primary components:

*   **Backend (`/backend`)**: A robust FastAPI application powered by Python. It uses an async SQLite database (often synced via OneDrive for cross-device persistence) and an OpenAI-compatible LLM client (currently configured for NVIDIA's API).
*   **Frontend (`/frontend`)**: A Next.js application that provides a responsive, Google Keep-style UI for chatting, viewing memory, uploading files, and managing sessions.

### Key Backend Systems

1.  **Memory Management (`backend/memory/`)**
    *   **Short-Term Memory**: A sliding window of the most recent conversation turns, directly injected into the LLM context.
    *   **Medium-Term Memory**: An automated background system that fires every 15 messages, summarizing the conversation to maintain context without hitting token limits.
    *   **Long-Term Memory**: Semantic retrieval that extracts essential facts and retrieves them when contextually relevant.
2.  **Model Context Protocol (MCP) Controller (`backend/mcp/`)**
    *   Orchestrates the entire query lifecycle. Detects intents, routes to specific tools, fetches memory, and generates streaming responses.
3.  **Tools (`backend/tools/`)**
    *   A modular directory of tools (e.g., File Upload/Read, Web Search, System Automation). 

---

## Roadmap & Implementation Phases

*   [x] **Phase 1: Foundation**
    *   Established the FastAPI server and Next.js shell.
    *   Set up basic SSE (Server-Sent Events) streaming.
    *   Integrated SQLite session storage.
*   [x] **Phase 2: Basic Memory**
    *   Implemented Short-Term sliding windows.
    *   Drafted long-term fact extraction.
*   [x] **Phase 3: Tool Routing**
    *   Introduced an LLM pre-flight intent detection step to dynamically select and run basic tools before generating a response.
*   [x] **Phase 4: File Upload**
    *   Built multipart endpoints and frontend components for ingesting `.txt`, `.pdf`, `.csv`, etc., into the MCP.
*   [x] **Phase 5: Medium-Term Summarization**
    *   Activated the rolling summarization engine that compresses history every `N` messages and automatically injects it as a persistent system prompt.
*   [ ] **Phase 6: Advanced Tooling & Function Calling (Next Up)**
    *   *Planned:* Transition intent-detection to native LLM function calling schemas.
    *   *Planned:* Build out advanced OS integrations (calendar, code execution, local search).

---

## Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

**Configuration (`backend/.env`)**
Create an `.env` file in the backend directory based on `.env.example`:
```ini
OPENAI_API_KEY=your_nvidia_or_openai_key
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=meta/llama-3.1-8b-instruct
PORT=8002
# Optional: ngrok for phone access
ENABLE_NGROK=true
NGROK_AUTH_TOKEN=your_token_here
```

**Run the Backend**
```bash
python start.py
```
*(This starts the uvicorn server on port 8002, and opens an ngrok tunnel if enabled).*

### 2. Frontend Setup

```bash
cd frontend
npm install
```

**Configuration (`frontend/.env.local`)**
Create an `.env.local` to point to the backend:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8002
```
*(Note: If using ngrok, update this URL to your public ngrok URL to access the UI from your phone).*

**Run the Frontend**
```bash
npm run dev
```

Visit `http://localhost:3000` to interact with your Personal AI OS.
