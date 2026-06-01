/**
 * VectraLogo — Logo vetorial (SVG) do Vectra Health.
 * Escudo em "V" metálico com núcleo ciano + wordmark "VECTRA".
 * Renderiza nítido em qualquer tamanho, sem dependência de PNG.
 *
 * Props:
 *   size        — altura do ícone em px (default 34)
 *   showText    — exibe o wordmark "VECTRA" ao lado (default true)
 *   textColor   — cor do texto (default '#ffffff')
 */
export default function VectraLogo({ size = 34, showText = true, textColor = '#ffffff' }) {
  const uid = 'vlogo';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"
        style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,.45))' }}>
        <defs>
          <linearGradient id={`${uid}-steel`} x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#e8edf5" />
            <stop offset="0.45" stopColor="#9aa7ba" />
            <stop offset="0.55" stopColor="#6b7888" />
            <stop offset="1" stopColor="#2b3442" />
          </linearGradient>
          <linearGradient id={`${uid}-core`} x1="32" y1="6" x2="32" y2="58" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#7fe9ff" />
            <stop offset="0.5" stopColor="#1ea7e6" />
            <stop offset="1" stopColor="#0a4d7a" />
          </linearGradient>
          <linearGradient id={`${uid}-v`} x1="20" y1="14" x2="44" y2="50" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#f4f8ff" />
            <stop offset="1" stopColor="#8b97a8" />
          </linearGradient>
        </defs>

        {/* Escudo externo metálico */}
        <path d="M32 3 L57 13 V33 C57 47 46 56 32 61 C18 56 7 47 7 33 V13 Z"
          fill={`url(#${uid}-steel)`} stroke="#cdd6e3" strokeWidth="1" />

        {/* Núcleo interno ciano */}
        <path d="M32 9 L51 16.5 V32.5 C51 43.5 42.5 51 32 55 C21.5 51 13 43.5 13 32.5 V16.5 Z"
          fill="#0a1626" stroke={`url(#${uid}-core)`} strokeWidth="1.2" />

        {/* Chevron superior (brilho) */}
        <path d="M22 17 L32 22 L42 17 L42 21 L32 26 L22 21 Z" fill={`url(#${uid}-core)`} opacity="0.9" />

        {/* "V" central metálico */}
        <path d="M19 23 L28 23 L32 40 L36 23 L45 23 L35 51 L29 51 Z"
          fill={`url(#${uid}-v)`} stroke="#dfe7f2" strokeWidth="0.6" strokeLinejoin="round" />
      </svg>

      {showText && (
        <span style={{
          fontWeight: 800,
          fontSize: size * 0.62,
          letterSpacing: '.14em',
          color: textColor,
          fontFamily: 'Inter, sans-serif',
          lineHeight: 1,
        }}>
          VECTRA
        </span>
      )}
    </span>
  );
}
