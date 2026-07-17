import { apiFetch } from '../services/api';

function TruthBadge({ truthConfidence }) {
  if (truthConfidence == null) return null;
  let color, label;
  if (truthConfidence >= 0.8) { color = 'bg-green-500'; label = 'Высокая'; }
  else if (truthConfidence >= 0.5) { color = 'bg-yellow-500'; label = 'Средняя'; }
  else { color = 'bg-gray-500'; label = 'Низкая'; }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs text-white ${color}`}>
      <span>{Math.round(truthConfidence * 100)}%</span>
      <span className="opacity-80">{label}</span>
    </span>
  );
}

function WhyAnswerWidget({ meta }) {
  if (!meta) return null;
  const strategy = meta.cognitive?.strategy || '—';
  const impulse = meta.meta?.metadata?.impulse_primary || '—';
  const confidence = meta.cognitive?.confidence || 0;

  const strategyLabels = {
    simple: 'Прямая генерация',
    retrieval: 'Поиск и синтез',
    reasoning: 'Логический анализ',
    creative: 'Творческая генерация',
    analytical: 'Аналитическая обработка',
  };

  const impulseLabels = {
    understand: 'понять',
    improve: 'улучшить',
    protect: 'защитить',
    create: 'создать',
  };

  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-xs text-text-secondary">
      <span>Стратегия: <span className="text-text-primary font-medium">{strategyLabels[strategy] || strategy}</span></span>
      <span>Импульс: <span className="text-text-primary font-medium">{impulseLabels[impulse] || impulse}</span></span>
      <span>Уверенность: <span className="text-text-primary font-medium">{Math.round(confidence * 100)}%</span></span>
    </div>
  );
}

export default function ChatMessage({ msg, dialogId }) {
  const isUser = msg.role === 'user';
  const isAssistant = msg.role === 'assistant';

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-gray-800 text-text-primary'
        }`}
      >
        <div className="text-base whitespace-pre-wrap">{msg.content}</div>
        {msg.streaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse align-middle" />
        )}
        {isAssistant && !msg.streaming && msg.meta?.truth?.confidence != null && (
          <div className="mt-2 flex justify-end">
            <TruthBadge truthConfidence={msg.meta.truth.confidence} />
          </div>
        )}
      </div>

      {isAssistant && !msg.streaming && (
        <div className="mt-1 ml-1 w-full max-w-[80%]">
          <WhyAnswerWidget meta={msg.meta} />
          <div className="flex gap-1 mt-1">
            <button
              onClick={async () => {
                await apiFetch('/api/v1/feedback', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ rating: 1, dialog_id: dialogId }),
                }).catch(() => {});
              }}
              className="text-xs text-gray-500 hover:text-green-400 transition-colors px-1"
              title="Нравится"
            >👍</button>
            <button
              onClick={async () => {
                await apiFetch('/api/v1/feedback', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ rating: -1, dialog_id: dialogId }),
                }).catch(() => {});
              }}
              className="text-xs text-gray-500 hover:text-red-400 transition-colors px-1"
              title="Не нравится"
            >👎</button>
          </div>
        </div>
      )}
    </div>
  );
}
