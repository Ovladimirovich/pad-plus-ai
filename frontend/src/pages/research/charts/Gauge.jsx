export default function Gauge({ value = 0, label = '', size = 100, thresholds = [0.4, 0.7] }) {
  const r = size * 0.4;
  const cx = size / 2;
  const cy = size / 2 + size * 0.05;
  const stroke = size * 0.08;
  const arcLen = Math.PI;
  const startAngle = Math.PI;
  const clamped = Math.max(0, Math.min(1, value));
  const angle = startAngle + arcLen * clamped;

  let color = thresholds.length >= 2
    ? clamped < thresholds[0] ? '#ef4444'
      : clamped < thresholds[1] ? '#f59e0b'
      : '#22c55e'
    : '#22c55e';

  const bgX1 = cx - r * Math.cos(startAngle);
  const bgY1 = cy - r * Math.sin(startAngle);
  const bgX2 = cx + r;
  const bgY2 = cy;
  const fgX = cx - r * Math.cos(angle);
  const fgY = cy - r * Math.sin(angle);
  const largeArc = angle - startAngle > Math.PI ? 1 : 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="inline-block">
      <path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 1 0 ${bgX2} ${bgY2}`}
        fill="none" stroke="#1f2937" strokeWidth={stroke} strokeLinecap="round" />
      <path d={`M ${bgX1} ${bgY1} A ${r} ${r} 0 ${largeArc} 0 ${fgX} ${fgY}`}
        fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
        style={{ transition: 'd 0.5s ease' }} />
      <text x={cx} y={cy - size * 0.02} textAnchor="middle"
        className="fill-text-primary" fontSize={size * 0.16} fontWeight="bold">
        {typeof value === 'number' ? `${(value * 100).toFixed(0)}%` : 'N/A'}
      </text>
      {label && (
        <text x={cx} y={cy + size * 0.14} textAnchor="middle"
          className="fill-text-secondary" fontSize={size * 0.07}>
          {label}
        </text>
      )}
    </svg>
  );
}
