import { ClipboardList } from 'lucide-react';

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
  return Number(value).toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

/**
 * Painel de ranking operacional dos municípios com maior risco.
 * @param {{ data: Array, onSelect: Function }} props
 */
export default function AlertPanel({ data, onSelect }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">Ranking operacional</h2>
          <p className="text-sm text-slate-500">Municípios priorizados por score ambiental e incidência</p>
        </div>
        <ClipboardList className="h-6 w-6 text-slate-700" />
      </div>
      <div className="space-y-3">
        {data.slice(0, 6).map((item, index) => (
          <button
            key={item.geocode}
            onClick={() => onSelect(item)}
            className="flex w-full items-center justify-between rounded-2xl border border-slate-100 bg-slate-50 p-3 text-left transition hover:border-cyan-200 hover:bg-cyan-50"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white text-sm font-black text-slate-700 shadow-sm">
                {index + 1}
              </div>
              <div>
                <p className="font-bold text-slate-950">{item.municipio || item.geocode}</p>
                <p className="text-xs text-slate-500">Incidência: {formatNumber(item.incidencia_100k, 1)} / 100k</p>
              </div>
            </div>
            <span className="text-lg font-black text-slate-950">{formatNumber(item.environmental_risk_score, 0)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
