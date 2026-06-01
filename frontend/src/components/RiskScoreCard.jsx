import { motion } from 'framer-motion';

/**
 * Card executivo com métrica principal.
 * @param {{ icon: React.ElementType, label: string, value: string, hint: string }} props
 */
export function MetricCard({ icon: Icon, label, value, hint }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-black tracking-tight text-slate-950">{value}</p>
        </div>
        <div className="rounded-2xl bg-slate-100 p-3">
          <Icon className="h-6 w-6 text-slate-700" />
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-500">{hint}</p>
    </motion.div>
  );
}

/**
 * Metric compacta para painel de município.
 * @param {{ icon: React.ElementType, label: string, value: string }} props
 */
export function MiniMetric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <Icon className="h-5 w-5 text-slate-600" />
      <p className="mt-2 text-xs font-medium text-slate-500">{label}</p>
      <p className="text-lg font-black text-slate-950">{value}</p>
    </div>
  );
}
