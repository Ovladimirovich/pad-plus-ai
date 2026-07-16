import { Card, CardContent } from '../ui/Card';

const STAGES = [
  { id: 'safety', label: 'Safety', icon: '🛡️', color: 'blue' },
  { id: 'intent', label: 'Intent', icon: '🎯', color: 'purple' },
  { id: 'retrieve', label: 'Retrieve', icon: '🔍', color: 'cyan' },
  { id: 'persona', label: 'Persona', icon: '👤', color: 'pink' },
  { id: 'generate', label: 'Generate', icon: '⚡', color: 'amber' },
  { id: 'verify', label: 'Verify', icon: '✅', color: 'green' },
  { id: 'remember', label: 'Remember', icon: '💾', color: 'indigo' },
  { id: 'emit', label: 'Emit', icon: '📤', color: 'rose' },
];

const colorMap = {
  blue: 'from-blue-500 to-blue-600',
  purple: 'from-purple-500 to-purple-600',
  cyan: 'from-cyan-500 to-cyan-600',
  pink: 'from-pink-500 to-pink-600',
  amber: 'from-amber-500 to-amber-600',
  green: 'from-green-500 to-green-600',
  indigo: 'from-indigo-500 to-indigo-600',
  rose: 'from-rose-500 to-rose-600',
};

const glowMap = {
  blue: 'shadow-blue-500/30',
  purple: 'shadow-purple-500/30',
  cyan: 'shadow-cyan-500/30',
  pink: 'shadow-pink-500/30',
  amber: 'shadow-amber-500/30',
  green: 'shadow-green-500/30',
  indigo: 'shadow-indigo-500/30',
  rose: 'shadow-rose-500/30',
};

export function XRayPipeline({ activeStage, completedStages, stageData, status, error }) {
  return (
    <Card className="w-full bg-gray-900/50 border-gray-700">
      <CardContent className="p-4">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>🔬</span> Pipeline Status
          {status === 'processing' && (
            <span className="ml-2 inline-flex items-center gap-1 text-xs text-blue-400">
              <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
              Processing
            </span>
          )}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          {STAGES.map((stage) => {
            const isActive = activeStage === stage.id;
            const isCompleted = completedStages.includes(stage.id);
            const data = stageData[stage.id];

            return (
              <div key={stage.id} className="flex-1 min-w-[120px]">
                <div
                  className={`
                    p-3 rounded-lg border text-center transition-all duration-300
                    ${isActive
                      ? `bg-gradient-to-br ${colorMap[stage.color]} text-white shadow-lg ${glowMap[stage.color]} border-transparent scale-105`
                      : isCompleted
                        ? 'bg-gray-800 border-green-700/50 text-green-400'
                        : 'bg-gray-800/50 border-gray-700 text-gray-500'
                    }
                  `}
                >
                  <div className="text-xl mb-1">{stage.icon}</div>
                  <div className="text-xs font-medium">{stage.label}</div>
                  {isCompleted && <div className="text-xs text-green-400 mt-1">✓</div>}
                  {data?.duration_ms != null && (
                    <div className="text-xs text-gray-400 mt-1">{data.duration_ms}ms</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default XRayPipeline;
