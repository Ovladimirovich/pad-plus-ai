import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { apiFetch } from '../../services/api';

export default function TracesTab() {
  const [traces, setTraces] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replay, setReplay] = useState(null);

  const loadTraces = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/v1/experiments/traces?limit=50');
      if (res.ok) {
        const data = await res.json();
        setTraces(data.traces || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { loadTraces(); }, [loadTraces]);

  const selectTrace = async (id) => {
    setSelected(id);
    try {
      const res = await apiFetch(`/api/v1/experiments/traces/${encodeURIComponent(id)}`);
      if (res.ok) setDetail(await res.json());
    } catch (e) { console.error(e); }
  };

  return (
    <div className="flex gap-4 h-full">
      <div className="w-1/3 min-w-[300px] overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-text-primary">Trace History</h3>
          <button onClick={loadTraces} className="text-xs text-primary hover:underline">refresh</button>
        </div>
        {loading ? (
          <div className="text-text-secondary text-sm">Loading...</div>
        ) : traces.length === 0 ? (
          <div className="text-text-secondary text-sm">No traces yet.</div>
        ) : (
          <div className="space-y-2">
            {traces.map((t) => (
              <div
                key={t.id}
                onClick={() => selectTrace(t.id)}
                className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                  selected === t.id
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-text-primary">{t.id?.substring(0, 12)}...</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    t.success ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
                  }`}>{t.success ? 'ok' : 'err'}</span>
                </div>
                <div className="text-xs text-text-secondary mt-1 truncate">{t.user_message}</div>
                <div className="text-xs text-text-secondary mt-1">
                  {t.timestamp ? new Date(t.timestamp).toLocaleString() : ''}
                  {t.total_ms ? ` | ${t.total_ms.toFixed(0)}ms` : ''}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto">
        {!detail ? (
          <div className="text-text-secondary text-sm flex items-center justify-center h-64">
            Select a trace to view details
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-text-primary">Trace: {detail.id}</h3>
                <div className="text-xs text-text-secondary">
                  {detail.timestamp ? new Date(detail.timestamp).toLocaleString() : ''}
                  {detail.total_ms ? ` | ${detail.total_ms.toFixed(0)}ms` : ''}
                  {detail.model ? ` | ${detail.model}` : ''}
                </div>
              </div>
              <span className={`text-sm px-2 py-1 rounded ${
                detail.success ? 'bg-green-900/30 text-green-400' : 'bg-red-900/30 text-red-400'
              }`}>{detail.success ? 'Success' : 'Failed'}</span>
            </div>

            {detail.user_message && (
              <Card>
                <CardHeader><CardTitle>User Message</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-sm text-text-primary">{detail.user_message}</div>
                </CardContent>
              </Card>
            )}

            {detail.spans?.length > 0 && (
              <Card>
                <CardHeader><CardTitle>Timeline ({detail.spans.length} spans)</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-1">
                    {detail.spans.map((span, i) => (
                      <div key={i} className="flex items-center gap-3 py-1.5 border-b border-border/30 text-sm">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          span.status === 'ok' || span.status === 'success'
                            ? 'bg-green-500'
                            : span.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                        }`} />
                        <span className="text-text-primary w-32 font-medium truncate">{span.name}</span>
                        <span className="text-text-secondary w-20 text-right">{span.duration_ms?.toFixed(0)}ms</span>
                        <span className={`text-xs ${
                          span.status === 'ok' || span.status === 'success'
                            ? 'text-green-400' : span.status === 'error' ? 'text-red-400' : 'text-yellow-400'
                        }`}>{span.status}</span>
                        {span.error && <span className="text-xs text-red-400 truncate">{span.error}</span>}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {detail.response && (
              <Card>
                <CardHeader><CardTitle>Response</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-sm text-text-primary whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {detail.response}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex items-center gap-2">
              <button
                onClick={async () => {
                  try {
                    const res = await apiFetch('/api/v1/experiments/replay', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ request_id: detail.id }),
                    });
                    const data = await res.json();
                    if (data.status === 'ok') {
                      setReplay(data);
                    } else {
                      setReplay({ error: data.message });
                    }
                  } catch (e) {
                    setReplay({ error: e.message });
                  }
                }}
                className="px-3 py-1.5 rounded bg-primary text-white text-sm hover:bg-primary/80"
              >
                ⟳ Replay this trace
              </button>
            </div>

            {replay && (
              <Card>
                <CardHeader><CardTitle>Replay Result {replay.new_request_id ? `(→ ${replay.new_request_id.substring(0, 12)}…)` : ''}</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {replay.error && <div className="text-red-400">{replay.error}</div>}
                  {replay.response && (
                    <>
                      <div className="text-text-secondary">
                        strategy: <b className="text-text-primary">{replay.strategy}</b> |
                        confidence: <b className="text-text-primary">{replay.confidence?.toFixed?.(2)}</b> |
                        {replay.execution_time_ms != null && <> latency: <b className="text-text-primary">{Math.round(replay.execution_time_ms)}ms</b></>}
                      </div>
                      <div className="text-text-primary whitespace-pre-wrap max-h-48 overflow-y-auto border-t border-border pt-2">
                        {replay.response}
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
