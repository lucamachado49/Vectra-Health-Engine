/**
 * Botões de decisão humana sobre protocolo gerado pelo agente.
 * @param {{ onApprove: Function, onRevise: Function, onReject: Function, reviewStatus: string|null }} props
 */
export default function HumanApprovalModal({ onApprove, onRevise, onReject, reviewStatus }) {
  return (
    <div>
      <div className="flex flex-col gap-3 md:flex-row">
        <button
          onClick={onApprove}
          id="btn-approve-protocol"
          className="flex-1 rounded-2xl bg-emerald-700 px-4 py-3 text-sm font-bold text-white transition hover:bg-emerald-800"
        >
          Aprovar protocolo
        </button>
        <button
          onClick={onRevise}
          id="btn-revise-protocol"
          className="flex-1 rounded-2xl bg-amber-500 px-4 py-3 text-sm font-bold text-white transition hover:bg-amber-600"
        >
          Solicitar revisão
        </button>
        <button
          onClick={onReject}
          id="btn-reject-protocol"
          className="flex-1 rounded-2xl bg-slate-200 px-4 py-3 text-sm font-bold text-slate-700 transition hover:bg-slate-300"
        >
          Rejeitar
        </button>
      </div>
      {reviewStatus && (
        <div className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">
          Revisão humana registrada: {reviewStatus}
        </div>
      )}
    </div>
  );
}
