import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

export default function RunsTab() {
  const [runs, setRuns] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [snapshots, setSnapshots] = useState([]);
  const [snapshotsOpen, setSnapshotsOpen] = useState(false);
  const [snapshotDetail, setSnapshotDetail] = useState(null);
  const { exportJSON, exportCSV, exportReport } = useExport();

  const loadRuns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/v1/experiments/runs');
      if (res.ok) {
        const data = await res.json();
        setRuns(data.runs || []);
      }
    } catch (e) { console.error('Failed to load runs:', e); }
    setLoading(false);
  }, []);

  useEffect(() => { loadRuns(); }, [loadRuns]);

  const loadSnapshots = useCallback(async () => {
    try {
      const res = await apiFetch('/api/v1/experiments/snapshots');
      if (res.ok) {
        const data = await res.json();
        setSnapshots(data.snapshots || []);
      }
    } catch (_) {}
  }, []);

  const captureSnapshot = async () => {
    try {
      const res = await apiFetch('/api/v1/experiments/snapshot', { method: 'POST' });
      if (res.ok) {
        await loadSnapshots();
        setSnapshotsOpen(true);
      }
    } catch (e) { console.error(e); }
  };

  const selectRun = async (name) => {
    setSelected(name);
    setSnapshotDetail(null);
    try {
      const res = await apiFetch(`/api/v1/experiments/runs/${encodeURIComponent(name)}`);
      if (res.ok) {
        const d = await res.json();
        setDetail(d);
        const sid = d.data ? d.data.snapshot_id : null;
        const cfgSid = d.config ? d.config.snapshot_id : null;
        const finalSid = sid || cfgSid;
        if (finalSid) {
          const sRes = await apiFetch(`/api/v1/experiments/snapshots/${finalSid}`);
          if (sRes.ok) {
            const sData = await sRes.json();
            setSnapshotDetail(sData.snapshot);
          }
        }
      }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="flex gap-4 h-full">
      <div className="w-1/3 min-w-[300px] overflow-y-auto flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-text-primary">Experiment Runs</h3>
          <div className="flex gap-2">
            <button onClick={captureSnapshot} className="text-xs text-primary hover:underline">+ snapshot</button>
            <button onClick={() => exportCSV(runs, 'experiment-runs.csv')}
              className="text-xs text-primary hover:underline">CSV</button>
            <button onClick={() => { loadRuns(); loadSnapshots(); }} className="text-xs text-primary hover:underline">refresh</button>
          </div>
        </div>

        {loading ? (
          <div className="text-text-secondary text-sm">Loading...</div>
        ) : runs.length === 0 ? (
          <div className="text-text-secondary text-sm">No runs yet.</div>
        ) : (
          <div className="space-y-2 flex-1 overflow-y-auto">
            {runs.map((run) => (
              <div
                key={run.name}
                onClick={() => selectRun(run.name)}
                className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                  selected === run.name
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="text-sm font-medium text-text-primary">{run.display_name}</div>
                <div className="text-xs text-text-secondary mt-1">
                  {run.timestamp ? new Date(run.timestamp).toLocaleString() : run.name}
                </div>
                <div className="flex gap-2 mt-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-green-900/30 text-green-400">
                    {run.successful}/{run.total_runs} ok
                  </span>
                  {run.provider && (
                    <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-text-secondary">
                      {run.provider}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-2 pt-2 border-t border-border">
          <button
            onClick={() => { setSnapshotsOpen(!snapshotsOpen); if (!snapshots.length) loadSnapshots(); }}
            className="flex items-center gap-2 w-full px-1 py-2 text-xs text-text-secondary hover:text-text-primary"
          >
            <span className={`text-xs transition-transform ${snapshotsOpen ? 'rotate-90' : ''}`}>▶</span>
            Snapshots ({snapshots.length})
          </button>
          {snapshotsOpen && (
            <div className="mt-1 space-y-1 max-h-40 overflow-y-auto">
              {snapshots.map((s) => (
                <div
                  key={s.id}
                  onClick={async () => {
                    const res = await apiFetch(`/api/v1/experiments/snapshots/${s.id}`);
                    if (res.ok) {
                      const d = await res.json();
                      setSnapshotDetail(d.snapshot || s);
                    }
                  }}
                  className="p-2 rounded cursor-pointer border border-border hover:border-primary/50 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-text-primary font-medium truncate">{s.label}</div>
                    {s.decision_count != null && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const ts = s.timestamp ? new Date(s.timestamp).getTime() / 1000 : '';
                          window.location.hash = `research?component=&since=${ts}`;
                        }}
                        className="text-xs px-1.5 py-0.5 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/40 transition-colors"
                        title="Решения после снэпшота"
                      >
                        📋 {s.decision_count}
                      </button>
                    )}
                  </div>
                  <div className="text-text-secondary">{s.timestamp ? new Date(s.timestamp).toLocaleString() : s.id}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {!detail ? (
          <div className="text-text-secondary text-sm flex items-center justify-center h-64">
            Select a run to view details
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-medium text-text-primary">{detail.name}</h3>
                {detail.data && detail.data.provider && (
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-text-secondary">
                    {detail.data.provider}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                {detail.report && (
                  <button onClick={() => exportReport(detail.report, `${detail.name}-report.md`)}
                    className="text-xs text-primary hover:underline">Report</button>
                )}
                <button onClick={() => exportJSON(detail, `${detail.name}.json`)}
                  className="text-xs text-primary hover:underline">JSON</button>
              </div>
            </div>

            {detail.data && detail.data.results && (
              <Card>
                <CardHeader><CardTitle>Results</CardTitle></CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-text-secondary border-b border-border">
                          <th className="text-left py-2 pr-4">Profile</th>
                          <th className="text-left py-2 pr-4">Question</th>
                          <th className="text-left py-2 pr-4">Status</th>
                          <th className="text-right py-2">Length</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.data.results.map((r, i) => (
                          <tr key={i} className="border-b border-border/50 hover:bg-gray-800/30">
                            <td className="py-2 pr-4 text-text-primary font-medium">{r.profile}</td>
                            <td className="py-2 pr-4 text-text-secondary max-w-md truncate">{r.question}</td>
                            <td className="py-2 pr-4">{r.success ? '✅' : '❌'}</td>
                            <td className="py-2 text-right text-text-secondary">{(r.response || '').length}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {snapshotDetail && (
              <Card>
                <CardHeader className="flex items-center justify-between">
                  <CardTitle>System Snapshot: {snapshotDetail.label}</CardTitle>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        const ts = snapshotDetail.timestamp ? new Date(snapshotDetail.timestamp).getTime() / 1000 : '';
                        window.location.hash = `research?since=${ts}`;
                      }}
                      className="text-xs px-2 py-1 rounded bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/40 transition-colors"
                    >
                      📋 Решения
                    </button>
                    <button
                      onClick={() => { window.location.hash = `anatomy?snapshot=${snapshotDetail.id}`; }}
                      className="text-xs px-2 py-1 rounded bg-purple-600/20 text-purple-300 hover:bg-purple-600/40 transition-colors"
                    >
                      🧬 Anatomy
                    </button>
                    <span className="text-xs text-text-secondary">{snapshotDetail.id}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="p-2 rounded bg-gray-800/40 text-center">
                      <div className="text-xs text-text-secondary">Pipeline</div>
                      <div className="text-sm font-medium text-text-primary">
                        {(snapshotDetail.pipeline_phase_order || []).length} phases
                      </div>
                      <div className="text-xs text-text-secondary">{snapshotDetail.pipeline_state}</div>
                    </div>
                    <div className="p-2 rounded bg-gray-800/40 text-center">
                      <div className="text-xs text-text-secondary">PAD</div>
                      <div className="text-sm font-mono text-text-primary">
                        {snapshotDetail.pad && snapshotDetail.pad.pleasure !== undefined
                          ? `${snapshotDetail.pad.pleasure.toFixed(2)} / ${snapshotDetail.pad.arousal.toFixed(2)} / ${snapshotDetail.pad.dominance.toFixed(2)}`
                          : '—'}
                      </div>
                      <div className="text-xs text-text-secondary">P / A / D</div>
                    </div>
                    <div className="p-2 rounded bg-gray-800/40 text-center">
                      <div className="text-xs text-text-secondary">Persona</div>
                      <div className="text-sm font-medium text-text-primary">
                        {Object.keys(snapshotDetail.persona_traits || {}).length} traits
                      </div>
                      <div className="text-xs text-text-secondary">
                        {(snapshotDetail.impulse && (snapshotDetail.impulse.label || snapshotDetail.impulse.primary)) || '—'}
                      </div>
                    </div>
                  </div>
                  <pre className="text-xs text-text-secondary overflow-x-auto max-h-48">
                    {JSON.stringify(snapshotDetail, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}

            {detail.config && (
              <Card>
                <CardHeader><CardTitle>Config</CardTitle></CardHeader>
                <CardContent>
                  <pre className="text-xs text-text-secondary overflow-x-auto max-h-64">
                    {JSON.stringify(detail.config, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
