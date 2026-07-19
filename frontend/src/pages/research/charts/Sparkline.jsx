export default function Sparkline({ data = [], width = 200, height = 40, color = '#22c55e' }) {
  if (!data.length) return null;
  const values = data.map(d => (typeof d === 'number' ? d : d.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const stepX = w / (values.length - 1 || 1);

  const points = values.map((v, i) => {
    const x = pad + i * stepX;
    const y = pad + h - ((v - min) / range) * h;
    return `${x},${y}`;
  });

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points.join(' ')}
      />
      {values.map((v, i) => {
        const x = pad + i * stepX;
        const y = pad + h - ((v - min) / range) * h;
        return (
          <circle key={i} cx={x} cy={y} r="1.5" fill={color} />
        );
      })}
    </svg>
  );
}
