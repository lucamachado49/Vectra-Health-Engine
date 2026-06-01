import { useState } from 'react';
import { Brain, HeartPulse, Loader2 } from 'lucide-react';
import AgentRecommendation from '../components/AgentRecommendation.jsx';
import HumanApprovalModal from '../components/HumanApprovalModal.jsx';
import { postAgentProtocol, postAgentReview } from '../api/vectraApi.js';

function buildFallbackProtocol(selected, prediction) {
  const risk = prediction?.risk_label || selected?.risco_ambiental_label || 'medio';
  return {
    protocol_id: `vectra-demo-${selected?.geocode || '0000000'}`,
    status: 'pending_review',
    title: `Protocolo preventivo para ${selected?.municipio || 'região monitorada'}`,
    executive_summary: `O Vectra Health identificou risco ${risk}. A recomendação é preventiva e exige aprovação humana.`,
    recommended_actions: [
      'Validar alerta com a coordenação de vigilância epidemiológica.',
      'Reforçar monitoramento de casos suspeitos nas UBS.',
      'Direcionar agentes comunitários para áreas com maior risco ambiental.',
      'Preparar comunicação preventiva para a população local.',
      'Verificar estoque de hidratação e insumos básicos.',
    ],
    message_to_health_units:
      'Alerta preventivo Vectra Health\n\nFoi identificado aumento de risco epidemiológico na região monitorada. Revisar o alerta, validar dados locais e preparar ações preventivas proporcionais ao risco.',
  };
}

function normalizeRiskLabel(label) {
  const normalized = String(label || 'medio')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

  if (['baixo', 'medio', 'alto', 'critico'].includes(normalized)) {
    return normalized;
  }
  return 'medio';
}

/**
 * Centro de decisão com LLM Agent e Human-in-the-Loop.
 * @param {{ selected: object|null, prediction: object|null }} props
 */
export default function AgentCenter({ selected, prediction }) {
  const [protocol, setProtocol] = useState(null);
  const [loading, setLoading] = useState(false);
  const [reviewStatus, setReviewStatus] = useState(null);

  async function generateProtocol() {
    if (!selected) return;
    setLoading(true);
    setReviewStatus(null);
    const riskLabel = normalizeRiskLabel(prediction?.risk_label || selected.risco_ambiental_label);
    const payload = {
      risk_context: {
        geocode: selected.geocode,
        municipio: selected.municipio,
        ano: selected.ano,
        semana_epidemiologica: selected.semana_epidemiologica,
        risk_label: riskLabel,
        probability_surto: prediction?.probability_surto || null,
        casos_dengue: selected.casos_dengue,
        incidencia_100k: selected.incidencia_100k,
        temp_media_7d: selected.temp_media_7d,
        chuva_acumulada_7d: selected.chuva_acumulada_7d,
        umidade_media_7d: selected.umidade_media_7d,
        environmental_risk_score: selected.environmental_risk_score,
        top_context_factors: prediction?.top_context_factors || [
          'score ambiental elevado',
          'condições climáticas favoráveis ao vetor',
          'monitoramento epidemiológico recomendado',
        ],
        model_name: prediction?.model_name || 'best_model',
      },
      audience: 'gestor_saude',
      tone: 'operacional',
      use_llm: false,
    };
    try {
      const response = await postAgentProtocol(payload);
      setProtocol(response);
    } catch {
      setProtocol(buildFallbackProtocol(selected, prediction));
    } finally {
      setLoading(false);
    }
  }

  async function submitReview(decision) {
    if (!protocol) return;
    setReviewStatus(decision);
    try {
      await postAgentReview({
        protocol_id: protocol.protocol_id,
        decision,
        reviewer_name: 'Gestor Demo',
        reviewer_role: 'Coordenação de Vigilância',
        comments: decision === 'approved' ? 'Ação aprovada no protótipo.' : 'Revisão registrada no protótipo.',
      });
    } catch { /* estado visual já demonstra a ação */ }
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-950">Centro de decisão LLM</h2>
          <p className="text-sm text-slate-500">Geração de protocolo com aprovação humana obrigatória</p>
        </div>
        <HeartPulse className="h-6 w-6 text-red-700" />
      </div>
      <button
        onClick={generateProtocol}
        disabled={!selected || loading}
        id="btn-generate-protocol"
        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-cyan-700 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-100 transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Brain className="h-5 w-5" />}
        Gerar protocolo de contingência
      </button>
      {protocol && (
        <div className="mt-5 space-y-4">
          <AgentRecommendation protocol={protocol} />
          <HumanApprovalModal
            onApprove={() => submitReview('approved')}
            onRevise={() => submitReview('revision_requested')}
            onReject={() => submitReview('rejected')}
            reviewStatus={reviewStatus}
          />
        </div>
      )}
    </div>
  );
}
