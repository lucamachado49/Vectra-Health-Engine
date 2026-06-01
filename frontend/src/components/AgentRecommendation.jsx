import { CheckCircle2 } from 'lucide-react';

/**
 * Exibe o protocolo gerado pelo LLM Agent.
 * @param {{ protocol: object }} props
 */
export default function AgentRecommendation({ protocol }) {
  if (!protocol) return null;

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-cyan-200 bg-cyan-50 p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-wide text-cyan-700">{protocol.protocol_id}</p>
            <h3 className="mt-1 text-lg font-black text-cyan-950">{protocol.title}</h3>
          </div>
          <span className="rounded-full border border-cyan-200 bg-white px-3 py-1 text-xs font-bold text-cyan-800">
            {protocol.status || 'pending_review'}
          </span>
        </div>
        <p className="mt-3 text-sm leading-6 text-cyan-950">{protocol.executive_summary}</p>
      </div>

      <div>
        <p className="mb-2 text-sm font-black text-slate-950">Ações recomendadas</p>
        <ul className="space-y-2">
          {(protocol.recommended_actions || []).slice(0, 5).map((action, index) => (
            <li key={index} className="flex gap-2 rounded-2xl bg-slate-50 p-3 text-sm text-slate-700">
              <CheckCircle2 className="mt-0.5 h-4 w-4 flex-none text-emerald-700" />
              {action}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm font-black text-slate-950">Mensagem para UBS</p>
        <pre className="mt-2 whitespace-pre-wrap rounded-2xl bg-white p-3 text-xs leading-5 text-slate-700">
          {protocol.message_to_health_units}
        </pre>
      </div>
    </div>
  );
}
