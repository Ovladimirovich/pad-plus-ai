import { Card, CardContent } from '../ui/Card';

export function XRayMeta({ connected = false, wsStats = {} }) {
  return (
    <Card className="w-full bg-gray-900/50 border-gray-700">
      <CardContent className="p-4">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>ℹ️</span> Connection
        </h2>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">WebSocket</span>
            <span className={`flex items-center gap-1.5 ${connected ? 'text-green-400' : 'text-red-400'}`}>
              <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {wsStats.messagesSent != null && (
            <div className="flex justify-between">
              <span className="text-gray-400">Messages Sent</span>
              <span className="text-white">{wsStats.messagesSent}</span>
            </div>
          )}
          {wsStats.errors != null && wsStats.errors > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-400">Errors</span>
              <span className="text-red-400">{wsStats.errors}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default XRayMeta;
