import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import BarChart from './charts/BarChart';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

function ProfileCard({ profile, comp, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen);
  const metrics = comp?.metrics || {};
  const hasData = Object.keys(metrics).length > 0;
  const isEmpty = !hasData && comp?.error;

  return (
    <Card>
      <div
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-800/30 select-none"
      >
        <div className="flex items-center gap-3">
          <span className={`text-xs transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
          <span className="text-sm font-medium text-text-primary">Profile: {profile}</span>
          {isEmpty && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-yellow-900/30 text-yellow-400">
              {comp.error}
            </span>
          )}
          {hasData && (
            <span className="text-xs text-text-secondary">
              {Object.keys(metrics).length} metrics
            </span>
          )}
        </div>
      </div>
      {open && (
        <CardContent className="border-t border-border">
          {isEmpty ? (
            <div className="text-sm text-text-secondary py-2">No comparison data for this profile.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-text-secondary border-b border-border">
                  <th className="text-left py-2 pr-4">Metric</th>
                  <th className="text-right py-2 pr-4">Baseline</th>
                  <th className="text-right py-2 pr-4">Treatment</th>
                  <th className="text-right py-2 pr-4">Delta</th>
                  <th className="text-right py-2">Delta%</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics).map(([name, m]) => (
                  <tr key={name} className="border-b border-border/50">
                    <td className="py-2 pr-4 text-text-primary">{name}</td>
                    <td className="py-2 pr-4 text-right text-text-secondary">{m.baseline}</td>
                    <td className="py-2 pr-4 text-right text-text-secondary">{m.treatment}</td>
                    <td className={`py-2 pr-4 text-right ${
                      m.delta > 0 ? 'text-green-400' : m.delta < 0 ? 'text-red-400' : 'text-text-secondary'
                    }`}>
                      {m.delta > 0 ? '+' : ''}{m.delta.toFixed(3)}
                    </td>
                    <td className={`py-2 text-right ${
                      m.pct_change > 0 ? 'text-green-400' : m.pct_change < 0 ? 'text-red-400' : 'text-text-secondary'
                    }`}>
                      {m.pct_change > 0 ? '+' : ''}{m.pct_change.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      )}
    </Card>
  );
}

export default function CompareTab() {
  const [runs, setRuns] = useState([]);
  const [baseline, setBaseline] = useState('');
  const [treatment, setTreatment] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [snapshots, setSnapshots] = useState({});
  const { exportJSON } = useExport();

  const runCompare = async () => {
    if (!baseline || !treatment) return;
    try {
      const res = await apiFetch(
        `/api/v1/experiments/compare?baseline=${encodeURIComponent(baseline)}&treatment=${encodeURIComponent(treatment)}`
      );
      if (res.ok) setResult(await res.json());
      // Загружаем snapshot-мета для обоих прогонов
      for (const name of [baseline, treatment]) {
        try {
          const rRes = await apiFetch(`/api/v1/experiments/runs/${encodeURIComponent(name)}`);
          if (rRes.ok) {
            const d = await rRes.json();
            const sid = d.data?.snapshot_id || d.config?.snapshot_id;
            if (sid) {
              const sRes = await apiFetch(`/api/v1/experiments/snapshots/${sid}`);
              if (sRes.ok) {
                const sData = await sRes.json();
                setSnapshots(prev => ({ ...prev, [name]: sData.snapshot }));
              }
            }
          }
        } catch (_) {}
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch('/api/v1/experiments/runs');
        if (res.ok) {
          const data = await res.json();
          setRuns(data.runs || []);
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    })();
  }, []);

  const allMetrics = result?.profiles?.length
    ? [...new Set(
        result.profiles.flatMap(p => Object.keys(result.comparisons?.[p]?.metrics || {}))
      )]
    : [];

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-xs text-text-secondary mb-1">Baseline</label>
          <select
            value={baseline}
            onChange={(e) => setBaseline(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-border text-text-primary text-sm"
          >
            <option value="">-- select --</option>
            {runs.map((r) => (
              <option key={r.name} value={r.name}>{r.display_name}</option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="block text-xs text-text-secondary mb-1">Treatment</label>
          <select
            value={treatment}
            onChange={(e) => setTreatment(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-border text-text-primary text-sm"
          >
            <option value="">-- select --</option>
            {runs.map((r) => (
              <option key={r.name} value={r.name}>{r.display_name}</option>
            ))}
          </select>
        </div>
        <button
          onClick={runCompare}
          disabled={!baseline || !treatment}
          className="px-4 py-2 bg-primary text-white rounded-lg text-sm disabled:opacity-50"
        >
          Compare
        </button>
      </div>

      {result && result.status === 'no_data' && (
        <Card>
          <CardHeader><CardTitle>Нет данных для сравнения</CardTitle></CardHeader>
          <CardContent className="p-3">
            <p className="text-sm text-text-primary mb-3">{result.message}</p>
            <div className="flex gap-4 text-xs text-text-secondary">
              <div>
                <span className="font-medium text-text-primary">Baseline ({result.baseline}):</span>
                <pre className="mt-1">{JSON.stringify(result.baseline_meta, null, 2)}</pre>
              </div>
              <div>
                <span className="font-medium text-text-primary">Treatment ({result.treatment}):</span>
                <pre className="mt-1">{JSON.stringify(result.treatment_meta, null, 2)}</pre>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {result && (!result.status || result.status === 'ok') && (
        <div className="space-y-6">
          {/* Snapshot meta row */}
          <div className="flex gap-3">
            {[result.baseline, result.treatment].map((name, i) => {
              const snap = snapshots[name];
              return (
                <div key={name} className="flex-1 p-3 rounded-lg bg-gray-800/40 border border-border">
                  <div className="text-xs text-text-secondary">{i === 0 ? 'Baseline' : 'Treatment'}</div>
                  <div className="text-sm font-medium text-text-primary truncate">{name}</div>
                  {snap ? (
                    <div className="mt-1 flex flex-wrap gap-1">
                      <span className="text-xs px-1.5 py-0.5 rounded bg-primary/20 text-primary">
                        {snap.pipeline_phase_order?.length || 0} phases
                      </span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-text-secondary">
                        {snap.pipeline_state}
                      </span>
                      {snap.pad?.pleasure !== undefined && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-text-secondary">
                          PAD: {snap.pad.pleasure.toFixed(2)}/{snap.pad.arousal.toFixed(2)}/{snap.pad.dominance.toFixed(2)}
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-text-secondary mt-1">no snapshot</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Summary bar chart — latency delta per profile */}
          {result.profiles?.length > 1 && allMetrics.includes('latency_ms') && (
            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Latency Delta by Profile</CardTitle>
                <button onClick={() => exportJSON(result, 'comparison.json')}
                  className="text-xs text-primary hover:underline">Export JSON</button>
              </CardHeader>
              <CardContent className="p-3">
                <BarChart
                  data={result.profiles.map(p => ({
                    label: p,
                    value: Math.abs(result.comparisons?.[p]?.metrics?.latency_ms?.delta || 0),
                    color: (result.comparisons?.[p]?.metrics?.latency_ms?.delta || 0) > 0 ? '#ef4444' : '#22c55e',
                  }))}
                  width={500} height={140}
                />
              </CardContent>
            </Card>
          )}

          {/* Per-profile collapsible cards */}
          <div className="space-y-2">
            {result.profiles?.map((profile) => {
              const comp = result.comparisons?.[profile];
              if (!comp) return null;
              const defaultOpen = Object.keys(comp.metrics || {}).length > 0;
              return (
                <ProfileCard key={profile} profile={profile} comp={comp} defaultOpen={defaultOpen} />
              );
            })}
          </div>

          {/* Per-profile summary */}
          {result.profiles?.length > 1 && (
            <Card>
              <CardHeader><CardTitle>Per-Profile Summary</CardTitle></CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-text-secondary border-b border-border">
                        <th className="text-left py-2 px-3">Profile</th>
                        <th className="text-right py-2 px-3">Latency Δ</th>
                        <th className="text-right py-2 px-3">Confidence Δ</th>
                        <th className="text-right py-2 px-3">Length Δ</th>
                        <th className="text-right py-2 px-3">Success Δ</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.profiles.map(p => {
                        const m = result.comparisons?.[p]?.metrics || {};
                        return (
                          <tr key={p} className="border-b border-border/30 hover:bg-gray-800/30">
                            <td className="py-2 px-3 text-text-primary font-medium">{p}</td>
                            {['latency_ms', 'confidence', 'response_length', 'success'].map(k => {
                              const v = m[k]?.delta;
                              if (v == null) return <td key={k} className="py-2 px-3 text-right text-text-secondary">—</td>;
                              return (
                                <td key={k} className={`py-2 px-3 text-right ${
                                  v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-text-secondary'
                                }`}>
                                  {v > 0 ? '+' : ''}{k === 'success' ? v : v.toFixed(2)}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
