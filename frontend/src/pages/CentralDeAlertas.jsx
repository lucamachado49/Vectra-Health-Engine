import { useState } from 'react';
import {
  AlertTriangle, Bell, ChevronRight, Copy, Eye, FileText,
  Filter, Plus, Share2, TrendingUp, X,
} from 'lucide-react';
import Gauge from '../components/Gauge.jsx';

/* Severidade → classe de badge / cor */
const SEV = {
  'MUITO ALTO': { cls: 'critico', color: '#fb7185' },
  ALTO:         { cls: 'alto',    color: '#fdba74' },
  'MÉDIO':      { cls: 'atencao', color: '#fde047' },
  BAIXO:        { cls: 'baixo',   color: '#86efac' },
};

const STATUS = {
  Ativo:              '#f43f5e',
  'Em investigação':  '#facc15',
  'Em monitoramento': '#38bdf8',
};

const ALERTS = [
  { id: 'ALT-2025-00073', sev: 'MUITO ALTO', titulo: 'Surto de Dengue em expansão', desc: 'Crescimento acelerado de casos confirmados.', doenca: 'Dengue', regiao: 'Salvador, Lauro de Freitas, Simões Filho +3', inicio: '14/05 08:23', atualizado: '14/05 10:42', status: 'Ativo', score: 86.4, munic: 5 },
  { id: 'ALT-2025-00072', sev: 'MUITO ALTO', titulo: 'Aumento expressivo de casos', desc: 'Tendência de crescimento acima do esperado.', doenca: 'Chikungunya', regiao: 'Feira de Santana, Conceição do Jacuípe +2', inicio: '13/05 15:10', atualizado: '14/05 09:18', status: 'Ativo', score: 84.1, munic: 3 },
  { id: 'ALT-2025-00071', sev: 'ALTO', titulo: 'Elevação de casos prováveis', desc: 'Aumento significativo nas últimas 72h.', doenca: 'Zika', regiao: 'Ilhéus, Itabuna', inicio: '13/05 11:05', atualizado: '14/05 08:30', status: 'Em investigação', score: 78.2, munic: 2 },
  { id: 'ALT-2025-00070', sev: 'MÉDIO', titulo: 'Chuvas intensas e risco de leptospirose', desc: 'Condições ambientais favoráveis à transmissão.', doenca: 'Leptospirose', regiao: 'Vitória da Conquista, Jequié +1', inicio: '12/05 18:40', atualizado: '14/05 07:51', status: 'Em monitoramento', score: 58.0, munic: 3 },
  { id: 'ALT-2025-00069', sev: 'ALTO', titulo: 'Aumento de SRAG em crianças', desc: 'Alta de internações por SRAG.', doenca: 'SRAG', regiao: 'Salvador', inicio: '12/05 09:22', atualizado: '13/05 16:12', status: 'Ativo', score: 74.6, munic: 1 },
  { id: 'ALT-2025-00068', sev: 'MÉDIO', titulo: 'Suspeitas de Febre Amarela', desc: 'Notificações acima da média histórica.', doenca: 'Febre Amarela', regiao: 'Bom Jesus da Lapa, Seabra +2', inicio: '11/05 16:33', atualizado: '13/05 10:05', status: 'Em investigação', score: 55.3, munic: 3 },
  { id: 'ALT-2025-00067', sev: 'BAIXO', titulo: 'Vigilância de Malária', desc: 'Casos pontuais em áreas de risco.', doenca: 'Malária', regiao: 'Eunápolis', inicio: '11/05 08:11', atualizado: '12/05 14:20', status: 'Em monitoramento', score: 32.7, munic: 1 },
  { id: 'ALT-2025-00066', sev: 'MÉDIO', titulo: 'Aumento de casos de Diarreia', desc: 'Surtos localizados em comunidades.', doenca: 'Diarreia Aguda', regiao: 'Porto Seguro, Santa Cruz Cabrália', inicio: '10/05 14:45', atualizado: '12/05 09:32', status: 'Em investigação', score: 49.1, munic: 2 },
];

const STAT_CARDS = [
  { label: 'ALERTAS ATIVOS',   value: 73, sub: '+12 nas últimas 24h', color: '#f43f5e', icon: AlertTriangle },
  { label: 'MUITO ALTO RISCO', value: 18, sub: '+5 nas últimas 24h',  color: '#fb7185', icon: AlertTriangle },
  { label: 'EM INVESTIGAÇÃO',  value: 27, sub: '36,9% do total',       color: '#facc15', icon: Eye },
  { label: 'EM MONITORAMENTO', value: 28, sub: '38,4% do total',       color: '#38bdf8', icon: Bell },
];

const FACTORS = [
  ['NDVI (vegetação)', 'Muito alto', 'critico'],
  ['Precipitação (7 dias)', 'Alto', 'alto'],
  ['Temperatura da superfície', 'Alto', 'alto'],
  ['Densidade populacional', 'Muito alto', 'critico'],
  ['Mobilidade populacional', 'Médio', 'atencao'],
];

const RESPONSE = [
  'Intensificar bloqueio vetorial',
  'Aumentar testagem e triagem',
  'Mobilizar equipes de campo',
  'Campanhas de comunicação',
];

function StatSparkline({ color }) {
  return (
    <svg viewBox="0 0 90 28" width="90" height="22" preserveAspectRatio="none" style={{ marginTop: 6 }}>
      <polyline points="0,24 12,20 24,22 36,15 48,17 60,10 72,12 90,4" fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

export default function CentralDeAlertas() {
  const [selectedId, setSelectedId] = useState(ALERTS[0].id);
  const sel = ALERTS.find((a) => a.id === selectedId) || ALERTS[0];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 430px', gap: 16, alignItems: 'start' }}>
      {/* ── Coluna principal ── */}
      <div style={{ minWidth: 0 }}>
        {/* Stat cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 16 }}>
          {STAT_CARDS.map(({ label, value, sub, color, icon: Icon }) => (
            <div key={label} className="kpi-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <Icon size={15} style={{ color }} />
                <span className="kpi-label" style={{ margin: 0 }}>{label}</span>
              </div>
              <div className="kpi-value" style={{ fontSize: 30 }}>{value}</div>
              <StatSparkline color={color} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* Filtros */}
        <div className="card" style={{ padding: '14px 16px', marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            {[
              ['Severidade', 'Todas'],
              ['Doença / Indicador', 'Todas'],
              ['Região', 'Todas'],
            ].map(([label, val]) => (
              <div key={label} style={{ minWidth: 150 }}>
                <div className="filter-label">{label}</div>
                <select className="filter-select"><option>{val}</option></select>
              </div>
            ))}
            <div style={{ minWidth: 210 }}>
              <div className="filter-label">Período</div>
              <div className="filter-date-range">08/05/2025 — 14/05/2025</div>
            </div>
            <button type="button" className="btn btn-secondary btn-sm" style={{ height: 38 }}><Filter size={13} /> Mais filtros</button>
            <button type="button" className="btn btn-ghost btn-sm" style={{ height: 38, color: 'var(--text-muted)' }}>Limpar</button>
          </div>
        </div>

        {/* Lista */}
        <div className="card">
          <div className="card-header" style={{ paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>
            <h3>Lista de alertas ativos <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>({ALERTS.length})</span></h3>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ minWidth: 720 }}>
              <thead>
                <tr>
                  <th>Severidade</th><th>Alerta</th><th>Doença</th><th>Região / Municípios</th>
                  <th>Início</th><th>Atualizado</th><th>Status</th><th />
                </tr>
              </thead>
              <tbody>
                {ALERTS.map((a) => (
                  <tr key={a.id} className={a.id === selectedId ? 'selected' : ''} onClick={() => setSelectedId(a.id)}>
                    <td><span className={`risk-badge ${SEV[a.sev].cls}`}>{a.sev}</span></td>
                    <td style={{ maxWidth: 220 }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{a.titulo}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.desc}</div>
                    </td>
                    <td>{a.doenca}</td>
                    <td style={{ fontSize: 12 }}>{a.regiao}</td>
                    <td style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{a.inicio}</td>
                    <td style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{a.atualizado}</td>
                    <td>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600, color: STATUS[a.status] }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: STATUS[a.status] }} />{a.status}
                      </span>
                    </td>
                    <td><ChevronRight size={14} style={{ color: 'var(--text-muted)' }} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--text-muted)' }}>
            <span>Resultados por página: 20</span>
            <span style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              {['1', '2', '3', '4'].map((p) => (
                <span key={p} style={{ padding: '3px 9px', borderRadius: 6, background: p === '1' ? 'var(--blue)' : 'transparent', color: p === '1' ? '#fff' : 'var(--text-secondary)', fontWeight: 600 }}>{p}</span>
              ))}
            </span>
          </div>
        </div>
      </div>

      {/* ── Coluna de detalhe ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, position: 'sticky', top: 0 }}>
        {/* Ações */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary btn-sm"><Plus size={13} /> Criar alerta</button>
          <button type="button" className="btn btn-secondary btn-sm"><TrendingUp size={13} /> Escalonar</button>
          <button type="button" className="btn btn-secondary btn-sm"><Share2 size={13} /> Compartilhar</button>
          <button type="button" className="btn btn-secondary btn-sm"><FileText size={13} /> Relatório</button>
        </div>

        {/* Detalhe */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px 10px' }}>
            <span className="panel-title">Alerta selecionado</span>
            <X size={15} style={{ color: 'var(--text-muted)', cursor: 'pointer' }} />
          </div>

          <div style={{ padding: '0 18px 14px', borderBottom: '1px solid var(--border)' }}>
            <span className={`risk-badge ${SEV[sel.sev].cls}`}>{sel.sev}</span>
            <div style={{ fontSize: 17, fontWeight: 800, margin: '8px 0 2px' }}>{sel.titulo}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 5 }}>
              ID: {sel.id} <Copy size={11} />
            </div>
          </div>

          {/* Gauge + tendência */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--border)' }}>
            <div style={{ padding: '14px 18px', borderRight: '1px solid var(--border)' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Índice de risco (Dengue)</div>
              <Gauge score={sel.score} size={132} />
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Percentil nacional: {Math.round(sel.score * 1.09)}°</div>
            </div>
            <div style={{ padding: '14px 18px' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6 }}>Tendência (7 dias)</div>
              <div className="trend-value" style={{ fontSize: 28 }}><TrendingUp size={18} /> 28%</div>
              <div style={{ fontSize: 12, color: 'var(--risk-critico)', fontWeight: 600, marginTop: 2 }}>Crescente</div>
            </div>
          </div>

          {/* Meta */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, padding: '14px 18px', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
            {[
              ['Início', '14/05/2025 08:23'],
              ['Última atualização', '14/05/2025 10:42'],
              ['Status', sel.status],
              ['Municípios afetados', `${sel.munic} municípios`],
            ].map(([k, v]) => (
              <div key={k}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 2 }}>{k}</div>
                <div style={{ fontWeight: 700, color: k === 'Status' ? STATUS[sel.status] : 'var(--text-primary)' }}>{v}</div>
              </div>
            ))}
          </div>

          {/* Fatores + resposta */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: '1px solid var(--border)' }}>
            <div style={{ padding: '14px 18px', borderRight: '1px solid var(--border)' }}>
              <div className="territory-section-title">Principais fatores</div>
              {FACTORS.map(([f, lvl, cls]) => (
                <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '5px 0', fontSize: 12 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: SEV[lvl === 'Muito alto' ? 'MUITO ALTO' : lvl === 'Alto' ? 'ALTO' : 'MÉDIO'].color, flexShrink: 0 }} />
                  <span style={{ flex: 1, color: 'var(--text-secondary)' }}>{f}</span>
                  <span className={`risk-badge ${cls}`} style={{ fontSize: 9 }}>{lvl}</span>
                </div>
              ))}
            </div>
            <div style={{ padding: '14px 18px' }}>
              <div className="territory-section-title">Resposta recomendada</div>
              {RESPONSE.map((r) => (
                <div key={r} style={{ display: 'flex', gap: 7, padding: '5px 0', fontSize: 12, color: 'var(--text-secondary)' }}>
                  <ChevronRight size={13} style={{ color: 'var(--blue)', flexShrink: 0, marginTop: 1 }} />{r}
                </div>
              ))}
            </div>
          </div>

          {/* Mapa de calor */}
          <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
            <div className="territory-section-title">Mapa de calor · casos prováveis (7 dias)</div>
            <div style={{
              height: 120, borderRadius: 10, position: 'relative', overflow: 'hidden',
              border: '1px solid var(--border)',
              background: `radial-gradient(circle at 60% 45%, rgba(244,63,94,.85), transparent 30%),
                           radial-gradient(circle at 42% 60%, rgba(249,115,22,.7), transparent 28%),
                           radial-gradient(circle at 70% 65%, rgba(250,204,21,.55), transparent 32%),
                           radial-gradient(circle at 50% 40%, rgba(34,197,94,.4), transparent 55%),
                           #060a10`,
            }}>
              <span style={{ position: 'absolute', top: 30, left: '52%', width: 14, height: 14, borderRadius: '50%', background: '#fff', border: '2px solid #f43f5e', display: 'grid', placeItems: 'center', fontSize: 8, color: '#f43f5e', fontWeight: 800 }}>!</span>
              <span style={{ position: 'absolute', top: 64, left: '38%', width: 12, height: 12, borderRadius: '50%', background: '#fff', border: '2px solid #f97316' }} />
            </div>
          </div>

          {/* Timeline */}
          <div style={{ padding: '14px 18px' }}>
            <div className="territory-section-title">Linha do tempo (escalonamento)</div>
            {[
              ['14/05/2025 10:42', 'Alerta ativo', 'Sistema VECTRA', 'blue'],
              ['14/05/2025 09:10', 'Notificação enviada', 'Coordenação Municipal', 'done'],
              ['14/05/2025 08:23', 'Alerta criado', 'Sistema VECTRA', 'done'],
            ].map(([ts, label, sub, dot]) => (
              <div key={ts} className="audit-trail-item">
                <span className={`audit-trail-dot ${dot}`} />
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{ts}</div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>
                </div>
              </div>
            ))}
            <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: 6, padding: 0 }}>Ver histórico completo →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
