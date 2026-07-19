import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import BarChart from './charts/BarChart';
import Sparkline from './charts/Sparkline';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

function ScoreBar({ label, value, max = 1 }) {
  const pct = Math.min((value / max) * 100, 100);
  const color = value >= 0.8 ? '#22c55e' : value >= 0.5 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-secondary w-24 text-right">{label}</span>
      <div className="flex-1 h-3 rounded-full bg-gray-700 overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs font-medium text-text-primary w-10 text-right">{value.toFixed(2)}</span>
    </div>
  );
}

export default function EvalTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { exportJSON, exportCSV } = useExport();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/v1/experiments/evals?limit=500');
      if (res.ok) setData(await res.json());
    } catch (e) { console.error('Eval load failed:', e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) {
    return <div className="text-text-secondary text-sm py-8 text-center">Loading evaluation data...</div>;
  }

  if (!data || data.total_entries === 0) {
    return (
      <div className="text-text-secondary text-sm py-8 text-center">
        No evaluation data found. Run the pipeline with evaluation phase enabled.
      </div>
    );
  }

  const avgs = data.averages || {};
  const dims = ['completeness', 'consistency', 'safety', 'confidence', 'latency_score', 'novelty', 'overall'];
  const dimLabels = {
    completeness: 'Completeness',
    consistency: 'Consistency',
    safety: 'Safety',
    confidence: 'Confidence',
    latency_score: 'Latency',
    novelty: 'Novelty',
    overall: 'Overall',
  };

  const barData = dims.filter(k => avgs[k] != null).map(k => ({
    label: dimLabels[k] || k,
    value: avgs[k],
  }));

  const ts = data.timeseries || [];
  const tsData = ts.map(d => ({ label: d.date.slice(5), value: d.overall }));

  const stratData = Object.entries(data.by_strategy || {}).map(([name, s]) => ({
    label: name,
    value: s.averages?.overall || 0,
    count: s.count,
    color: name === 'simple' ? '#22c55e' : name === 'reasoning' ? '#3b82f6' : name === 'retrieval' ? '#a855f7' : '#f59e0b',
  }));

  const providerData = Object.entries(data.by_provider || {}).map(([name, s]) => ({
    label: name,
    value: s.averages?.overall || 0,
    count: s.count,
  }));

  const recent = data.recent || [];

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">Evaluation Scores</h3>
        <div className="flex gap-2">
          <button onClick={() => exportJSON(data, 'eval-scores.json')}
            className="text-xs text-primary hover:underline">Export JSON</button>
          <button onClick={() => exportCSV(recent.map(r => ({ id: r.id, ...r.evaluation, strategy: r.strategy, provider: r.provider })), 'eval-scores.csv')}
            className="text-xs text-primary hover:underline">Export CSV</button>
        </div>
      </div>

      {/* Counter row */}
      <div className="flex gap-3">
        <div className="flex-1 p-3 rounded-lg bg-gray-800/50 border border-border text-center">
          <div className="text-2xl font-bold text-primary">{data.total_entries}</div>
          <div className="text-xs text-text-secondary mt-0.5">Evaluated Dialogs</div>
        </div>
        <div className="flex-1 p-3 rounded-lg bg-gray-800/50 border border-border text-center">
          <div className="text-2xl font-bold text-green-400">{ts.length > 0 ? ts[ts.length - 1].overall?.toFixed(2) ?? '—' : '—'}</div>
          <div className="text-xs text-text-secondary mt-0.5">Latest Overall</div>
        </div>
        <div className="flex-1 p-3 rounded-lg bg-gray-800/50 border border-border text-center">
          <div className="text-2xl font-bold text-text-primary">{stratData.length}</div>
          <div className="text-xs text-text-secondary mt-0.5">Strategies Tracked</div>
        </div>
        <div className="flex-1 p-3 rounded-lg bg-gray-800/50 border border-border text-center">
          <div className="text-2xl font-bold text-text-primary">{providerData.length}</div>
          <div className="text-xs text-text-secondary mt-0.5">Providers</div>
        </div>
      </div>

      {/* Row 2: Quality bars */}
      <Card>
        <CardHeader><CardTitle>Average Quality Scores</CardTitle></CardHeader>
        <CardContent className="p-3">
          <div className="space-y-2 max-w-md">
            {barData.filter(d => d.label !== 'Overall').map(d => (
              <ScoreBar key={d.label} label={d.label} value={d.value} />
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-border">
            <ScoreBar label="OVERALL" value={avgs.overall || 0} />
          </div>
        </CardContent>
      </Card>

      {/* Row 2: Charts */}
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <CardHeader><CardTitle>Score by Strategy</CardTitle></CardHeader>
          <CardContent className="p-3">
            {stratData.length > 0 ? (
              <BarChart data={stratData} width={260} height={140} valueKey="value" labelKey="label" barColor="#22c55e" />
            ) : (
              <div className="text-text-secondary text-sm text-center py-8">No strategy data</div>
            )}
            <div className="flex flex-wrap gap-2 mt-2">
              {stratData.map(d => (
                <span key={d.label} className="text-xs text-text-secondary">
                  {d.label}: <span className="text-text-primary">{d.value.toFixed(2)}</span> ({d.count})
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Overall Trend</CardTitle></CardHeader>
          <CardContent className="p-3">
            {tsData.length > 1 ? (
              <Sparkline data={tsData} width={260} height={80} color="#22c55e" />
            ) : (
              <div className="text-text-secondary text-sm text-center py-8">Need 2+ days for trend</div>
            )}
            <div className="flex flex-wrap gap-2 mt-2">
              {tsData.slice(-3).map(d => (
                <span key={d.label} className="text-xs text-text-secondary">
                  {d.label}: {d.value.toFixed(2)}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: By provider */}
      {providerData.length > 1 && (
        <Card>
          <CardHeader><CardTitle>Score by Provider</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-text-secondary border-b border-border">
                    <th className="text-left py-2 px-3">Provider</th>
                    <th className="text-right py-2 px-3">Count</th>
                    {dims.filter(k => k !== 'overall').map(k => (
                      <th key={k} className="text-right py-2 px-3">{dimLabels[k] || k}</th>
                    ))}
                    <th className="text-right py-2 px-3">Overall</th>
                  </tr>
                </thead>
                <tbody>
                  {providerData.map(p => {
                    const provDetail = data.by_provider[p.label]?.averages || {};
                    return (
                      <tr key={p.label} className="border-b border-border/30 hover:bg-gray-800/30">
                        <td className="py-1.5 px-3 text-text-primary">{p.label}</td>
                        <td className="py-1.5 px-3 text-right text-text-secondary">{p.count}</td>
                        {dims.filter(k => k !== 'overall').map(k => (
                          <td key={k} className="py-1.5 px-3 text-right text-text-secondary">{provDetail[k]?.toFixed(2) ?? '—'}</td>
                        ))}
                        <td className="py-1.5 px-3 text-right font-medium text-text-primary">{provDetail.overall?.toFixed(2) ?? '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent evaluations */}
      {recent.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Recent Evaluations</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-text-secondary border-b border-border">
                    <th className="text-left py-2 px-3">Time</th>
                    <th className="text-left py-2 px-3">Strategy</th>
                    <th className="text-right py-2 px-3">Overall</th>
                    <th className="text-right py-2 px-3">Resp Len</th>
                    <th className="text-left py-2 px-3">Provider</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((r) => (
                    <tr key={r.id} className="border-b border-border/30 hover:bg-gray-800/30">
                      <td className="py-1.5 px-3 text-xs text-text-secondary">
                        {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
                      </td>
                      <td className="py-1.5 px-3 text-text-primary text-xs">{r.strategy}</td>
                      <td className="py-1.5 px-3 text-right font-medium">
                        <span className={r.evaluation?.overall >= 0.8 ? 'text-green-400' : r.evaluation?.overall >= 0.5 ? 'text-yellow-400' : 'text-red-400'}>
                          {r.evaluation?.overall?.toFixed(2) ?? '—'}
                        </span>
                      </td>
                      <td className="py-1.5 px-3 text-right text-text-secondary text-xs">{r.response_length ?? '—'}</td>
                      <td className="py-1.5 px-3 text-text-secondary text-xs">{r.provider}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
