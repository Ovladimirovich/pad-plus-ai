import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

function MetricCard({ label, value, sub, color = 'text-text-primary' }) {
  return (
    <Card className="flex-1">
      <CardContent className="p-3 text-center">
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        <div className="text-xs text-text-secondary mt-0.5">{label}</div>
        {sub && <div className="text-xs text-text-secondary">{sub}</div>}
      </CardContent>
    </Card>
  );
}

function StatusBadge({ ok }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded ${ok ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
      {ok ? 'успех' : 'ошибка'}
    </span>
  );
}

const PHASE_CATEGORY = {
  safety: { icon: '🛡️', color: 'border-l-red-500', label: 'Safety' },
  intent: { icon: '🎯', color: 'border-l-blue-500', label: 'Reasoning' },
  rag: { icon: '📚', color: 'border-l-purple-500', label: 'Memory' },
  knowledge_graph: { icon: '🕸️', color: 'border-l-purple-500', label: 'Memory' },
  episodic: { icon: '📓', color: 'border-l-purple-500', label: 'Memory' },
  semantic: { icon: '💡', color: 'border-l-purple-500', label: 'Memory' },
  emotion: { icon: '😊', color: 'border-l-yellow-500', label: 'Emotion' },
  impulse: { icon: '⚡', color: 'border-l-yellow-500', label: 'Emotion' },
  persona: { icon: '🎭', color: 'border-l-pink-500', label: 'Identity' },
  roots: { icon: '🌱', color: 'border-l-green-500', label: 'Identity' },
  identity: { icon: '🪪', color: 'border-l-pink-500', label: 'Identity' },
  generate: { icon: '✍️', color: 'border-l-cyan-500', label: 'Generate' },
  truth_loop: { icon: '🔍', color: 'border-l-indigo-500', label: 'Reasoning' },
  evaluation: { icon: '🏆', color: 'border-l-amber-500', label: 'Reasoning' },
  response_guard: { icon: '🚧', color: 'border-l-red-500', label: 'Safety' },
  save_episode: { icon: '💾', color: 'border-l-gray-500', label: 'Memory' },
  extraction: { icon: '🪓', color: 'border-l-gray-500', label: 'Memory' },
};

function phaseMeta(phaseName) {
  return PHASE_CATEGORY[phaseName] || { icon: '⚙️', color: 'border-l-gray-500', label: 'Other' };
}

function WhyCard({ explanation }) {
  if (!explanation) return null;
  const [open, setOpen] = useState(false);
  const evalBlock = explanation.evaluation;
  return (
    <div className="mt-4 bg-card border border-border rounded-2xl overflow-hidden">
      <div
        role="button"
        tabIndex={0}
        onClick={() => setOpen(o => !o)}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setOpen(o => !o); }}
        className="px-4 py-3 cursor-pointer hover:bg-gray-800/30 select-none flex items-center justify-between"
      >
        <span className="text-base font-semibold text-text-primary">💡 Why this answer</span>
        <span className="text-text-secondary">{open ? '▾' : '▸'}</span>
      </div>
      {open && (
        <div className="p-4 space-y-3 text-sm border-t border-border">
          <div>
            <div className="font-semibold text-text-primary">🎯 Стратегия</div>
            <div className="text-text-secondary">{explanation.strategy_why}</div>
          </div>
          <div>
            <div className="font-semibold text-text-primary">⚙️ Фазы пайплайна</div>
            <div className="text-text-secondary">{Array.isArray(explanation.phases_ran) ? explanation.phases_ran.join(', ') : '—'}</div>
          </div>
          <div>
            <div className="font-semibold text-text-primary">🧠 Память / знания</div>
            <div className="text-text-secondary">
              {explanation.memory_used
                ? `RAG: ${explanation.memory_used.rag ?? 0}, Episodic: ${explanation.memory_used.episodic ?? 0}, Knowledge Graph: ${explanation.memory_used.knowledge_graph ?? 0}`
                : '—'}
            </div>
          </div>
          <div>
            <div className="font-semibold text-text-primary">📊 Уверенность</div>
            <div className="text-text-secondary">{explanation.confidence_why}</div>
          </div>
          <div>
            <div className="font-semibold text-text-primary">✅ Truth Loop</div>
            <div className="text-text-secondary">{explanation.truth_notes}</div>
          </div>
          {evalBlock && (
            <div>
              <div className="font-semibold text-text-primary">🏆 Evaluation</div>
              <div className="text-text-secondary">
                {evalBlock.summary
                  ? evalBlock.summary
                  : `Score: ${evalBlock.score ?? '—'}, Passed: ${evalBlock.passed ?? '—'}`}
              </div>
              {evalBlock.details && Object.keys(evalBlock.details).length > 0 && (
                <pre className="mt-1 text-xs whitespace-pre-wrap text-text-secondary">
                  {JSON.stringify(evalBlock.details, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MicroscopeTab({ navParams = {} }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const wsRef = useRef(null);

  const loadSnapshot = useCallback(async () => {
    try {
      const res = await apiFetch('/api/v1/xray/current');
      const d = await res.json();
      setData(d);
      setError('');
    } catch (e) {
      setError('Не удалось загрузить срез ответа: ' + e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSnapshot();

    const token = localStorage.getItem('auth_token');
    let ws = null;
    let retries = 0;
    const MAX_RETRIES = 5;
    let retryTimer = null;

    function connect() {
      try {
        const wsUrl = new URL('/api/v1/xray/ws', window.location.origin);
        if (token) wsUrl.searchParams.set('token', token);
        ws = new WebSocket(wsUrl.toString());
        wsRef.current = ws;
      } catch (e) {
        setConnected(false);
        scheduleRetry();
        return;
      }

      ws.onopen = () => {
        retries = 0;
        setConnected(true);
        ws.send(JSON.stringify({ type: 'subscribe', channels: ['trace', 'all'] }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'trace' && msg.data && msg.data.session) {
            const s = msg.data.session;
            setData(prev => ({
              ...(prev || {}),
              user_message: s.user_message,
              strategy: s.metadata?.strategy,
              intent: s.metadata?.intent,
              confidence: s.metadata?.confidence,
              truth_confidence: s.metadata?.truth_confidence,
              provider: s.metadata?.provider,
              model: s.metadata?.model,
              latency_ms: s.total_time_ms,
              success: s.metadata?.success,
              phases: s.events || prev?.phases || [],
              explanation: s.metadata?.explanation || prev?.explanation,
              evaluation: s.metadata?.explanation?.evaluation,
              status: 'ok',
            }));
            setLoading(false);
          } else if (msg.type === 'pipeline' || msg.type === 'all') {
            loadSnapshot();
          }
        } catch (e) {
          console.warn('Microscope WS parse error:', e);
        }
      };

      ws.onerror = () => setConnected(false);

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        if (retries < MAX_RETRIES) scheduleRetry();
      };
    }

    function scheduleRetry() {
      if (retryTimer) clearTimeout(retryTimer);
      retries++;
      const delay = Math.min(1000 * Math.pow(2, retries), 15000);
      retryTimer = setTimeout(connect, delay);
    }

    connect();

    return () => {
      if (retryTimer) clearTimeout(retryTimer);
      try {
        if (ws) { ws.onopen = null; ws.onmessage = null; ws.onerror = null; ws.onclose = null; ws.close(); }
      } catch {}
      wsRef.current = null;
    };
  }, [loadSnapshot]);

  const exportData = useExport();

  if (loading) return <div className="p-6 text-text-secondary">Загрузка «под микроскопом»…</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!data || data.status === 'no_data') {
    return (
      <div className="p-6 text-text-secondary">
        Нет данных. Отправьте запрос в чат, чтобы увидеть внутреннюю картину ответа.
        <button onClick={loadSnapshot} className="ml-3 px-3 py-1 rounded bg-primary text-white text-sm">Обновить</button>
      </div>
    );
  }

  const phases = Array.isArray(data.phases) ? data.phases : [];

  return (
    <div className="h-full overflow-y-auto p-2 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-text-primary">🔬 AI Under Microscope</h3>
          <p className="text-sm text-text-secondary">{data.user_message || '—'}</p>
        </div>
        <div className="flex gap-2 items-center">
          <span className={`text-xs px-2 py-0.5 rounded ${connected ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
            {connected ? '● Live' : '○ Polling'}
          </span>
          <button onClick={loadSnapshot} className="px-3 py-1 rounded bg-gray-700 text-white text-sm">Обновить</button>
          <button onClick={() => exportData.exportJSON(data, 'microscope.json')} className="px-3 py-1 rounded bg-primary text-white text-sm">Экспорт</button>
        </div>
      </div>

      <div className="flex gap-3 flex-wrap">
        <MetricCard label="Strategy" value={data.strategy || '—'} sub={data.intent || ''} />
        <MetricCard label="Confidence" value={data.confidence != null ? data.confidence.toFixed(2) : '—'} color="text-blue-400" />
        <MetricCard label="Truth" value={data.truth_confidence != null ? data.truth_confidence.toFixed(2) : '—'} color="text-purple-400" />
        <MetricCard label="Latency" value={data.latency_ms != null ? `${Math.round(data.latency_ms)}ms` : '—'} color="text-yellow-400" />
        <MetricCard label="Provider" value={data.provider || '—'} sub={data.model || ''} />
        <MetricCard label="Status" value={<StatusBadge ok={data.success} />} />
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Активные стадии пайплайна</CardTitle></CardHeader>
        <CardContent>
              {phases.length === 0 ? (
            <div className="text-text-secondary text-sm">Нет данных о фазах (in-memory сессия очищена).</div>
          ) : (
            <div className="space-y-1">
              {phases.map((p, i) => {
                const meta = phaseMeta(p.phase || p.stage);
                return (
                  <div key={i} className={`flex items-center gap-3 text-sm border-b border-l-4 border-border ${meta.color} pb-1 pl-2`}>
                    <span className="text-lg">{meta.icon}</span>
                    <span className="w-40 text-text-primary font-mono">{p.phase || p.stage}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-700/40 text-gray-300">{meta.label}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${p.status === 'success' ? 'bg-green-500/20 text-green-400' : p.status === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'}`}>{p.status}</span>
                    <span className="text-text-secondary">{p.duration_ms != null ? `${Math.round(p.duration_ms)}ms` : ''}</span>
                    {p.error && <span className="text-red-400 text-xs">{p.error}</span>}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <WhyCard explanation={data.explanation} />

      {data.evaluation && (
        <Card>
          <CardHeader><CardTitle className="text-base">📊 Evaluation summary</CardTitle></CardHeader>
          <CardContent className="text-sm text-text-secondary">
            <pre className="whitespace-pre-wrap">{JSON.stringify(data.evaluation, null, 2)}</pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
