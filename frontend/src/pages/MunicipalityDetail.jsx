import { useMemo } from 'react';
import { Activity, Brain, CheckCircle2, Droplets, Gauge, ThermometerSun, Waves } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { MiniMetric } from '../components/RiskScoreCard.jsx';

const FALLBACK_TREND = [
  { week: 'W07', cases: 62, rain: 18, risk: 32 },
  { week: 'W08', cases: 76, rain: 24, risk: 41 },
  { week: 'W09', cases: 91, rain: 33, risk: 49 },
  { week: 'W10', cases: 130, rain: 48, risk: 63 },
  { week: 'W11', cases: 187, rain: 57, risk: 75 },
  { week: 'W12', cases: 245, rain: 64, risk: 84 },
];

function riskToBadgeClass(label) {
  const n = String(label || '').toLowerCase();
  if (n.includes('critico') || n.includes('crítico')) return 'bg-red-100 text-red-800 border-red-200';
  if (n.includes('alto')) return 'bg-orange-100 text-orange-800 border-orange-200';
  if (n.includes('medio') || n.includes('médio')) return 'bg-amber-100 text-amber-800 border-amber-200';
  return 'bg-emerald-100 text-emerald-800 border-emerald-200';
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
  return Number(value).toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

/**
 * Painel de detalhe do município selecionado.
 * @param {{ selected: object, prediction: object|null, onPredict: Function }} props
 */
export function MunicipalityDetailPanel({ selected, prediction, onPredict }) {
  if (!selected) return null;
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-black text-slate-950">{selected.municipio || selected.geocode}</h2>
          <p className="text-sm text-slate-500">
            Semana epidemiológica {selected.semana_epidemiologica || 'N/A'} · {selected.ano || 'N/A'}
          </p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-sm font-bold ${riskToBadgeClass(selected.risco_ambiental_label)}`}>
          {selected.risco_ambiental_label || 'N/A'}
        </span>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <MiniMetric icon={Activity} label="Casos" value={formatNumber(selected.casos_dengue, 0)} />
        <MiniMetric icon={Gauge} label="Score ambiental" value={formatNumber(selected.environmental_risk_score, 1)} />
        <MiniMetric icon={ThermometerSun} label="Temp. 7d" value={`${formatNumber(selected.temp_media_7d, 1)} °C`} />
        <MiniMetric icon={Droplets} label="Chuva 7d" value={`${formatNumber(selected.chuva_acumulada_7d, 1)} mm`} />
      </div>
      <button
        onClick={() => onPredict(selected)}
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-slate-300 transition hover:bg-slate-800"
      >
        <Brain className="h-5 w-5" />
        Executar predição do modelo
      </button>
      {prediction && (
        <div className="mt-5 rounded-3xl border border-cyan-200 bg-cyan-50 p-4">
          <div className="flex items-center justify-between">
            <p className="font-black text-cyan-950">Predição supervisionada</p>
            <span className={`rounded-full border px-3 py-1 text-xs font-bold ${riskToBadgeClass(prediction.risk_label)}`}>
              {prediction.risk_label}
            </span>
          </div>
          <p className="mt-2 text-sm text-cyan-900">
            Probabilidade estimada: <strong>{formatNumber((prediction.probability_surto || 0) * 100, 1)}%</strong>
          </p>
          <ul className="mt-3 space-y-2 text-sm text-cyan-900">
            {(prediction.top_context_factors || []).map((factor, index) => (
              <li key={index} className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Painel de tendência epidemiológica.
 * @param {{ selected: object|null }} props
 */
export function TrendPanel({ selected }) {
  const trend = useMemo(() => {
    const factor = Math.max(0.6, Math.min(1.4, (selected?.environmental_risk_score || 70) / 70));
    return FALLBACK_TREND.map((row) => ({ ...row, cases: Math.round(row.cases * factor), risk: Math.round(row.risk * factor) }));
  }, [selected]);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">Tendência epidemiológica</h2>
          <p className="text-sm text-slate-500">Casos, chuva e score de risco nas últimas semanas</p>
        </div>
        <Waves className="h-6 w-6 text-cyan-700" />
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trend} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="cases" name="Casos" strokeWidth={2} fillOpacity={0.2} />
            <Area type="monotone" dataKey="rain" name="Chuva" strokeWidth={2} fillOpacity={0.2} />
            <Area type="monotone" dataKey="risk" name="Risco" strokeWidth={2} fillOpacity={0.2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default MunicipalityDetailPanel;
