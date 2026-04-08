"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { buildInitialGreeting } from "../../lib/buildChatContext";

function parseMarkdownBold(text) {
  // Convert **bold** to <strong> inline
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i} className="text-foreground font-semibold">{part.slice(2, -2)}</strong>
      : part
  );
}

function ChatMessage({ role, content }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-(--color-primary)/20 border border-(--color-primary)/40 flex items-center justify-center shrink-0 mr-2 mt-0.5">
          <span className="text-[9px] font-bold text-(--color-primary)">VT</span>
        </div>
      )}
      <div
        className={`max-w-[82%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-(--color-primary)/10 border border-(--color-primary)/25 text-foreground rounded-br-sm"
            : "bg-slate-50 border border-slate-200 text-(--color-muted) rounded-bl-sm"
        }`}
      >
        {parseMarkdownBold(content)}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="w-6 h-6 rounded-full bg-(--color-primary)/20 border border-(--color-primary)/40 flex items-center justify-center shrink-0 mr-2 mt-0.5">
        <span className="text-[9px] font-bold text-(--color-primary)">VT</span>
      </div>
      <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1 items-center">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-(--color-primary)/60"
            style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function TwinChatPanel({ profile, input, result, isOpen, onClose }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const abortRef = useRef(null);

  // Initialize with greeting on open
  useEffect(() => {
    if (isOpen && messages.length === 0 && result) {
      const greeting = buildInitialGreeting(profile, result);
      setMessages([{ role: "assistant", content: greeting }]);
    }
  }, [isOpen, result]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  useEffect(() => {
    if (isOpen) setTimeout(() => textareaRef.current?.focus(), 100);
  }, [isOpen]);

  const sendMessage = useCallback(async () => {
    const text = inputValue.trim();
    if (!text || isStreaming) return;
    setError(null);
    setInputValue("");

    const userMsg = { role: "user", content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsStreaming(true);

    abortRef.current = new AbortController();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortRef.current.signal,
        body: JSON.stringify({
          messages: newMessages,
          profile,
          input,
          result,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Request failed" }));
        throw new Error(err.error || `Error ${res.status}`);
      }

      // Stream SSE response
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();
          if (data === "[DONE]") break;
          try {
            const parsed = JSON.parse(data);
            const delta = parsed?.choices?.[0]?.delta?.content;
            if (delta) {
              assistantContent += delta;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = { role: "assistant", content: assistantContent };
                return updated;
              });
            }
          } catch {
            // skip malformed SSE lines
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      setError(err.message || "Something went wrong. Please try again.");
      setMessages((prev) => prev.filter((m) => !(m.role === "assistant" && m.content === "")));
    } finally {
      setIsStreaming(false);
    }
  }, [inputValue, messages, isStreaming, profile, input, result]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleClose = () => {
    abortRef.current?.abort();
    onClose?.();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-20 right-4 md:right-6 z-50 w-[min(420px,calc(100vw-2rem))] flex flex-col rounded-2xl border border-(--color-primary)/20 bg-white shadow-2xl shadow-slate-900/10"
      style={{ height: "min(560px, calc(100vh - 8rem))" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 shrink-0 bg-linear-to-r from-emerald-50 to-emerald-50 rounded-t-2xl">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-(--color-primary)/20 border border-(--color-primary)/40 flex items-center justify-center">
            <span className="text-xs font-bold text-(--color-primary)">VT</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground leading-none">Your Digital Twin</p>
            <p className="text-[10px] text-(--color-muted) mt-0.5">AI health assistant · Powered by Groq</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-(--color-muted) hover:text-foreground hover:bg-slate-100 transition-colors"
          aria-label="Close chat"
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-4 min-h-0">
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
        {isStreaming && messages[messages.length - 1]?.content === "" && <TypingIndicator />}
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-600 mb-2" role="alert">
            {error}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-3 pb-3 pt-2 border-t border-slate-100 shrink-0 bg-slate-50/50 rounded-b-2xl">
        <div className="flex gap-2 items-end">
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your health report…"
            rows={1}
            disabled={isStreaming}
            className="flex-1 resize-none rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-foreground placeholder:text-(--color-muted-dim) focus:border-(--color-primary) focus:outline-none focus:ring-2 focus:ring-(--color-primary)/15 disabled:opacity-50 leading-relaxed"
            style={{ maxHeight: "96px", overflowY: "auto" }}
            aria-label="Chat message"
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={!inputValue.trim() || isStreaming}
            className="shrink-0 w-9 h-9 rounded-xl border border-(--color-primary)/50 bg-(--color-primary)/10 flex items-center justify-center text-(--color-primary) transition-all hover:bg-(--color-primary)/20 hover:border-(--color-primary) disabled:opacity-40 disabled:pointer-events-none"
            aria-label="Send message"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
        <p className="text-[10px] text-(--color-muted)/50 mt-1.5 text-center">Press Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
