import { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle, Bot,
  Map, Mic, Paperclip, Send, Settings2, Zap,
} from 'lucide-react';
import { BRAZIL_MUNICIPALITIES, riskColor, topByRisk } from '../data/brazilMunicipalities.js';
import { fetchCopilotAnswer } from '../api/vectraApi.js';

const QUICK_ACTIONS = [
  { label: 'Explore o alerta atual',              icon: AlertTriangle },
  { label: 'Quais áreas precisam de ação hoje?',  icon: Map },
  { label: 'Simular alocação de recursos',        icon: Zap },
  { label: 'Gerar mensagem para a população',     icon: Send },
  { label: 'Revisar plano de resposta',           icon: Settings2 },
];

const INITIAL_MESSAGES = [
  {
    role: 'assistant',
    content: 'Olá! Sou o Vectra Copilot. Como posso ajudar com a vigilância epidemiológica hoje? Você pode perguntar sobre municípios em risco, tendências de surto, alocação de recursos ou gerar mensagens de alerta.',
    time: '09:14',
  },
];

export default function CopilotPage() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [selected]              = useState(BRAZIL_MUNICIPALITIES.find(m => m.municipio === 'Fortaleza') || BRAZIL_MUNICIPALITIES[0]);
  const chatRef                 = useRef(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, loading]);

  async function sendMessage(text) {
    const question = text || input.trim();
    if (!question) return;
    setInput('');
    const userMsg = { role: 'user', content: question, time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    try {
      const res = await fetchCopilotAnswer({ geocode: selected.geocode, question });
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: res.answer,
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Com base nos dados atuais, ${selected.municipio} apresenta índice de risco ${selected.environmental_risk_score}/100 e ${selected.casos_dengue} casos notificados. Os principais fatores são NDWI elevado (${selected.ndwi_mean?.toFixed(2)}), ocupação de leitos (${selected.leitos_ocupacao_pct}%) e condições climáticas favoráveis ao vetor. Recomendo acionar o protocolo de vigilância ativa.`,
        time: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setLoading(false);
    }
  }

  const top5 = topByRisk(5);
  const totalCritical = BRAZIL_MUNICIPALITIES.filter(m => m.environmental_risk_score >= 70).length;

  return (
    <div className="copilot-layout">
      {/* ── Chat principal ── */}
      <div className="chat-card">
        {/* Contexto atual */}
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', background: 'var(--bg)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 8 }}>
            Contexto atual
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
            {[
              ['Risco atual',       'Alto',       'var(--risk-alto)'],
              ['Principais riscos', 'Dengue, Chik.', null],
              ['Munic. em alerta',  '12',         null],
              ['Pop. afetada',      '1,2 mi',     null],
              ['Tendência (7d)',    '↑ Aumento',  'var(--risk-critico)'],
              ['Última atualiz.',   'Há 2 min',   'var(--green)'],
            ].map(([label, val, color]) => (
              <div key={label} style={{ minWidth: 0 }}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 2 }}>{label}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: color || 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick actions */}
        <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 8 }}>Ações rápidas</div>
          <div className="quick-actions">
            {QUICK_ACTIONS.map(({ label, icon: Icon }) => (
              <button key={label} type="button" className="quick-action-btn" onClick={() => sendMessage(label)}>
                <Icon size={12} /> {label}
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div style={{ padding: '14px 20px 6px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
          Conversa com o Copilot
        </div>

        <div className="chat-messages" ref={chatRef}>
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className={`chat-avatar ${msg.role === 'assistant' ? 'bot' : 'user'}`}>
                {msg.role === 'assistant' ? <Bot size={15} /> : 'V'}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>
                    {msg.role === 'assistant' ? 'Vectra Copilot' : 'Você'}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{msg.time}</span>
                </div>
                <div className={`chat-bubble ${msg.role}`}>{msg.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-msg">
              <div className="chat-avatar bot"><Bot size={15} /></div>
              <div className="chat-bubble bot loading-pulse">Analisando dados epidemiológicos...</div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <div className="chat-input-row">
            <textarea
              className="chat-textarea"
              rows={1}
              placeholder="Como posso ajudar hoje? Faça sua pergunta ou escolha uma ação rápida acima."
              value={input}
              disabled={loading}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
            />
            <button type="button" className="chat-send-btn" onClick={() => sendMessage()} disabled={loading}>
              <Send size={16} />
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
            <button type="button" style={{ color: 'var(--text-muted)' }}><Paperclip size={14} /></button>
            <button type="button" style={{ color: 'var(--text-muted)' }}><Mic size={14} /></button>
            <button type="button" style={{ color: 'var(--text-muted)' }}><Settings2 size={14} /></button>
            <span className="chat-disclaimer" style={{ marginLeft: 'auto' }}>
              A IA pode cometer erros. Sempre valide as informações antes de tomar decisões.
            </span>
          </div>
        </div>
      </div>

      {/* ── Painel de risco ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="card">
          <div className="card-header"><h3>Panorama de risco</h3></div>
          <div className="card-body" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 42, fontWeight: 900, color: riskColor(selected.environmental_risk_score) }}>
              {(selected.environmental_risk_score / 10).toFixed(1)}
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, color: riskColor(selected.environmental_risk_score), marginBottom: 6 }}>
              Risco Alto
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
              Risco elevado para dengue em {totalCritical} municípios.
            </div>
            <button type="button" className="btn btn-ghost" style={{ fontSize: 12 }}>Ver detalhes do risco →</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Top 5 regiões críticas</h3><span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Índice de risco</span></div>
          <div className="card-body" style={{ paddingTop: 6 }}>
            {top5.map((m, i) => (
              <div key={m.geocode} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none', fontSize: 13 }}>
                <span style={{ width: 18, fontWeight: 700, color: 'var(--text-muted)', fontSize: 12 }}>{i + 1}</span>
                <span style={{ flex: 1, fontWeight: 500 }}>{m.municipio} ({m.uf})</span>
                <span style={{ padding: '2px 8px', borderRadius: 5, fontWeight: 700, fontSize: 12, background: m.environmental_risk_score >= 85 ? 'var(--risk-critico-bg)' : 'var(--risk-alto-bg)', color: riskColor(m.environmental_risk_score) }}>
                  {(m.environmental_risk_score / 10).toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Alertas ativos ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="card">
          <div className="card-header"><h3>Ações recomendadas</h3></div>
          <div className="card-body" style={{ paddingTop: 6 }}>
            {[
              ['Mobilizar controle vetorial em 32 municípios', 'Crítica'],
              ['Mobilizar equipes para visitas domiciliares',  'Alta'],
              ['Ampliar comunicação preventiva',               'Alta'],
              ['Intensificar busca ativa de casos',            'Média'],
              ['Verificar estoque de insumos e kits',          'Baixa'],
            ].map(([action, priority]) => (
              <div key={action} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                <span style={{ flex: 1 }}>{action}</span>
                <span style={{ padding: '2px 7px', borderRadius: 4, fontWeight: 700, fontSize: 10,
                  background: priority === 'Crítica' ? 'var(--risk-critico-bg)' : priority === 'Alta' ? 'var(--risk-alto-bg)' : priority === 'Média' ? 'var(--risk-atencao-bg)' : 'var(--risk-baixo-bg)',
                  color: priority === 'Crítica' ? 'var(--risk-critico)' : priority === 'Alta' ? 'var(--risk-alto)' : priority === 'Média' ? 'var(--risk-atencao)' : 'var(--risk-baixo)',
                }}>{priority}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Alertas ativos (15)</h3></div>
          <div className="card-body" style={{ paddingTop: 6 }}>
            {[
              ['9 Críticos',  'Exigem ação imediata',     'var(--risk-critico)'],
              ['4 Altos',     'Monitoramento intensivo',  'var(--risk-alto)'],
              ['2 Médios',    'Acompanhar evolução',      'var(--risk-atencao)'],
              ['0 Baixos',    'Situação controlada',      'var(--risk-baixo)'],
            ].map(([label, sub, color]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ fontWeight: 700, fontSize: 13, color }}>{label}</span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>{sub}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
