// types/index.ts — Shared TypeScript types for the Personal AI OS

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  stream?: boolean;
}
