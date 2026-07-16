import { Card, CardContent } from '../ui/Card';

export function TraceHistory({ wsTraces = [] }) {
  const hasTraces = wsTraces && wsTraces.length > 0;

  return (
    <Card className="w-full bg-gray-900/50 border-gray-700">
      <CardContent className="p-4">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>📜</span> Trace History
        </h2>

        {!hasTraces ? (
          <div className="text-sm text-gray-500 text-center py-8">
            No traces yet. Start a conversation to see pipeline traces.
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {wsTraces.map((trace, i) => (
              <div
                key={trace.trace_id || i}
                className="p-2 bg-gray-800/50 rounded text-xs text-gray-400 flex justify-between"
              >
                <span className="font-mono truncate">{trace.name || trace.trace_id || `trace-${i}`}</span>
                <span className="text-gray-500 shrink-0 ml-2">
                  {trace.duration_ms != null ? `${Math.round(trace.duration_ms)}ms` : ''}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default TraceHistory;
