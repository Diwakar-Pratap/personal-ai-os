// lib/api.ts — API client for the Personal AI OS backend
// All calls go to NEXT_PUBLIC_API_URL (set in .env.local)

import { Session, Message } from '@/types';

const BASE = process.env.NEXT_PUBLIC_API_URL !== undefined ? process.env.NEXT_PUBLIC_API_URL : 'http://localhost:8002';

// ── Sessions ──────────────────────────────────────────────────

export async function createSession(title = 'New Chat'): Promise<Session> {
  const res = await fetch(`${BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function listSessions(): Promise<Session[]> {
  const res = await fetch(`${BASE}/api/sessions`);
  if (!res.ok) throw new Error('Failed to list sessions');
  return res.json();
}

export async function deleteSession(id: string): Promise<void> {
  await fetch(`${BASE}/api/sessions/${id}`, { method: 'DELETE' });
}

export async function updateSessionTitle(id: string, title: string): Promise<void> {
  await fetch(`${BASE}/api/sessions/${id}/title`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error('Failed to load messages');
  return res.json();
}

// ── Chat (Streaming SSE) ──────────────────────────────────────

export async function* streamChat(
  sessionId: string,
  message: string
): AsyncGenerator<string> {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message, stream: true }),
  });

  if (!res.ok) throw new Error('Chat request failed');
  if (!res.body) throw new Error('No response body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        if (data.startsWith('[ERROR]')) {
          throw new Error(data.slice(8)); // Strip "[ERROR] " prefix
        }
        // Unescape encoded characters from server-side
        yield data.replace(/\\n/g, '\n').replace(/\\n/g, '\n').replace(/\\/g, '\\');
      }
    }
  }
}

// ── Files ─────────────────────────────────────────────────────

export async function uploadFile(file: File): Promise<{ status: string; file_path: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE}/api/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error('Failed to upload file');
  return res.json();
}
