import { MapPin } from 'lucide-react';

function riskToMapClass(score) {
  if (score >= 80) return 'bg-red-500 shadow-red-200';
  if (score >= 65) return 'bg-orange-500 shadow-orange-200';
  if (score >= 45) return 'bg-amber-400 shadow-amber-200';
  return 'bg-emerald-500 shadow-emerald-200';
}

/**
 * Mapa conceitual de risco epidemiológico.
 * @param {{ data: Array, selectedGeocode: string, onSelect: Function }} props
 */
export default function RiskMap({ data, selectedGeocode, onSelect }) {
  const positioned = data.slice(0, 8).map((item, index) => ({
    ...item,
    left: [18, 42, 66, 29, 55, 78, 35, 61][index % 8],
    top: [30, 22, 39, 58, 63, 70, 78, 48][index % 8],
  }));

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">Mapa de risco epidemiológico</h2>
          <p className="text-sm text-slate-500">Visualização conceitual dos municípios monitorados</p>
        </div>
        <MapPin className="h-6 w-6 text-cyan-700" />
      </div>
      <div className="relative h-[370px] overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-100 via-cyan-50 to-emerald-50">
        <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(to_right,#94a3b8_1px,transparent_1px),linear-gradient(to_bottom,#94a3b8_1px,transparent_1px)] [background-size:34px_34px]" />
        <div className="absolute left-8 top-8 rounded-2xl border border-white/60 bg-white/70 px-4 py-3 shadow-sm backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Camadas ativas</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold">
            <span className="rounded-full bg-cyan-100 px-2 py-1 text-cyan-800">NDWI</span>
            <span className="rounded-full bg-emerald-100 px-2 py-1 text-emerald-800">NDVI</span>
            <span className="rounded-full bg-orange-100 px-2 py-1 text-orange-800">Ilhas de calor</span>
          </div>
        </div>
        {positioned.map((item) => (
          <button
            key={item.geocode}
            onClick={() => onSelect(item)}
            className={`absolute -translate-x-1/2 -translate-y-1/2 rounded-full p-1 transition hover:scale-110 ${
              selectedGeocode === item.geocode ? 'ring-4 ring-slate-950' : ''
            }`}
            style={{ left: `${item.left}%`, top: `${item.top}%` }}
          >
            <span className={`block h-9 w-9 rounded-full ${riskToMapClass(item.environmental_risk_score || 0)} shadow-lg`} />
            <span className="mt-1 block min-w-24 rounded-xl bg-white/90 px-2 py-1 text-xs font-bold text-slate-800 shadow-sm">
              {item.municipio || item.geocode}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
