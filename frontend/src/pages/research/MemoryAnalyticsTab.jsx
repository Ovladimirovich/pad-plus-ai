import { useState, useEffect } from 'react';

export default function MemoryAnalyticsTab() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/v1/memory/shadow/stats');
      if (!res.ok) throw new Error('Failed to fetch shadow memory stats');
      const data = await res.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000); // Poling каждые 5с
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return <div className="p-6 text-text-secondary">Загрузка аналитики Memory Decision Layer...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-400">Ошибка загрузки: {error}</div>;
  }

  const verdicts = stats?.verdicts_aggregate || { keep: 0, outdated: 0, discard: 0, conflict: 0, uncertain: 0 };
  const totalVerdicts = Object.values(verdicts).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="h-full overflow-y-auto space-y-6 pr-2">
      {/* Шапка с метриками */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="text-text-secondary text-sm">Всего запросов (Shadow)</div>
          <div className="text-2xl font-bold text-text-primary mt-1">{stats?.total_queries || 0}</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="text-text-secondary text-sm">Abstention Rate (Сомнения)</div>
          <div className="text-2xl font-bold text-yellow-400 mt-1">{stats?.abstention_rate || 0}%</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="text-text-secondary text-sm">Средняя латентность</div>
          <div className="text-2xl font-bold text-green-400 mt-1">{stats?.avg_latency_ms || 0} ms</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="text-text-secondary text-sm">Статус слоя</div>
          <div className="text-lg font-semibold text-primary mt-1">🟢 Shadow Mode Active</div>
        </div>
      </div>

      {/* Распределение вердиктов */}
      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">⚖️ Распределение вердиктов Memory Decision Layer</h3>
        
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
          <div className="bg-gray-800/50 p-3 rounded-lg border border-green-500/30">
            <div className="text-xs text-green-400 uppercase font-bold">KEEP (Допущено)</div>
            <div className="text-xl font-bold text-text-primary mt-1">{verdicts.keep}</div>
            <div className="text-xs text-text-secondary mt-1">{((verdicts.keep / totalVerdicts) * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-800/50 p-3 rounded-lg border border-orange-500/30">
            <div className="text-xs text-orange-400 uppercase font-bold">OUTDATED (Устарело)</div>
            <div className="text-xl font-bold text-text-primary mt-1">{verdicts.outdated}</div>
            <div className="text-xs text-text-secondary mt-1">{((verdicts.outdated / totalVerdicts) * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-800/50 p-3 rounded-lg border border-red-500/30">
            <div className="text-xs text-red-400 uppercase font-bold">DISCARD (Мусор)</div>
            <div className="text-xl font-bold text-text-primary mt-1">{verdicts.discard}</div>
            <div className="text-xs text-text-secondary mt-1">{((verdicts.discard / totalVerdicts) * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-800/50 p-3 rounded-lg border border-purple-500/30">
            <div className="text-xs text-purple-400 uppercase font-bold">CONFLICT (Конфликт)</div>
            <div className="text-xl font-bold text-text-primary mt-1">{verdicts.conflict}</div>
            <div className="text-xs text-text-secondary mt-1">{((verdicts.conflict / totalVerdicts) * 100).toFixed(1)}%</div>
          </div>
          <div className="bg-gray-800/50 p-3 rounded-lg border border-yellow-500/30">
            <div className="text-xs text-yellow-400 uppercase font-bold">UNCERTAIN (Отказ)</div>
            <div className="text-xl font-bold text-text-primary mt-1">{verdicts.uncertain}</div>
            <div className="text-xs text-text-secondary mt-1">{((verdicts.uncertain / totalVerdicts) * 100).toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Последние события */}
      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">📋 Последние запросы в Shadow Mode</h3>
        {stats?.recent_events?.length === 0 ? (
          <p className="text-text-secondary text-sm">Пока нет записей в буфере shadow mode.</p>
        ) : (
          <div className="space-y-3">
            {stats?.recent_events?.slice().reverse().map((ev, idx) => (
              <div key={idx} className="bg-background border border-border p-3 rounded-lg flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-text-primary">"{ev.query}"</div>
                  <div className="text-xs text-text-secondary mt-1 flex gap-2">
                    <span className="text-green-400">Keep: {ev.stats.keep}</span>
                    <span className="text-orange-400">Outdated: {ev.stats.outdated}</span>
                    <span className="text-red-400">Discard: {ev.stats.discard}</span>
                    <span className="text-yellow-400">Uncertain: {ev.stats.uncertain}</span>
                  </div>
                </div>
                <div className="text-xs text-text-secondary bg-surface px-2 py-1 rounded">
                  {ev.latency_ms.toFixed(2)} ms
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
