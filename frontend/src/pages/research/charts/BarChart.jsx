export default function BarChart({
  data = [],
  width = 300,
  height = 100,
  barColor = '#3b82f6',
  maxValue,
  showLabels = true,
  labelKey = 'label',
  valueKey = 'value',
}) {
  if (!data.length) return null;
  const max = maxValue ?? Math.max(...data.map((d) => d[valueKey]), 1);
  const pad = { top: 4, right: 4, bottom: 16, left: 4 };
  const w = width - pad.left - pad.right;
  const h = height - pad.top - pad.bottom;
  const barW = Math.max(4, w / data.length - 2);

  return (
    <svg width={width} height={height} className="overflow-visible">
      {data.map((d, i) => {
        const v = d[valueKey];
        const barH = (v / max) * h;
        const x = pad.left + (w / data.length) * i + 1;
        const y = pad.top + h - barH;
        return (
          <g key={i}>
            <rect x={x} y={y} width={barW} height={barH} fill={d.color || barColor} rx="2" />
            {showLabels && i % Math.max(1, Math.floor(data.length / 6)) === 0 && (
              <text x={x + barW / 2} y={height - 2} textAnchor="end"
                className="fill-text-secondary" fontSize="9"
                transform={`rotate(-45 ${x + barW / 2} ${height - 2})`}>
                {d[labelKey]}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
