import { useState, useEffect } from 'react';
import { apiFetch } from '../../services/api';

export default function ResearchHeader() {
  const [health, setHealth] = useState({ overall_score: 0, status: 'unknown' });
  const [stats, setStats] = useState({ active_sessions: 0, total_traces: 0 });
  const [evalAvg, setEvalAvg] = useState(null);
  const [lastRun, setLastRun] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [hRes, sRes, eRes, rRes] = await Promise.allSettled([
          apiFetch('/api/v1/mind-state'),
          apiFetch('/api/v1/xray/stats'),
          apiFetch('/api/v1/experiments/evals?limit=5'),
          apiFetch('/api/v1/experiments/runs'),
        ]);
        if (hRes.status === 'fulfilled' && hRes.value.ok) {
          const d = await hRes.value.json();
          setHealth({ overall_score: d.health?.overall_score || d.overall_score || 0, status: d.health?.status || d.status || 'unknown' });
        }
        if (sRes.status === 'fulfilled' && sRes.value.ok) {
          const d = await sRes.value.json();
          setStats({ active_sessions: d.active_sessions || d.active || 0, total_traces: d.total_traces || d.total || 0 });
        }
        if (eRes.status === 'fulfilled' && eRes.value.ok) {
          const d = await eRes.value.json();
          if (d.timeseries?.length) setEvalAvg(d.timeseries[d.timeseries.length - 1]?.overall || d.averages?.overall || null);
        }
        if (rRes.status === 'fulfilled' && rRes.value.ok) {
          const d = await rRes.value.json();
          const runs = d.runs || [];
          if (runs.length > 0) setLastRun(runs[runs.length - 1]);
        }
      } catch (_) {}
    };
    fetch();
    const id = setInterval(fetch, 30000);
    return () => clearInterval(id);
  }, []);

  const statusColor = { excellent: 'text-green-400', good: 'text-green-400', fair: 'text-yellow-400', poor: 'text-orange-400', critical: 'text-red-400' };

  const cards = [
    {
      label: 'System Health',
      value: health.overall_score?.toFixed(2) ?? '—',
      meta: health.status,
      color: statusColor[health.status] || 'text-text-secondary',
    },
    {
      label: 'Active Traces',
      value: stats.active_sessions,
      meta: `${stats.total_traces} total`,
      color: 'text-blue-400',
    },
    {
      label: 'Eval Avg',
      value: evalAvg !== null ? evalAvg.toFixed(2) : '—',
      meta: 'overall',
      color: evalAvg !== null && evalAvg >= 0.7 ? 'text-green-400' : 'text-yellow-400',
    },
    {
      label: 'Last Run',
      value: lastRun?.display_name || lastRun?.name || '—',
      meta: lastRun ? lastRun.name : 'no runs yet',
      color: 'text-purple-400',
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-3 mb-3">
      {cards.map((c) => (
        <div key={c.label} className="p-3 rounded-lg bg-gray-800/40 border border-border">
          <div className="text-xs text-text-secondary mb-1">{c.label}</div>
          <div className={`text-lg font-bold ${c.color}`}>{c.value}</div>
          <div className="text-xs text-text-secondary mt-0.5">{c.meta}</div>
        </div>
      ))}
    </div>
  );
}
