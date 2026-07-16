import { useEffect, useState } from 'react';
import { Card, CardContent } from '../ui/Card';
import { apiFetch } from '../../services/api';

export function TraceStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch('/api/v1/xray/stats')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setStats(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const items = stats ? [
    { label: 'Total Traces', value: stats.total_traces ?? '—' },
    { label: 'Active', value: stats.active_traces ?? '—' },
    { label: 'Completed', value: stats.completed_traces ?? '—' },
    { label: 'Avg Duration', value: stats.avg_duration_ms != null ? `${Math.round(stats.avg_duration_ms)}ms` : '—' },
    { label: 'Error Rate', value: stats.error_rate != null ? `${(stats.error_rate * 100).toFixed(1)}%` : '—' },
    { label: 'Orphan Spans', value: stats.orphan_spans ?? '—' },
  ] : [];

  return (
    <Card className="w-full bg-gray-900/50 border-gray-700">
      <CardContent className="p-4">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>📊</span> X-Ray Stats
        </h2>

        {loading ? (
          <div className="text-sm text-gray-500 text-center py-4">Loading...</div>
        ) : items.length === 0 ? (
          <div className="text-sm text-gray-500 text-center py-4">No stats available</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {items.map((item) => (
              <div key={item.label} className="p-3 bg-gray-800/50 rounded-lg">
                <div className="text-xs text-gray-400 mb-1">{item.label}</div>
                <div className="text-sm font-medium text-white">{item.value}</div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TraceStats;
