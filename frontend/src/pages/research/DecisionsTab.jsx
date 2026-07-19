import { useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../../services/api';

const COMPONENT_LABELS = {
  provider_selector: '🔌 Provider',
  strategy_selector: '🧭 Strategy',
  meta_learner: '🧠 MetaLearner',
  evaluator: '📊 Evaluator',
  reflection: '🪞 Reflection',
  healing: '🧬 Healer',
};

export default function DecisionsTab({ initialComponent = '', since = '' }) {
  const [decisions, setDecisions] = useState([]);
  const [stats, setStats] = useState(null);
  const [component, setComponent] = useState(initialComponent);
  const [sinceTs, setSinceTs] = useState(since ? parseFloat(since) : null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Cross-integration: фильтр из hash-навигации (Anatomy ↔ Snapshot)
  useEffect(() => {
    if (initialComponent && initialComponent !== component) setComponent(initialComponent);
  }, [initialComponent]);
  useEffect(() => {
    if (since && parseFloat(since) !== sinceTs) setSinceTs(parseFloat(since));
  }, [since]);

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const params = new URLSearchParams();
      if (component) params.set('component', component);
      if (sinceTs) params.set('since', String(sinceTs));
      params.set('limit', '200');
      const [dRes, sRes] = await Promise.allSettled([
        apiFetch(`/api/v1/decisions?${params.toString()}`),
        apiFetch('/api/v1/decisions/stats'),
      ]);
      if (dRes.status === 'fulfilled' && dRes.value.ok) {
        const d = await dRes.value.json();
        setDecisions(d.decisions || []);
      }
      if (sRes.status === 'fulfilled' && sRes.value.ok) {
        setStats(await sRes.value.json());
      }
    } catch (e) { console.error(e); }
    setLoading(false);
    setRefreshing(false);
  }, [component, sinceTs]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, [load]);

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">Decision Log</h3>
        <div className="flex items-center gap-3">
          <span className={`text-xs transition-opacity ${refreshing ? 'opacity-100 text-primary' : 'opacity-0'}`}>
            ⟳ refreshing
          </span>
          <span className="text-xs text-text-secondary">auto 15s</span>
        </div>
      </div>

      {stats && (
        <div className="flex gap-3 flex-wrap items-center">
          <div className="p-2 rounded-lg bg-gray-800/40 border border-border text-center">
            <div className="text-lg font-bold text-text-primary">{stats.total}</div>
            <div className="text-xs text-text-secondary">Всего решений</div>
          </div>
          {Object.entries(stats.by_component || {}).map(([comp, count]) => (
            <button
              key={comp}
              onClick={() => setComponent(component === comp ? '' : comp)}
              className={`p-2 rounded-lg border text-center transition-colors ${
                component === comp ? 'border-primary bg-primary/10' : 'border-border hover:border-primary/50'
              }`}
            >
              <div className="text-sm font-bold text-text-primary">{count}</div>
              <div className="text-xs text-text-secondary">{COMPONENT_LABELS[comp] || comp}</div>
            </button>
          ))}
          {(component || sinceTs) && (
            <button
              onClick={() => { setComponent(''); setSinceTs(null); window.location.hash = ''; }}
              className="text-xs px-2 py-1 rounded bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
            >
              ✕ Сбросить фильтр
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div className="text-text-secondary text-sm">Loading...</div>
      ) : decisions.length === 0 ? (
        <div className="text-text-secondary text-sm">No decisions logged yet.</div>
      ) : (
        <div className="space-y-2">
          {decisions.map((d) => (
            <div
              key={d.id}
              className="border border-border rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpanded(expanded === d.id ? null : d.id)}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-800/30 text-left"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-xs text-text-secondary">{COMPONENT_LABELS[d.component] || d.component}</span>
                  <span className="text-sm font-medium text-text-primary">{d.selected}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-text-secondary">{d.decision_type}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`text-xs ${d.confidence >= 0.7 ? 'text-green-400' : d.confidence >= 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {d.confidence?.toFixed(2) ?? '—'}
                  </span>
                  <span className="text-xs text-text-secondary">
                    {d.timestamp ? new Date(d.timestamp * 1000).toLocaleTimeString() : ''}
                  </span>
                  <span className={`text-xs transition-transform ${expanded === d.id ? 'rotate-90' : ''}`}>▶</span>
                </div>
              </button>
              {expanded === d.id && (
                <div className="px-3 py-2 border-t border-border bg-gray-900/30 text-sm space-y-2">
                  <div>
                    <span className="text-text-secondary text-xs">Причина: </span>
                    <span className="text-text-primary">{d.reason}</span>
                  </div>
                  {d.input_factors && Object.keys(d.input_factors).length > 0 && (
                    <div>
                      <div className="text-xs text-text-secondary mb-1">Факторы:</div>
                      <pre className="text-xs text-text-primary bg-gray-800/40 rounded p-2 overflow-x-auto">
                        {JSON.stringify(d.input_factors, null, 2)}
                      </pre>
                    </div>
                  )}
                  {d.candidates && d.candidates.length > 0 && (
                    <div>
                      <div className="text-xs text-text-secondary mb-1">Рассмотренные варианты:</div>
                      <div className="flex flex-col gap-1">
                        {d.candidates.map((c, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs">
                            <span className="text-text-primary w-32 truncate">{c.name}</span>
                            <span className="text-text-secondary">score: {c.score}</span>
                            {c.role && <span className="text-text-secondary">({c.role})</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {d.meta && Object.keys(d.meta).length > 0 && (
                    <div>
                      <div className="text-xs text-text-secondary mb-1">Meta:</div>
                      <pre className="text-xs text-text-primary bg-gray-800/40 rounded p-2 overflow-x-auto">
                        {JSON.stringify(d.meta, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
