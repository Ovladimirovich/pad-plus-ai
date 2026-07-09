import { memo } from 'react';
import { Handle, Position } from 'reactflow';

const TYPE_COLORS = {
  concept: { bg: '#1e3a5f', border: '#3b82f6', text: '#93c5fd' },
  fact: { bg: '#14532d', border: '#22c55e', text: '#86efac' },
  skill: { bg: '#3b0764', border: '#a855f7', text: '#c084fc' },
  question: { bg: '#422006', border: '#eab308', text: '#fde047' },
  entity: { bg: '#083344', border: '#06b6d4', text: '#67e8f9' },
};
const DEFAULT = { bg: '#1f2937', border: '#6b7280', text: '#d1d5db' };

function ConceptNode({ data }) {
  const colors = TYPE_COLORS[data.type?.toLowerCase()] || DEFAULT;
  return (
    <div
      className="px-4 py-2 rounded-xl border-2 shadow-lg backdrop-blur-sm min-w-[120px] cursor-pointer transition-transform hover:scale-105"
      style={{
        backgroundColor: colors.bg,
        borderColor: colors.border,
      }}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-500" />
      <div className="flex items-center gap-2">
        <span
          className="w-2.5 h-2.5 rounded-full shrink-0"
          style={{ backgroundColor: colors.border }}
        />
        <div className="text-sm font-medium truncate max-w-[150px]" style={{ color: colors.text }}>
          {data.label}
        </div>
      </div>
      <div className="text-[10px] mt-0.5 opacity-50" style={{ color: colors.text }}>
        {data.type || 'concept'}
        {data.connectionCount > 0 && ` · ${data.connectionCount} св.`}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-500" />
    </div>
  );
}

export default memo(ConceptNode);
