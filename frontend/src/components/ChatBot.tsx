import { useEffect, useRef, useState } from 'react';
import { Send, Loader2, User } from 'lucide-react';
import novaAvatar from '../assets/novaAvatar.avif';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

type ClientType = 'cardholder' | 'merchant';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'https://binary-ruby-animation-bottle.trycloudflare.com';

type Props = {
  sessionId: string;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  // lets App update sidebar title + timestamps
  onSessionActivity?: (sessionId: string, maybeTitle?: string) => void;
};

export function ChatBot({ sessionId, messages, setMessages, onSessionActivity }: Props) {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const [clientType] = useState<ClientType>('cardholder');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  async function callBackend(userText: string): Promise<string> {
    const resp = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        client_type: clientType,
        session_id: sessionId,
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`Backend error ${resp.status}: ${errText || resp.statusText}`);
    }

    const data: { reply?: string } = await resp.json();
    return data.reply ?? '';
  }

  const handleSendMessage = async () => {
    const text = inputValue.trim();
    if (!text || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // sidebar title like screenshot: first user message becomes the title
    onSessionActivity?.(sessionId, text.slice(0, 24));
    onSessionActivity?.(sessionId);

    try {
      const reply = await callBackend(text);

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: reply || "Sorry — I didn't get a reply from the backend.",
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botResponse]);
      onSessionActivity?.(sessionId);
    } catch (e: any) {
      const botError: Message = {
        id: (Date.now() + 1).toString(),
        text:
          `I couldn't reach the backend.\n` +
          `- Is it running on ${API_BASE}?\n` +
          `- Does /chat respond?\n\n` +
          `Error: ${e?.message ?? String(e)}`,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botError]);
      onSessionActivity?.(sessionId);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-blue-200 overflow-hidden h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 md:space-y-6">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.sender === 'bot' && (
              <img
                src={novaAvatar}
                alt="Nova"
                className="w-10 h-10 rounded-full object-cover flex-shrink-0 mt-1"
              />
            )}

            <div
              className={`max-w-[85%] md:max-w-[70%] rounded-2xl px-5 py-4 ${
                message.sender === 'user'
                  ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white'
                  : 'bg-gradient-to-r from-blue-50 to-sky-50 text-blue-900 border border-blue-100'
              }`}
            >
              <p className="whitespace-pre-line text-[16px] leading-relaxed">{message.text}</p>
              <p
                className={`text-xs mt-2 ${
                  message.sender === 'user' ? 'text-blue-100' : 'text-blue-600'
                }`}
              >
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>

            {message.sender === 'user' && (
              <div className="w-10 h-10 rounded-full bg-gray-400 flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-6 h-6 text-gray-200" />
              </div>
            )}
          </div>
        ))}

        {/* Typing */}
        {isTyping && (
          <div className="flex gap-3 justify-start">
            <img
              src={novaAvatar}
              alt="Nova"
              className="w-10 h-10 rounded-full object-cover flex-shrink-0 mt-1"
            />
            <div className="bg-gradient-to-r from-blue-50 to-sky-50 text-blue-900 border border-blue-100 rounded-2xl px-5 py-4 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
              <span>Typing...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-blue-200 p-5 bg-gradient-to-r from-blue-50 to-sky-50 flex-shrink-0">
        <div className="flex flex-col sm:flex-row gap-3">
  <input
    type="text"
    value={inputValue}
    onChange={(e) => setInputValue(e.target.value)}
    onKeyDown={handleKeyDown}
    placeholder="Type your message..."
    className="w-full sm:flex-1 px-5 py-4 rounded-2xl border border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-[16px]"
    disabled={isTyping}
  />

  <button
    onClick={handleSendMessage}
    disabled={!inputValue.trim() || isTyping}
    className="w-full sm:w-auto sm:shrink-0 px-4 sm:px-7 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-2xl hover:from-blue-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
  >
    <Send className="w-4 h-4" />
    <span className="hidden sm:inline">Send</span>
    <span className="sm:hidden">Send</span>
  </button>
</div>
      </div>
    </div>
  );
}
