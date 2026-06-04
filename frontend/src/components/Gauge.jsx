/**
 * Gauge.jsx — Medidor semicircular de risco (0–100) com arco em gradiente e brilho.
 * Usado nos cards "RISCO GLOBAL" e no painel de território do Centro de Operações.
 */
import { scoreColor } from '../data/geoLoader.js';

export default function Gauge({
  score = 0,
  size = 150,
  suffix = '/100',
  showValue = true,
  thickness = 9,
}) {
  const v = Math.max(0, Math.min(100, Number(score) || 0));
  const color = scoreColor(v);
  const R = 50;
  const LEN = Math.PI * R;               // comprimento do semicírculo
  const dash = (v / 100) * LEN;
  const uid = `gz${Math.round(v * 1000)}${Math.round(size)}`;

  return (
    <svg viewBox="0 0 120 70" width={size} height={size * 0.6} style={{ display: 'block', overflow: 'visible' }}>
      <defs>
        <linearGradient id={`grad-${uid}`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stopColor="#22c55e" />
          <stop offset="42%"  stopColor="#facc15" />
          <stop offset="72%"  stopColor="#f97316" />
          <stop offset="100%" stopColor="#f43f5e" />
        </linearGradient>
        <filter id={`glow-${uid}`} x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="2.4" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* trilho */}
      <path d="M10,60 A50,50 0 0,1 110,60" fill="none"
        stroke="rgba(148,163,184,.16)" strokeWidth={thickness} strokeLinecap="round" />
      {/* valor (preenche com animação ao montar) */}
      <path className="gauge-arc" d="M10,60 A50,50 0 0,1 110,60" fill="none"
        stroke={`url(#grad-${uid})`} strokeWidth={thickness} strokeLinecap="round"
        style={{ '--dash': dash }}
        strokeDasharray={`${dash} ${LEN}`} filter={`url(#glow-${uid})`} />

      {showValue && (
        <>
          <text x="60" y="48" textAnchor="middle" fontSize="23" fontWeight="800"
            fill={color} style={{ fontFamily: 'Fira Sans, sans-serif' }}>
            {v.toFixed(1).replace('.', ',')}
          </text>
          <text x="60" y="60" textAnchor="middle" fontSize="8" fill="#647689"
            style={{ fontFamily: 'Fira Sans, sans-serif' }}>
            {suffix}
          </text>
        </>
      )}
    </svg>
  );
}
