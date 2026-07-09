import { useState } from 'react';
import { apiFetch } from '../services/api';

const PAD_LABELS = [
  { key: 'pleasure', label: 'Удовольствие', emoji: '😊' },
  { key: 'arousal', label: 'Возбуждение', emoji: '⚡' },
  { key: 'dominance', label: 'Доминирование', emoji: '💪' },
];

export function FeedbackWidget({ dialogId, messageId, onSubmitted }) {
  const [values, setValues] = useState({ pleasure: 0.5, arousal: 0.5, dominance: 0.5 });
  const [sending, setSending] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (sending || submitted) return;
    setSending(true);
    try {
      await apiFetch('/api/v1/feedback/pad', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dialog_id: dialogId,
          message_id: messageId,
          ...values,
        }),
      });
      setSubmitted(true);
      onSubmitted?.();
    } catch {
      setSubmitted(true);
    } finally {
      setSending(false);
    }
  };

  if (submitted) {
    return (
      <div className="text-xs text-green-400 mt-1 px-1">
        Спасибо за отзыв!
      </div>
    );
  }

  return (
    <div className="mt-2 p-3 bg-gray-800/50 border border-gray-700/50 rounded-xl">
      <div className="text-xs text-text-muted mb-2 font-medium">
        Как вам ответ?
      </div>
      <div className="space-y-2">
        {PAD_LABELS.map(({ key, label, emoji }) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-sm w-6 text-center">{emoji}</span>
            <span className="text-xs text-text-secondary w-28 shrink-0">{label}</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={values[key]}
              onChange={(e) => setValues(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
              className="flex-1 h-1.5 accent-primary cursor-pointer"
            />
            <span className="text-xs text-text-muted w-8 text-right font-mono">
              {Math.round(values[key] * 100)}
            </span>
          </div>
        ))}
      </div>
      <button
        onClick={handleSubmit}
        disabled={sending}
        className="mt-2 w-full text-xs py-1.5 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 transition-colors disabled:opacity-50"
      >
        {sending ? 'Отправка...' : 'Отправить отзыв'}
      </button>
    </div>
  );
}

export default FeedbackWidget;
