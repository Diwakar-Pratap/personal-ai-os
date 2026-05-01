'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Session, Message } from '@/types';
import {
  createSession,
  listSessions,
  deleteSession,
  getMessages,
  streamChat,
  uploadFile,
} from '@/lib/api';

// ── Helpers ────────────────────────────────────────────────────

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const STARTERS = [
  '✨ What can you help me with today?',
  '🧠 Remember: my favourite language is Python',
  '📝 Summarize this text for me...',
  '🔍 Search my past conversations for...',
];

// ── Component ──────────────────────────────────────────────────

export default function Home() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Load sessions on mount ──────────────────────────────────
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const list = await listSessions();
      setSessions(list);
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  };

  // ── Auto-scroll ─────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Auto-resize textarea ────────────────────────────────────
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = '22px';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  // ── Session handling ────────────────────────────────────────
  const handleNewChat = async () => {
    try {
      const session = await createSession('New Chat');
      setSessions(prev => [session, ...prev]);
      setActiveSession(session);
      setMessages([]);
      setSidebarOpen(false);
    } catch (e) {
      console.error('Failed to create session', e);
    }
  };

  const handleSelectSession = async (session: Session) => {
    setActiveSession(session);
    setLoadingHistory(true);
    setSidebarOpen(false);
    try {
      const msgs = await getMessages(session.id);
      setMessages(msgs);
    } catch (e) {
      console.error('Failed to load messages', e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSession?.id === id) {
      setActiveSession(null);
      setMessages([]);
    }
  };

  // ── Send message ────────────────────────────────────────────
  const handleSend = useCallback(async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isStreaming) return;

    let session = activeSession;
    if (!session) {
      session = await createSession('New Chat');
      setSessions(prev => [session!, ...prev]);
      setActiveSession(session);
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsStreaming(true);

    // Placeholder for AI response
    const aiId = crypto.randomUUID();
    const aiPlaceholder: Message = {
      id: aiId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, aiPlaceholder]);

    try {
      let full = '';
      for await (const chunk of streamChat(session.id, content)) {
        full += chunk;
        setMessages(prev =>
          prev.map(m => (m.id === aiId ? { ...m, content: full } : m))
        );
      }

      // Update session title in sidebar after first message
      setSessions(prev =>
        prev.map(s =>
          s.id === session!.id
            ? { ...s, title: content.slice(0, 50), updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch (e) {
      console.error('Stream error', e);
      setMessages(prev =>
        prev.map(m =>
          m.id === aiId
            ? { ...m, content: '⚠️ Failed to get response. Is the backend running?' }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }, [input, activeSession, isStreaming]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── File Upload ─────────────────────────────────────────────
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const res = await uploadFile(file);
      // Append the instruction to read the file into the user's input box
      setInput(prev => {
        const spacer = prev && !prev.endsWith(' ') ? ' ' : '';
        return prev + spacer + `[Please read this file: ${res.file_path}]`;
      });
      // Optionally focus the textarea
      textareaRef.current?.focus();
    } catch (err) {
      console.error('File upload failed', err);
      alert('Failed to upload file.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="app-shell">

      {/* Sidebar overlay (mobile) */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Sidebar ── */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">🧠</div>
            <span className="sidebar-logo-text">Personal AI OS</span>
          </div>
          <button
            id="btn-new-chat"
            className="btn-new-chat"
            onClick={handleNewChat}
          >
            <span>＋</span> New Chat
          </button>
        </div>

        {sessions.length > 0 && (
          <div className="sidebar-section-label">Recent</div>
        )}

        <div className="session-list">
          {sessions.map(s => (
            <div
              key={s.id}
              id={`session-${s.id.slice(0, 8)}`}
              className={`session-item ${activeSession?.id === s.id ? 'active' : ''}`}
              onClick={() => handleSelectSession(s)}
            >
              <span className="session-icon">💬</span>
              <span className="session-title">{s.title}</span>
              <button
                className="session-delete"
                onClick={e => handleDeleteSession(e, s.id)}
                title="Delete session"
              >
                ✕
              </button>
            </div>
          ))}

          {sessions.length === 0 && (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
              No conversations yet
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="chat-main">

        {/* Header */}
        <header className="chat-header">
          {/* Hamburger (mobile) */}
          <button
            id="btn-sidebar-toggle"
            onClick={() => setSidebarOpen(o => !o)}
            style={{
              background: 'none', border: 'none', color: 'var(--text-secondary)',
              cursor: 'pointer', fontSize: '18px', display: 'none',
              padding: '4px',
            }}
            className="mobile-menu-btn"
          >
            ☰
          </button>
          <span className="chat-header-title">
            {activeSession?.title ?? 'Personal AI OS'}
          </span>
          <span className="header-badge">Llama 3.1 8B · NVIDIA</span>
        </header>

        {/* Messages */}
        <div className="messages-container" id="messages-container">
          {!activeSession && messages.length === 0 && (
            <div className="welcome-screen">
              <div className="welcome-orb">🧠</div>
              <h1 className="welcome-title">Your Personal AI OS</h1>
              <p className="welcome-subtitle">
                A private AI assistant with long-term memory, modular tools, and
                full control over your data.
              </p>
              <div className="welcome-chips">
                {STARTERS.map((s, i) => (
                  <button
                    key={i}
                    className="welcome-chip"
                    onClick={() => {
                      setInput(s);
                      textareaRef.current?.focus();
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loadingHistory && (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px', padding: '20px' }}>
              Loading history…
            </div>
          )}

          {messages.map(msg => (
            <div
              key={msg.id}
              className={`message-row ${msg.role}`}
              id={`msg-${msg.id.slice(0, 8)}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-bubble">
                {msg.content === '' && msg.role === 'assistant' ? (
                  <div className="typing-indicator">
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                    <div className="typing-dot" />
                  </div>
                ) : (
                  <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                )}
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-wrapper">
            <button
              className="btn-upload"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading || isStreaming}
              title="Upload file"
              style={{
                background: 'none', border: 'none', color: 'var(--text-muted)',
                cursor: 'pointer', padding: '8px', fontSize: '18px',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}
            >
              {isUploading ? '⏳' : '📎'}
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              accept=".txt,.pdf,.csv,.md,.json"
            />
            <textarea
              ref={textareaRef}
              id="chat-input"
              className="chat-textarea"
              placeholder="Message your AI OS…  (Shift+Enter for new line)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              rows={1}
            />
            <button
              id="btn-send"
              className="btn-send"
              onClick={() => handleSend()}
              disabled={!input.trim() || isStreaming}
              title="Send message"
            >
              {isStreaming ? '⏳' : '↑'}
            </button>
          </div>
          <p className="input-hint">
            Phase 5 · Medium-Term Memory & Advanced Tools Active
          </p>
        </div>
      </main>

      {/* Mobile menu button CSS injection */}
      <style>{`
        @media (max-width: 640px) {
          .mobile-menu-btn { display: flex !important; }
        }
      `}</style>
    </div>
  );
}
