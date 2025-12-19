import { useMemo, useState } from 'react';
import { Menu, X } from 'lucide-react';
import novaAvatar from './assets/novaAvatar.avif';
import { ChatHistory } from './components/ChatHistory';
import type { ChatSession } from './components/ChatHistory';

import { ChatBot } from './components/ChatBot';
import type { Message } from './components/ChatBot';

const NOVA_GREETING: Message = {
  id: 'greet',
  text:
    "Hello! I'm Nova, your FinTech Assistant. I can help you with account inquiries, transaction history, financial advice, and more. How can I assist you today?",
  sender: 'bot',
  timestamp: new Date(),
};

function createSession(title = 'New Conversation'): ChatSession {
  const now = new Date();
  return {
    id: `sess_${now.getTime()}_${Math.random().toString(16).slice(2)}`,
    title,
    createdAt: now,
    lastMessageAt: now,
  };
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const first = createSession('New Conversation');
    return [first];
  });

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const first = sessions[0];
    return first?.id ?? '';
  });

  // Per-session messages so switching chats preserves history
  const [messagesBySession, setMessagesBySession] = useState<Record<string, Message[]>>(() => {
    const first = sessions[0];
    return first ? { [first.id]: [NOVA_GREETING] } : {};
  });

  const activeMessages = useMemo(() => {
    return messagesBySession[activeSessionId] ?? [NOVA_GREETING];
  }, [messagesBySession, activeSessionId]);

  const setActiveMessages: React.Dispatch<React.SetStateAction<Message[]>> = (updater) => {
    setMessagesBySession((prev) => {
      const current = prev[activeSessionId] ?? [NOVA_GREETING];
      const next = typeof updater === 'function' ? (updater as any)(current) : updater;
      return { ...prev, [activeSessionId]: next };
    });
  };

  const handleNewChat = () => {
    const s = createSession('New Conversation');
    setSessions((prev) => [s, ...prev]);
    setMessagesBySession((prev) => ({ ...prev, [s.id]: [NOVA_GREETING] }));
    setActiveSessionId(s.id);
    setSidebarOpen(false);
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    setMessagesBySession((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });

    if (activeSessionId === id) {
      const remaining = sessions.filter((s) => s.id !== id);
      setActiveSessionId(remaining[0]?.id ?? '');
    }
  };

  const handleSessionActivity = (sessionId: string, maybeTitle?: string) => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === sessionId
          ? {
              ...s,
              lastMessageAt: new Date(),
              title: maybeTitle && s.title === 'New Conversation' ? maybeTitle : s.title,
            }
          : s
      )
    );
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50">
      {/* Header */}
      <header className="bg-white border-b border-blue-200 shadow-sm flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <img
                src={novaAvatar}
                alt="Nova"
                className="w-12 h-12 sm:w-16 sm:h-16 rounded-full object-cover ring-2 ring-blue-300/60"
              />
              <div>
                <h1 className="text-blue-600 text-2xl sm:text-4xl tracking-wide font-semibold">
                  Nova
                </h1>
                <p className="text-blue-700 text-sm sm:text-base">
                  Your AI-powered financial advisor
                </p>
              </div>
            </div>

            {/* Mobile Chats button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden bg-white border border-blue-200 shadow-sm rounded-xl px-3 py-2 flex items-center gap-2"
            >
              <Menu className="w-5 h-5" />
              Chats
            </button>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Desktop sidebar */}
        <div className="hidden md:block">
          <ChatHistory
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={setActiveSessionId}
            onNewChat={handleNewChat}
            onDeleteSession={handleDeleteSession}
          />
        </div>

        {/* Mobile sidebar drawer */}
        {sidebarOpen && (
          <div className="md:hidden absolute inset-0 z-40">
            <div className="absolute inset-0 bg-black/40" onClick={() => setSidebarOpen(false)} />
            <div className="absolute inset-y-0 left-0 w-[85%] max-w-sm">
              <div className="h-full relative">
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="absolute top-3 right-3 z-50 bg-blue-700 text-white rounded-xl p-2"
                  aria-label="Close chats"
                >
                  <X className="w-5 h-5" />
                </button>

                <ChatHistory
                  sessions={sessions}
                  activeSessionId={activeSessionId}
                  onSelectSession={(id) => {
                    setActiveSessionId(id);
                    setSidebarOpen(false);
                  }}
                  onNewChat={handleNewChat}
                  onDeleteSession={handleDeleteSession}
                />
              </div>
            </div>
          </div>
        )}

        {/* Main */}
        <main className="flex-1 overflow-hidden px-4 py-6 md:p-10">
          <div className="h-full max-w-5xl mx-auto">
            <ChatBot
              sessionId={activeSessionId}
              messages={activeMessages}
              setMessages={setActiveMessages}
              onSessionActivity={handleSessionActivity}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
