/**
 * Donut.jsx — Anel de distribuição de risco com rótulo central.
 * Usado em "Distribuição do Risco" / "Panorama de Risco".
 */
export default function Donut({ data = [], total, centerLabel = 'municípios', size = 150, thickness = 16 }) {
  const sum = data.reduce((a, d) => a + (d.value || 0), 0) || 1;
  const R = 52;
  const C = 60;
  const CIRC = 2 * Math.PI * R;
  let offset = 0;

  return (
    <svg viewBox="0 0 120 120" width={size} height={size} style={{ display: 'block' }}>
      <circle cx={C} cy={C} r={R} fill="none" stroke="rgba(148,163,184,.1)" strokeWidth={thickness} />
      {data.map((d, i) => {
        const dash = (d.value / sum) * CIRC;
        const seg = (
          <circle
            key={i}
            cx={C}
            cy={C}
            r={R}
            fill="none"
            stroke={d.color}
            strokeWidth={thickness}
            strokeDasharray={`${Math.max(dash - 1.5, 0)} ${CIRC - Math.max(dash - 1.5, 0)}`}
            strokeDashoffset={-offset}
            transform={`rotate(-90 ${C} ${C})`}
            strokeLinecap="butt"
          />
        );
        offset += dash;
        return seg;
      })}
      <text x={C} y={C - 1} textAnchor="middle" fontSize="23" fontWeight="800" fill="#e8eef7"
        style={{ fontFamily: 'Fira Sans, sans-serif' }}>
        {total ?? sum}
      </text>
      <text x={C} y={C + 15} textAnchor="middle" fontSize="9" fill="#647689"
        style={{ fontFamily: 'Fira Sans, sans-serif' }}>
        {centerLabel}
      </text>
    </svg>
  );
}
