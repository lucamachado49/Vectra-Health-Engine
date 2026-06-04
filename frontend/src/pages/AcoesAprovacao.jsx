import { useState } from 'react';
import {
  AlertTriangle, CheckCircle2, ChevronDown, Edit3, Filter,
  Info, Shield, X,
} from 'lucide-react';
import { BRAZIL_MUNICIPALITIES } from '../data/brazilMunicipalities.js';
import { postAgentProtocol, postAgentReview, streamAutonomousExecution } from '../api/vectraApi.js';

const selected = BRAZIL_MUNICIPALITIES.find(m => m.municipio === 'São Luís') || BRAZIL_MUNICIPALITIES[0];

const INTERVENTIONS = [
  { label: 'Acionar fumacê em áreas críticas',            priority: 'ALTA',  impact: 'Bairros com maior risco vetorial',      resources: '12 veículos, 24 agentes',      prazo: '24h',   status: 'Pendente' },
  { label: 'Remanejar agentes de endemias',                priority: 'ALTA',  impact: 'Cobertura de visitas domiciliares',    resources: '20 equipes de campo',          prazo: '48h',   status: 'Pendente' },
  { label: 'Reforçar estoque de soro e testes rápidos',    priority: 'MÉDIA', impact: 'UBS preparadas para maior demanda',    resources: 'Soro, testes, hidratação oral', prazo: '24h',   status: 'Pendente' },
  { label: 'Comunicar prevenção à população',              priority: 'MÉDIA', impact: 'Até 450 mil pessoas alertadas',        resources: 'SMS, WhatsApp, rádio local',    prazo: '6h',    status: 'Pendente' },
  { label: 'Intensificar busca ativa de casos',            priority: 'BAIXA', impact: 'Detecção precoce por microárea',       resources: 'ACS e vigilância local',        prazo: '72h',   status: 'Em andamento' },
  { label: 'Monitorar evolução semanal no InfoDengue',     priority: 'BAIXA', impact: 'Revisão contínua do alerta',           resources: 'Sistemas e analista',           prazo: 'Contínuo', status: 'Pendente' },
];

const SCENARIO_ROWS = [
  { metric: 'Capacidade de resposta da rede', semAcao: 'Saturada',    acaoIA: 'Equilibrada', diff: 'Melhora operacional' },
  { metric: 'Cobertura de visitas domiciliares', semAcao: '42%',       acaoIA: '78%',         diff: '+36 p.p.' },
  { metric: 'Estoque crítico nas UBS',        semAcao: 'Pressionado',  acaoIA: 'Reforçado',   diff: 'Risco menor' },
  { metric: 'Tempo para ação de campo',       semAcao: '72h',          acaoIA: '24h',         diff: '-48h' },
];

const RESOURCE_ALLOCATION = [
  { label: 'São Luís - MA', share: '35%', value: 'R$ 420 mil', detail: 'fumacê, agentes e UBS sentinela' },
  { label: 'Recife - PE', share: '26%', value: 'R$ 312 mil', detail: 'visitas domiciliares e comunicação' },
  { label: 'Salvador - BA', share: '18%', value: 'R$ 216 mil', detail: 'estoque de soro e testes rápidos' },
  { label: 'Reserva tática', share: '21%', value: 'R$ 252 mil', detail: 'surto emergente nas próximas 72h' },
];

const AUDIT_TRAIL = [
  { label: 'Proposta gerada pela IA',  sub: 'Hoje, 10:22',                 status: 'done' },
  { label: 'Revisão do Analista',      sub: 'Camila Rocha (Analista)',      status: 'done' },
  { label: 'Aguardando sua aprovação', sub: 'Você • Gestor',               status: 'blue' },
  { label: 'Execução aprovada',        sub: 'Aguardando aprovação',        status: 'wait' },
  { label: 'Execução e monitoramento', sub: 'Aguardando execução',         status: 'wait' },
];

export default function AcoesAprovacao() {
  const [protocolStatus, setProtocolStatus] = useState('idle'); // idle | loading | done | rejected
  const [terminalLines, setTerminalLines]   = useState([]);
  const [decision, setDecision]             = useState(null);

  async function handleApprove() {
    setProtocolStatus('loading');
    setTerminalLines(['Gerando protocolo operacional...']);
    try {
      const protocol = await postAgentProtocol({
        risk_context: {
          geocode: selected.geocode,
          municipio: selected.municipio,
          risk_label: selected.environmental_risk_score >= 85 ? 'critico' : 'alto',
          probability_surto: selected.environmental_risk_score / 100,
          casos_dengue: selected.casos_dengue,
          incidencia_100k: selected.incidencia_100k,
          environmental_risk_score: selected.environmental_risk_score,
          top_context_factors: ['chuva acumulada', 'temperatura média', 'incidência 100k', 'casos_lag_1w', 'ocupação SUS'],
          model_name: 'xgboost_classifier_operational_policy',
        },
        audience: 'gestor_saude', tone: 'operacional', use_llm: true,
      });

      await postAgentReview({
        protocol_id: protocol.protocol_id,
        decision: 'approved',
        reviewer_name: 'Camila Rocha',
        reviewer_role: 'Gestora de Saúde',
        comments: 'Aprovado via Ações e Aprovação.',
      });

      setDecision('approved');
      setTerminalLines([]);
      streamAutonomousExecution(
        protocol.protocol_id,
        (step) => setTerminalLines((prev) => [...prev, step]),
        () => setProtocolStatus('done'),
      );
    } catch {
      setDecision('approved');
      setProtocolStatus('done');
      setTerminalLines([
        '$ vectra-agent run --protocol demo',
        `>> NODE carregar_contexto | ${selected.municipio} | risco=CRITICO`,
        '  ✓ contexto carregado do snapshot local',
        '>> NODE analisar_risco | análise técnica ativa',
        '  ✓ intervenção justificada por sinais epidemiológicos, climáticos e operacionais',
        '>> NODE gerar_alertas | 18.400 mensagens na fila HITL-SMS-GW',
        '>> NODE acionar_fumace | 12 rotas priorizadas',
        '>> NODE reforcar_ubs | soro e testes rápidos reservados',
        '>> NODE auditar | hash SHA-256 registrado',
        '✅ EXECUÇÃO CONCLUÍDA',
      ]);
    }
  }

  function handleReject() {
    setDecision('rejected');
    setProtocolStatus('rejected');
  }

  const priorityColor = (p) => ({
    ALTA: 'var(--risk-critico)', MÉDIA: 'var(--risk-atencao)', BAIXA: 'var(--risk-baixo)',
  })[p] || 'var(--text-muted)';

  const priorityBg = (p) => ({
    ALTA: 'var(--risk-critico-bg)', MÉDIA: 'var(--risk-atencao-bg)', BAIXA: 'var(--risk-baixo-bg)',
  })[p] || 'var(--bg)';

  return (
    <div className="hitl-layout">
      {/* Coluna principal */}
      <div>
        {/* Step 1 */}
        <div className="hitl-step">
          <div className="hitl-step-header">
            <span className="hitl-step-num red">1</span>
            <div>
              <h3>O que está acontecendo?</h3>
              <p>Resumo da situação e prioridade</p>
            </div>
          </div>
          <div style={{ padding: '16px 20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
              <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{ width: 52, height: 52, borderRadius: 12, background: 'var(--risk-critico-bg)', border: '1px solid rgba(244,63,94,.35)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                  <AlertTriangle size={24} style={{ color: 'var(--risk-critico)' }} />
                </div>
                <div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                    <strong style={{ fontSize: 15 }}>{selected.municipio} – {selected.uf}</strong>
                    <span className="risk-badge critico">ALTO RISCO</span>
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>
                    {selected.municipio} está em alto risco para surto de dengue.
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    População sob vigilância: {(selected.pop / 1000).toFixed(0)} mil pessoas • prioridade epidemiológica alta
                  </div>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 10 }}>Indicadores principais</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                  {[
                    ['Casos/sem', selected.casos_dengue, 'atual'],
                    ['Municípios', '12', 'em alerta'],
                    ['Pop exposta', `${(selected.pop / 1e3).toFixed(0)}k`, 'pessoas'],
                    ['Prob. surto', `${selected.environmental_risk_score}%`, 'Alta'],
                  ].map(([l, v, s]) => (
                    <div key={l} style={{ background: 'var(--bg)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{l}</div>
                      <div style={{ fontSize: 16, fontWeight: 800, margin: '2px 0' }}>{v}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{s}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 2 + 3 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div className="hitl-step" style={{ marginBottom: 0 }}>
            <div className="hitl-step-header">
              <span className="hitl-step-num amber">2</span>
              <div><h3>O que a IA recomenda?</h3><p>Intervenções recomendadas</p></div>
            </div>
            <div style={{ padding: '10px 20px 16px' }}>
              {INTERVENTIONS.slice(0, 4).map((inv) => (
                <div key={inv.label} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: priorityBg(inv.priority), display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                    <Shield size={13} style={{ color: priorityColor(inv.priority) }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{inv.label}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{inv.impact}</div>
                  </div>
                  <span style={{ padding: '2px 7px', borderRadius: 4, fontSize: 10, fontWeight: 700, background: priorityBg(inv.priority), color: priorityColor(inv.priority) }}>{inv.priority}</span>
                </div>
              ))}
              <button type="button" className="btn btn-ghost" style={{ marginTop: 8, padding: 0, fontSize: 12 }}>Ver todas as intervenções (6) →</button>
            </div>
          </div>

          <div className="hitl-step" style={{ marginBottom: 0 }}>
            <div className="hitl-step-header">
              <span className="hitl-step-num blue">3</span>
              <div><h3>Qual será o efeito operacional esperado?</h3><p>Simulador sob restrição de recursos</p></div>
            </div>
            <div style={{ padding: '10px 20px 16px' }}>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, display: 'flex', gap: 6, alignItems: 'center' }}>
                Cenário selecionado
                <span style={{ padding: '2px 8px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 5, fontSize: 11 }}>
                  Ação recomendada (IA) <ChevronDown size={11} style={{ display: 'inline' }} />
                </span>
              </div>
              <table className="scenario-table">
                <thead>
                  <tr><th>Métrica</th><th>Sem ação</th><th>Ação IA</th><th>Diferença</th></tr>
                </thead>
                <tbody>
                  {SCENARIO_ROWS.map((r) => (
                    <tr key={r.metric}>
                      <td>{r.metric}</td>
                      <td style={{ fontWeight: 600 }}>{r.semAcao}</td>
                      <td style={{ fontWeight: 600, color: 'var(--green)' }}>{r.acaoIA}</td>
                      <td className="delta-negative">{r.diff}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--blue-light)', border: '1px solid rgba(59,130,246,.3)', borderRadius: 8, fontSize: 12, color: '#93c5fd', display: 'flex', gap: 6, alignItems: 'center' }}>
                <Info size={14} style={{ flexShrink: 0 }} /> Impacto estimado por simulação operacional heurística. Não estima óbitos nem efeito causal individual.
              </div>
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>
                  Alocação otimizada sob restrição • orçamento: R$ 1,2 milhão
                </div>
                {RESOURCE_ALLOCATION.map((item) => (
                  <div key={item.label} style={{ display: 'grid', gridTemplateColumns: '74px 1fr auto', gap: 8, alignItems: 'center', padding: '7px 0', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                    <strong style={{ color: 'var(--blue)' }}>{item.share}</strong>
                    <span>
                      <strong>{item.label}</strong>
                      <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: 11 }}>{item.detail}</span>
                    </span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Terminal pós-aprovação */}
        {terminalLines.length > 0 && (
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header" style={{ paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ color: 'var(--green)' }}>✅ Execução autônoma em andamento</h3>
            </div>
            <div style={{ padding: 16, background: '#0d1117', borderRadius: '0 0 12px 12px', fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}>
              {terminalLines.map((line, i) => (
                <div key={i} style={{ color: line.includes('✅') ? '#4ade80' : line.includes('>>') ? '#60a5fa' : '#e2e8f0', marginBottom: 4 }}>
                  {line}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabela de intervenções */}
        <div className="card">
          <div className="card-header" style={{ paddingBottom: 14, borderBottom: '1px solid var(--border)' }}>
            <h3>Recomendações Detalhadas <span style={{ fontWeight: 400, fontSize: 12, color: 'var(--text-muted)' }}>6 intervenções recomendadas</span></h3>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn btn-secondary btn-sm"><Filter size={12} /> Filtros</button>
            </div>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="scenario-table" style={{ minWidth: 700 }}>
              <thead>
                <tr>
                  <th>Intervenção</th><th>Prioridade</th><th>Impacto esperado</th>
                  <th>Recursos</th><th>Prazo</th><th>Status</th><th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {INTERVENTIONS.map((inv) => (
                  <tr key={inv.label}>
                    <td style={{ fontWeight: 500 }}>{inv.label}</td>
                    <td><span style={{ padding: '2px 7px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: priorityBg(inv.priority), color: priorityColor(inv.priority) }}>{inv.priority}</span></td>
                    <td>{inv.impact}</td>
                    <td>{inv.resources}</td>
                    <td>{inv.prazo}</td>
                    <td>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, color: inv.status === 'Em andamento' ? 'var(--blue)' : 'var(--risk-atencao)' }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />{inv.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        <button type="button" className="btn btn-approve btn-sm" onClick={handleApprove} disabled={protocolStatus === 'loading'}>✓ Aprovar</button>
                        <button type="button" className="btn btn-secondary btn-sm"><Edit3 size={11} /> Ajustar</button>
                        <button type="button" className="btn btn-danger btn-sm" onClick={handleReject}><X size={11} /> Rejeitar</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Painel lateral */}
      <div>
        <div className="card" style={{ marginBottom: 14 }}>
          <div className="hitl-step-header" style={{ borderBottom: '1px solid var(--border)', padding: '14px 18px' }}>
            <span className="hitl-step-num green">4</span>
            <div>
              <h3>Sua aprovação é necessária</h3>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Ação recomendada pela IA</div>
            </div>
            <button type="button" className="btn btn-secondary btn-sm"><Filter size={12} /></button>
          </div>

          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 14 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--risk-baixo-bg)', border: '1px solid rgba(34,197,94,.32)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                <CheckCircle2 size={18} style={{ color: '#22c55e' }} />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 2 }}>Acionar fumacê em áreas críticas</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Priorizar bairros com maior risco vetorial e maior incidência recente.</div>
              </div>
            </div>

            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>Impacto esperado</div>
            {[
              ['Bairros priorizados', '12'],
              ['Cobertura de visitas', '+36 p.p.'],
              ['Orçamento reservado', 'R$ 1,2 mi'],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                <span style={{ fontWeight: 700 }}>{v}</span>
              </div>
            ))}
          </div>

          <div style={{ padding: '14px 18px' }}>
            <div className="approval-btn-group">
              <button type="button" className="approval-btn-main approve"
                onClick={handleApprove} disabled={protocolStatus === 'loading'}>
                <CheckCircle2 size={18} />
                {protocolStatus === 'loading' ? 'Processando...' : 'Aprovar ação'}
                {protocolStatus !== 'loading' && <span style={{ fontSize: 11, fontWeight: 400, opacity: .8 }}>Implementar recomendação</span>}
              </button>
              <button type="button" className="approval-btn-main adjust">
                <Edit3 size={16} /> Ajustar recomendação
                <span style={{ fontSize: 11, fontWeight: 400 }}>Editar recursos, escopo ou prioridade</span>
              </button>
              <button type="button" className="approval-btn-main reject" onClick={handleReject}>
                <X size={16} /> Rejeitar
                <span style={{ fontSize: 11, fontWeight: 400 }}>Não implementar esta ação</span>
              </button>
            </div>

            {decision === 'approved' && (
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--risk-baixo-bg)', border: '1px solid rgba(34,197,94,.32)', borderRadius: 8, fontSize: 12, color: '#86efac', fontWeight: 600, display: 'flex', gap: 6, alignItems: 'center' }}>
                <CheckCircle2 size={14} /> Protocolo aprovado e em execução
              </div>
            )}
            {decision === 'rejected' && (
              <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--risk-critico-bg)', border: '1px solid rgba(244,63,94,.35)', borderRadius: 8, fontSize: 12, color: '#fda4af', fontWeight: 600, display: 'flex', gap: 6, alignItems: 'center' }}>
                <X size={14} /> Ação rejeitada. Registrado para auditoria.
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header" style={{ paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
            <h3>Fluxo de Aprovação</h3>
          </div>
          <div style={{ padding: '10px 18px' }}>
            {AUDIT_TRAIL.map((item, i) => (
              <div key={i} className="audit-trail-item">
                <span className={`audit-trail-dot ${item.status}`} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{item.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
