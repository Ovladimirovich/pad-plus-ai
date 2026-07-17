import { useState, useRef, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/Card';
import { useWebSocket } from '../hooks/useWebSocket';
import CognitivePanel from './CognitivePanel';
import { apiFetch } from '../services/api';
import ChatMessage from './ChatMessage';
import ChatControls from './ChatControls';

const CHAT_STORAGE_KEY = 'chatMessages';

export function ChatInterface({ selectedModel, user }) {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = sessionStorage.getItem(CHAT_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [dialogId, setDialogId] = useState(() => sessionStorage.getItem('currentDialogId') || null);
  const messagesEndRef = useRef(null);
  const ws = useWebSocket();

  const [showMetrics, setShowMetrics] = useState(true);
  const [lastResponseMeta, setLastResponseMeta] = useState(null);

  useEffect(() => {
    try { sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages)); } catch {}
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (ws.messages.length > 0) {
      const lastMsg = ws.messages[ws.messages.length - 1];
      if (lastMsg.type === 'response') {
        setMessages(prev => {
          const updated = [...prev];
          const lastAssistant = updated.findIndex(m => m.role === 'assistant' && m.streaming);
          if (lastAssistant >= 0) {
            updated[lastAssistant] = {
              ...updated[lastAssistant],
              content: updated[lastAssistant].content + (lastMsg.content || ''),
            };
          }
          return updated;
        });
        setTimeout(scrollToBottom, 50);
      }
    }
  }, [ws.messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setStreaming(true);

    setMessages(prev => [...prev, { role: 'assistant', content: '', streaming: true }]);

    try {
      const response = await apiFetch('/api/v1/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage.content,
          key_id: selectedModel?.keyId || null,
          model: selectedModel?.id || 'auto',
          provider: selectedModel?.provider || null,
          dialog_id: dialogId,
          auto_mode: false,
          explain: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Ошибка отправки');
      }

      const data = await response.json();

      if (data.dialog_id) {
        setDialogId(data.dialog_id);
        sessionStorage.setItem('currentDialogId', data.dialog_id);
      }

      const perMsgMeta = {
        cognitive: data.cognitive,
        memory: data.memory,
        emotion: data.emotion,
        truth: data.truth,
        xray: data.xray,
        meta: data.meta,
        execution_time_ms: data.cognitive?.execution_time_ms,
      };

      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: data.text || 'Нет ответа',
          streaming: false,
          meta: perMsgMeta,
        };
        return updated;
      });

      setLastResponseMeta(perMsgMeta);
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: `Ошибка: ${err.message}`,
          streaming: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  return (
    <Card className="h-full flex flex-col min-h-0">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span>💬</span>
          Чат
          {selectedModel && (
            <span className="text-xs text-text-secondary font-normal ml-2">
              {selectedModel.name}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 min-h-0">
          {messages.length === 0 ? (
            <div className="text-center text-text-muted py-8">
              <div className="text-4xl mb-2">🤖</div>
              <div className="text-sm">Начните диалог с AI</div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage key={idx} msg={msg} dialogId={dialogId} />
            ))
          )}

          {lastResponseMeta?.meta?.fallback_used && (
            <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-center gap-2 text-yellow-500">
                <span className="text-lg">⚠️</span>
                <span className="text-sm font-medium">Использован fallback провайдера</span>
              </div>
              <div className="text-xs text-text-secondary mt-1 ml-4">
                {lastResponseMeta.meta.fallback_from && lastResponseMeta.meta.fallback_to && (
                  <>
                    <span className="line-through opacity-70">{lastResponseMeta.meta.fallback_from}</span>
                    <span> → </span>
                    <span className="font-medium text-green-500">{lastResponseMeta.meta.fallback_to}</span>
                  </>
                )}
              </div>
            </div>
          )}

          {showMetrics && lastResponseMeta && (
            <CognitivePanel {...lastResponseMeta} />
          )}

          <div ref={messagesEndRef} />
        </div>

        <ChatControls
          input={input}
          onInputChange={setInput}
          onSend={sendMessage}
          loading={loading}
          disabled={loading}
          selectedModel={selectedModel}
          showMetrics={showMetrics}
          onToggleMetrics={() => setShowMetrics(!showMetrics)}
        />

      </CardContent>
    </Card>
  );
}

export default ChatInterface;