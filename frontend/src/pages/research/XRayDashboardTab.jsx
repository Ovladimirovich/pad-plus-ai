import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import Gauge from './charts/Gauge';
import BarChart from './charts/BarChart';
import Sparkline from './charts/Sparkline';
import { apiFetch } from '../../services/api';
import { useExport } from './useExport';

function HealthBadge({ status }) {
  const colors = {
    healthy: 'bg-green-900/30 text-green-400 border-green-700/50',
    degraded: 'bg-yellow-900/30 text-yellow-400 border-yellow-700/50',
    critical: 'bg-red-900/30 text-red-400 border-red-700/50',
    warning: 'bg-yellow-900/30 text-yellow-400 border-yellow-700/50',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${colors[status] || 'bg-gray-800 text-text-secondary border-border'}`}>
      {status}
    </span>
  );
}

export default function XRayDashboardTab() {
  const [brain, setBrain] = useState(null);
  const [stats, setStats] = useState(null);
  const [active, setActive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { exportJSON } = useExport();

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const [brainRes, statsRes, activeRes] = await Promise.all([
        apiFetch('/api/v1/xray/brain/status'),
        apiFetch('/api/v1/xray/stats'),
        apiFetch('/api/v1/xray/active'),
      ]);
      if (brainRes.ok) setBrain(await brainRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
      if (activeRes.ok) setActive(await activeRes.json());
    } catch (e) { console.error('X-Ray load failed:', e); }
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const id = setInterval(() => load(true), 15000); return () => clearInterval(id); }, [load]);

  if (loading) {
    return <div className="text-text-secondary text-sm py-8 text-center">Loading X-Ray data...</div>;
  }

  const sysState = brain?.system_state || {};
  const meta = brain?.meta_learner || {};
  const reflection = brain?.reflection || {};
  const tc = stats?.trace_collector || {};
  const stageStats = tc.stage_stats || {};
  const strategies = meta.strategies || {};

  const stratList = Object.entries(strategies).map(([name, s]) => ({
    name,
    count: s.count || 0,
    successRate: s.success_rate != null ? (s.success_rate * 100).toFixed(0) : '—',
    avgConfidence: s.avg_confidence != null ? s.avg_confidence.toFixed(2) : '—',
    lastUsed: s.last_used ? new Date(s.last_used * 1000).toLocaleString() : '—',
  }));

  const stageList = Object.entries(stageStats).map(([name, s]) => ({
    name,
    count: s.count || 0,
    avgMs: s.avg_duration_ms != null ? s.avg_duration_ms.toFixed(0) : '',
    errors: s.errors || 0,
    errorRate: s.count ? ((s.errors / s.count) * 100).toFixed(1) : '0',
  }));

  const activeSessions = active?.active_sessions ?? active?.sessions?.length ?? 0;

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">X-Ray System Dashboard</h3>
        <div className="flex items-center gap-3">
          <span className={`text-xs transition-opacity ${refreshing ? 'opacity-100 text-primary' : 'opacity-0'}`}>
            ⟳ refreshing
          </span>
          <span className="text-xs text-text-secondary">auto 15s</span>
          <button onClick={() => exportJSON({ brain, stats, active }, 'xray-dashboard.json')}
            className="text-xs text-primary hover:underline">Export JSON</button>
        </div>
      </div>

      {/* Row 1: System Health */}
      <div className="grid grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-3 flex flex-col items-center">
            <Gauge value={sysState.load != null ? 1 - Math.min(sysState.load, 1) : 1} label="Free" size={90} />
            <div className="mt-1"><HealthBadge status={sysState.health_status || 'unknown'} /></div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 flex flex-col items-center">
            <Gauge value={sysState.confidence ?? 1} label="Confidence" size={90} thresholds={[0.5, 0.75]} />
            <div className="mt-1 text-xs text-text-secondary">
              {sysState.success_rate != null ? `${(sysState.success_rate * 100).toFixed(0)}% success` : '—'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 flex flex-col items-center justify-center">
            <div className="text-3xl font-bold text-text-primary">{tc.total_sessions ?? 0}</div>
            <div className="text-xs text-text-secondary">Total Sessions</div>
            <div className="text-xs text-text-secondary mt-1">
              {tc.completed_sessions ?? 0} completed
              {activeSessions > 0 && ` · ${activeSessions} active`}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 flex flex-col items-center justify-center">
            <div className="text-3xl font-bold text-text-primary">{meta.total_decisions ?? 0}</div>
            <div className="text-xs text-text-secondary">Meta Decisions</div>
            <div className="text-xs text-text-secondary mt-1">
              {meta.overall_success_rate != null ? `${(meta.overall_success_rate * 100).toFixed(0)}% success` : '—'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Meta-Learner Strategies */}
      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Strategies</CardTitle>
          {meta.best_strategy && (
            <div className="text-xs text-text-secondary">
              Best: <span className="text-green-400">{meta.best_strategy}</span>
              {meta.worst_strategy && <><span className="mx-1">·</span>Worst: <span className="text-red-400">{meta.worst_strategy}</span></>}
            </div>
          )}
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-text-secondary border-b border-border">
                  <th className="text-left py-2 px-3">Strategy</th>
                  <th className="text-right py-2 px-3">Count</th>
                  <th className="text-right py-2 px-3">Success Rate</th>
                  <th className="text-right py-2 px-3">Avg Confidence</th>
                  <th className="text-right py-2 px-3">Last Used</th>
                </tr>
              </thead>
              <tbody>
                {stratList.map((s) => (
                  <tr key={s.name} className="border-b border-border/30 hover:bg-gray-800/30">
                    <td className="py-2 px-3 text-text-primary font-medium">{s.name}</td>
                    <td className="py-2 px-3 text-right text-text-secondary">{s.count}</td>
                    <td className="py-2 px-3 text-right">
                      <span className={s.successRate >= 80 ? 'text-green-400' : s.successRate >= 50 ? 'text-yellow-400' : 'text-red-400'}>
                        {s.successRate}%
                      </span>
                    </td>
                    <td className="py-2 px-3 text-right text-text-secondary">{s.avgConfidence}</td>
                    <td className="py-2 px-3 text-right text-text-secondary text-xs">{s.lastUsed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Row 3: Stage Performance + Chart */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="col-span-2">
          <CardHeader><CardTitle>Stage Performance</CardTitle></CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-text-secondary border-b border-border">
                    <th className="text-left py-2 px-3">Stage</th>
                    <th className="text-right py-2 px-3">Count</th>
                    <th className="text-right py-2 px-3">Avg ms</th>
                    <th className="text-right py-2 px-3">Errors</th>
                    <th className="text-right py-2 px-3">Error Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {stageList.map((s) => (
                    <tr key={s.name} className="border-b border-border/30 hover:bg-gray-800/30">
                      <td className="py-1.5 px-3 text-text-primary">{s.name}</td>
                      <td className="py-1.5 px-3 text-right text-text-secondary">{s.count}</td>
                      <td className="py-1.5 px-3 text-right text-text-secondary">{s.avgMs}ms</td>
                      <td className="py-1.5 px-3 text-right text-text-secondary">{s.errors}</td>
                      <td className="py-1.5 px-3 text-right">
                        <span className={parseFloat(s.errorRate) > 10 ? 'text-red-400' : 'text-text-secondary'}>
                          {s.errorRate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Duration by Stage</CardTitle></CardHeader>
          <CardContent className="p-3">
            <BarChart
              data={stageList.filter(s => s.avgMs).map(s => ({ label: s.name, value: parseFloat(s.avgMs) }))}
              width={240} height={160} barColor="#3b82f6"
            />
          </CardContent>
        </Card>
      </div>

      {/* Row 4: Reflection + Cognitive */}
      <div className="grid grid-cols-2 gap-3">
        <Card>
          <CardHeader><CardTitle>Reflection Loop</CardTitle></CardHeader>
          <CardContent className="p-3">
            <div className="flex gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">{reflection.reflection_count ?? 0}</div>
                <div className="text-xs text-text-secondary">Reflections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">{reflection.adjustment_count ?? 0}</div>
                <div className="text-xs text-text-secondary">Adjustments</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">
                  {reflection.adjustment_rate != null ? `${(reflection.adjustment_rate * 100).toFixed(0)}%` : '—'}
                </div>
                <div className="text-xs text-text-secondary">Adj Rate</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>History & Broadcasting</CardTitle></CardHeader>
          <CardContent className="p-3">
            <div className="flex gap-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">{stats?.history_recorder?.total_traces ?? 0}</div>
                <div className="text-xs text-text-secondary">Recorded Traces</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">{stats?.history_recorder?.total_errors ?? 0}</div>
                <div className="text-xs text-text-secondary">Errors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-text-primary">{stats?.broadcaster?.total_messages_sent ?? 0}</div>
                <div className="text-xs text-text-secondary">Broadcasts</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Patterns */}
      {meta.patterns?.recommendations?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Patterns & Recommendations</CardTitle></CardHeader>
          <CardContent className="p-3">
            <div className="space-y-1">
              {meta.patterns.recommendations.map((r, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="text-yellow-400">💡</span>
                  <span className="text-text-primary">{r}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
