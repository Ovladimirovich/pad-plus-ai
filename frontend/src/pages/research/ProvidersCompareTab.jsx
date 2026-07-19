import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

const EVAL_ROWS = [
  ['overall', 'Overall'],
  ['completeness', 'Completeness'],
  ['consistency', 'Consistency'],
  ['safety', 'Safety'],
  ['confidence', 'Confidence'],
  ['latency_score', 'Latency'],
  ['novelty', 'Novelty'],
];

function ProviderRow({ r }) {
  const [open, setOpen] = useState(false);
  if (!r.success) {
    return (
      <tr className="border-b border-border/50 text-red-400 text-sm">
        <td className="py-2 pr-4">{r.provider}</td>
        <td className="py-2 pr-4" colSpan={5}>{r.error || 'ошибка'}</td>
      </tr>
    );
  }
  const ev = r.evaluation || {};
  return (
    <>
      <tr className="border-b border-border/50 text-sm hover:bg-gray-800/20 cursor-pointer" onClick={() => setOpen(o => !o)}>
        <td className="py-2 pr-4 text-text-primary font-medium">{r.provider}</td>
        <td className="py-2 pr-4 text-text-secondary">{r.model}</td>
        <td className="py-2 pr-4 text-right text-text-primary">{(ev.overall ?? 0).toFixed(2)}</td>
        <td className="py-2 pr-4 text-right text-text-primary">{(ev.confidence ?? 0).toFixed(2)}</td>
        <td className="py-2 pr-4 text-right text-text-primary">{r.latency_ms != null ? `${Math.round(r.latency_ms)}ms` : '—'}</td>
        <td className="py-2 pr-4 text-right text-text-secondary">{ev.safety != null ? ev.safety.toFixed(2) : '—'}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={6} className="bg-gray-900/40 p-3">
            <div className="text-xs text-text-secondary mb-1">Ответ:</div>
            <div className="text-sm text-text-primary whitespace-pre-wrap max-h-40 overflow-y-auto">{r.response}</div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function ProvidersCompareTab() {
  const [prompt, setPrompt] = useState('');
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState([]);
  const [seeds, setSeeds] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { exportJSON } = useExport();

  const loadKeys = useCallback(async () => {
    try {
      const res = await apiFetch('/api/v1/keys?limit=50');
      if (res.ok) {
        const data = await res.json();
        const items = data.data || data.keys || [];
        const mapped = items.map(k => ({ provider: k.provider, model: k.model_preference || 'auto', key_id: k.id, label: `${k.provider} / ${k.name || k.model_preference || 'auto'}` }));
        setProviders(mapped);
        setSelected(mapped.map(m => m.key_id));
      }
    } catch (e) { console.error(e); }
  }, []);

  const loadSeeds = useCallback(async () => {
    try {
      const res = await apiFetch('/api/v1/experiments/seed-experiments');
      if (res.ok) {
        const data = await res.json();
        setSeeds(data.seeds || []);
      }
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { loadKeys(); loadSeeds(); }, [loadKeys, loadSeeds]);

  const runCompare = async () => {
    setLoading(true);
    setError('');
    try {
      const chosen = providers.filter(p => selected.includes(p.key_id));
      const res = await apiFetch('/api/v1/experiments/compare-providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, providers: chosen }),
      });
      const data = await res.json();
      if (data.status === 'ok') setResult(data);
      else setError(data.detail || data.message || 'Ошибка сравнения');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const toggle = (id) => setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  const replaySelected = async () => {
    if (!result) return;
    for (const r of result.results.filter(x => x.success)) {
      try {
        await apiFetch('/api/v1/experiments/replay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_message: result.prompt, provider: r.provider }),
        });
      } catch (e) { console.error(e); }
    }
  };

  return (
    <div className="h-full overflow-y-auto p-2 space-y-4">
      <div>
        <h3 className="text-lg font-bold text-text-primary">⇄ Compare Providers</h3>
        <p className="text-sm text-text-secondary">Один prompt → разные провайдеры в одинаковых условиях.</p>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Промпт</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Введите prompt для сравнения…"
            className="w-full h-20 bg-gray-900 border border-border rounded p-2 text-sm text-text-primary"
          />
          <div className="flex flex-wrap gap-2">
            {seeds.map((s, i) => (
              <button
                key={i}
                onClick={() => setPrompt(s.prompt)}
                className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-text-secondary"
              >
                🌱 {s.prompt.slice(0, 40)}…
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Провайдеры ({selected.length} выбрано)</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {providers.length === 0 && <div className="text-sm text-text-secondary">Нет ключей. Добавьте в «Провайдеры».</div>}
          {providers.map(p => (
            <label key={p.key_id} className="flex items-center gap-2 text-sm cursor-pointer px-2 py-1 rounded bg-gray-800/50">
              <input type="checkbox" checked={selected.includes(p.key_id)} onChange={() => toggle(p.key_id)} />
              <span className="text-text-primary">{p.label}</span>
            </label>
          ))}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <button
          onClick={runCompare}
          disabled={loading || !prompt}
          className="px-4 py-2 rounded bg-primary text-white text-sm disabled:opacity-50 hover:bg-primary/80"
        >
          {loading ? 'Сравниваем…' : '▶ Run comparison'}
        </button>
        {result && (
          <>
            <button onClick={replaySelected} className="px-4 py-2 rounded bg-gray-700 text-white text-sm hover:bg-gray-600">⟳ Replay selected</button>
            <button onClick={() => exportJSON(result, 'compare-providers.json')} className="px-4 py-2 rounded bg-gray-700 text-white text-sm hover:bg-gray-600">JSON</button>
            <button
              onClick={() => exportCSV(
                (result.results || []).map(r => ({
                  provider: r.provider,
                  model: r.model,
                  quality: r.quality,
                  confidence: r.confidence,
                  latency_ms: r.latency,
                  safety: r.safety,
                })),
                'compare-providers.csv'
              )}
              className="px-4 py-2 rounded bg-gray-700 text-white text-sm hover:bg-gray-600"
            >CSV</button>
          </>
        )}
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      {result && (
        <Card>
          <CardHeader><CardTitle className="text-base">Результаты сравнения</CardTitle></CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-text-secondary border-b border-border">
                  <th className="text-left py-2 pr-4">Provider</th>
                  <th className="text-left py-2 pr-4">Model</th>
                  <th className="text-right py-2 pr-4">Quality</th>
                  <th className="text-right py-2 pr-4">Confidence</th>
                  <th className="text-right py-2 pr-4">Latency</th>
                  <th className="text-right py-2">Safety</th>
                </tr>
              </thead>
              <tbody>
                {result.results.map((r, i) => <ProviderRow key={i} r={r} />)}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
