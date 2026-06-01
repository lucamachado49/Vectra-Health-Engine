import { Brain } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';

const FEATURE_IMPORTANCE_DATA = [
  { feature: 'casos_lag_1w', importance: 88 },
  { feature: 'chuva_14d', importance: 76 },
  { feature: 'temp_media_7d', importance: 69 },
  { feature: 'umidade_7d', importance: 63 },
  { feature: 'critical_area_pct', importance: 58 },
  { feature: 'incidencia_100k', importance: 54 },
];

/**
 * Gráfico de importância das variáveis do modelo.
 * @param {{ data?: Array }} props
 */
export default function FeatureImportanceChart({ data = FEATURE_IMPORTANCE_DATA }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">Explicabilidade do modelo</h2>
          <p className="text-sm text-slate-500">Variáveis mais influentes na classificação de risco</p>
        </div>
        <Brain className="h-6 w-6 text-violet-700" />
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20, top: 5, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="feature" width={130} />
            <Tooltip />
            <Bar dataKey="importance" name="Importância">
              {data.map((_, index) => <Cell key={index} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
