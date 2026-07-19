import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import BarChart from './charts/BarChart';
import Sparkline from './charts/Sparkline';
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

export default function MetricsTab() {
  const [pipeline, setPipeline] = useState(null);
  const [system, setSystem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { exportJSON, exportCSV } = useExport();

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const [pipeRes, sysRes] = await Promise.all([
        apiFetch('/api/v1/metrics/pipeline'),
        apiFetch('/api/v1/metrics/system'),
      ]);
      if (pipeRes.ok) setPipeline(await pipeRes.json());
      if (sysRes.ok) setSystem(await sysRes.json());
    } catch (e) { console.error('Metrics load failed:', e); }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const id = setInterval(() => load(true), 15000); return () => clearInterval(id); }, [load]);

  if (loading) {
    return <div className="text-text-secondary text-sm py-8 text-center">Loading metrics...</div>;
  }

  const counters = pipeline?.counters || {};
  const gauges = pipeline?.gauges || {};
  const hist = pipeline?.histograms?.pipeline_duration_ms || {};
  const timeSeries = pipeline?.time_series?.pipeline_duration_ms || [];
  const totalRequests = counters.pipeline_requests_total || 0;
  const successCount = counters.pipeline_success_total || 0;
  const errorCount = counters.pipeline_errors_total || 0;

  const barData = [
    { label: 'avg', value: Math.round(hist.avg || 0) },
    { label: 'p50', value: Math.round(hist.p50 || 0) },
    { label: 'p95', value: Math.round(hist.p95 || 0) },
    { label: 'p99', value: Math.round(hist.p99 || 0) },
  ].filter(d => d.value > 0);

  const tsValues = timeSeries.map((t) => ({
    label: t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : '',
    value: t.value,
  }));

  const sys = system || {};

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">Pipeline & System Metrics</h3>
        <div className="flex items-center gap-3">
          <span className={`text-xs transition-opacity ${refreshing ? 'opacity-100 text-primary' : 'opacity-0'}`}>
            ⟳ refreshing
          </span>
          <span className="text-xs text-text-secondary">auto 15s</span>
          <button onClick={() => exportJSON(pipeline, 'pipeline-metrics.json')}
            className="text-xs text-primary hover:underline">Export JSON</button>
        </div>
      </div>

      {/* Row 1: Pipeline counters */}
      <div className="flex gap-3">
        <MetricCard label="Total Requests" value={totalRequests} color="text-blue-400" />
        <MetricCard label="Successful" value={successCount} color="text-green-400"
          sub={totalRequests > 0 ? `${((successCount / totalRequests) * 100).toFixed(0)}%` : ''} />
        <MetricCard label="Errors" value={errorCount} color={errorCount > 0 ? 'text-red-400' : 'text-text-secondary'} />
        <MetricCard label="Uptime" value={pipeline?.uptime_seconds ? `${Math.floor(pipeline.uptime_seconds / 3600)}h` : '—'} />
      </div>

      {/* Row 2: Latency histogram + time series */}
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <CardHeader><CardTitle>Latency (ms)</CardTitle></CardHeader>
          <CardContent className="p-3">
            {barData.length > 0 ? (
              <BarChart data={barData} width={280} height={140} barColor="#3b82f6" showLabels={true} />
            ) : (
              <div className="text-text-secondary text-sm text-center py-8">No histogram data</div>
            )}
            <div className="flex justify-between mt-2 text-xs text-text-secondary px-2">
              {barData.map(d => (
                <span key={d.label}>{d.label}: {d.value}ms</span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Duration (last 1h)</CardTitle></CardHeader>
          <CardContent className="p-3">
            {tsValues.length > 1 ? (
              <Sparkline data={tsValues} width={280} height={80} color="#3b82f6" />
            ) : (
              <div className="text-text-secondary text-sm text-center py-8">No time series data</div>
            )}
            {tsValues.length > 0 && (
              <div className="text-xs text-text-secondary text-center mt-1">
                Latest: {tsValues[tsValues.length - 1].value?.toFixed(0)}ms
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row 3: System resources */}
      <Card>
        <CardHeader><CardTitle>System Resources</CardTitle></CardHeader>
        <CardContent className="p-3">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-text-secondary mb-1">CPU Usage</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-gray-700 overflow-hidden">
                  <div className="h-full rounded-full bg-blue-500 transition-all"
                    style={{ width: `${Math.min(sys.cpu_usage ?? 0, 100)}%` }} />
                </div>
                <span className="text-sm font-medium text-text-primary w-10 text-right">{(sys.cpu_usage ?? 0).toFixed(0)}%</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-text-secondary mb-1">Memory</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 rounded-full bg-gray-700 overflow-hidden">
                  <div className="h-full rounded-full bg-purple-500 transition-all"
                    style={{ width: `${Math.min(sys.memory_usage ?? 0, 100)}%` }} />
                </div>
                <span className="text-sm font-medium text-text-primary w-10 text-right">{(sys.memory_usage ?? 0).toFixed(0)}%</span>
              </div>
            </div>
            <div>
              <div className="text-xs text-text-secondary mb-1">Connections</div>
              <div className="text-sm font-medium text-text-primary">{sys.active_connections ?? 0}
                <span className="text-text-secondary text-xs ml-1">/ {sys.max_connections ?? '—'}</span>
              </div>
              <div className="text-xs text-text-secondary mt-0.5">{sys.active_sessions ?? 0} active sessions</div>
            </div>
            <div>
              <div className="text-xs text-text-secondary mb-1">Today</div>
              <div className="text-sm font-medium text-text-primary">${sys.cost_today ?? '0.00'}</div>
              <div className="text-xs text-text-secondary mt-0.5">Cost</div>
              <div className="text-xs text-text-secondary">{sys.cache_hit_rate ?? 0}% cache hit</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* All counters */}
      {Object.keys(counters).length > 0 && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>All Counters</CardTitle>
            <button onClick={() => exportCSV(Object.entries(counters).map(([k, v]) => ({ metric: k, value: v })), 'counters.csv')}
              className="text-xs text-primary hover:underline">Export CSV</button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-text-secondary border-b border-border">
                    <th className="text-left py-2 px-3">Metric</th>
                    <th className="text-right py-2 px-3">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(counters).map(([k, v]) => (
                    <tr key={k} className="border-b border-border/30 hover:bg-gray-800/30">
                      <td className="py-1.5 px-3 text-text-primary font-mono text-xs">{k}</td>
                      <td className="py-1.5 px-3 text-right text-text-secondary">{v}</td>
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
