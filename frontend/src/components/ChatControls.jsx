import { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { setImpulsePreset, PRESET_LABELS } from '../services/impulse';

const PRESETS = ['strict', 'balanced', 'creative'];

export default function ChatControls({
  input,
  onInputChange,
  onSend,
  loading,
  disabled,
  selectedModel,
  showMetrics,
  onToggleMetrics,
}) {
  const [currentPreset, setCurrentPreset] = useState('balanced');

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handlePresetChange = async (preset) => {
    setCurrentPreset(preset);
    try {
      await setImpulsePreset(preset);
    } catch (e) {
      console.warn('Failed to set impulse preset:', e);
    }
  };

  return (
    <div className="space-y-2">
      {/* Preset toggle */}
      <div className="flex gap-1 justify-center">
        {PRESETS.map((p) => {
          const info = PRESET_LABELS[p];
          const active = currentPreset === p;
          return (
            <button
              key={p}
              onClick={() => handlePresetChange(p)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                active
                  ? 'bg-primary text-white'
                  : 'bg-gray-800 text-text-secondary hover:bg-gray-700'
              }`}
              title={info.label}
            >
              {info.icon} {info.label}
            </button>
          );
        })}
      </div>

      {/* Input row */}
      <div className="flex gap-3">
        <input
          type="text"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Введите сообщение..."
          disabled={loading}
          className="flex-1 px-5 py-3 bg-gray-800 border border-border rounded-xl text-text-primary text-base focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
        />
        <Button
          onClick={onSend}
          loading={loading}
          disabled={!input.trim() || !selectedModel}
          className="px-6 py-3 text-lg"
        >
          {loading ? '...' : 'Отправить'}
        </Button>
        <Button
          variant="outline"
          onClick={onToggleMetrics}
          className={`px-4 ${showMetrics ? 'bg-primary text-white' : ''}`}
          title="Показать/скрыть когнитивные метрики"
        >
          🧠
        </Button>
      </div>
    </div>
  );
}
