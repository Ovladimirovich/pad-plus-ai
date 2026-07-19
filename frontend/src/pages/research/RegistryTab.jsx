import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import { apiFetch } from '../../services/api';

function PhaseCard({ phase, selected, onClick }) {
  const isBg = phase.background;
  return (
    <div
      onClick={() => onClick(phase)}
      className={`p-3 rounded-lg border cursor-pointer transition-all ${
        selected?.name === phase.name
          ? 'border-primary bg-primary/10'
          : 'border-border hover:border-primary/50 hover:bg-gray-800/50'
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-text-primary">{phase.name}</span>
        <div className="flex items-center gap-2">
          {phase.order != null && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-text-secondary">#{phase.order}</span>
          )}
          {isBg && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-purple-900/30 text-purple-400">bg</span>
          )}
          {!isBg && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">sync</span>
          )}
        </div>
      </div>
      {selected?.name === phase.name && phase.description && (
        <p className="text-xs text-text-secondary mt-2 leading-relaxed">{phase.description}</p>
      )}
    </div>
  );
}

export default function RegistryTab() {
  const [phases, setPhases] = useState([]);
  const [details, setDetails] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch('/api/v1/experiments/pipeline/registry');
        if (res.ok) {
          const data = await res.json();
          setPhases(data.phases || []);
          setDetails(data.details || []);
        }
      } catch (e) { console.error(e); }
      setLoading(false);
    })();
  }, []);

  const syncPhases = details.filter((d) => !d.background);
  const bgPhases = details.filter((d) => d.background);

  return (
    <div className="space-y-4 overflow-y-auto h-full">
      <h3 className="text-sm font-medium text-text-primary">
        Pipeline Registry — {details.length} phases (click for details)
      </h3>
      {loading ? (
        <div className="text-text-secondary text-sm">Loading...</div>
      ) : (
        <div className="space-y-4">
          <div>
            <h4 className="text-xs text-text-secondary font-medium mb-2 uppercase tracking-wider">
              Sync — {syncPhases.length} phases (выполняются последовательно)
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {syncPhases.map((p) => (
                <PhaseCard key={p.name} phase={p} selected={selected} onClick={setSelected} />
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-xs text-text-secondary font-medium mb-2 uppercase tracking-wider">
              Background — {bgPhases.length} phases (fire-and-forget после ответа)
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {bgPhases.map((p) => (
                <PhaseCard key={p.name} phase={p} selected={selected} onClick={setSelected} />
              ))}
            </div>
          </div>

          {selected && (
            <Card>
              <CardHeader><CardTitle>{selected.name}</CardTitle></CardHeader>
              <CardContent className="p-3 space-y-2 text-sm">
                <div className="flex gap-4 text-xs text-text-secondary">
                  <span>Class: <span className="text-text-primary font-mono">{selected.class_name}</span></span>
                  <span>Order: <span className="text-text-primary font-bold">#{selected.order}</span></span>
                  <span>Type: <span className={selected.background ? 'text-purple-400' : 'text-blue-400'}>
                    {selected.background ? 'background' : 'sync'}</span>
                  </span>
                </div>
                {selected.description && (
                  <p className="text-text-primary">{selected.description}</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
