import { useState } from 'react';
import { Calendar, ChevronDown, Download, FileText, MessageSquareText, TrendingUp } from 'lucide-react';
import { riskColor, topByRisk } from '../data/brazilMunicipalities.js';

const TABS = ['Modo Executivo', 'Justificativas', 'Histórico'];

const METRICS = [
  {
    label: 'Pressão de surto',
    hint: 'Risco médio previsto para as próximas semanas',
    value: '0,87',
    delta: '+0,04',
    up: true,
    color: '#ef4444',
  },
  {
    label: 'Margem de erro',
    hint: 'Quanto menor, mais calibrado está o alerta',
    value: '0,12',
    delta: '-0,03',
    up: false,
    color: '#16a34a',
  },
  {
    label: 'Alertas confirmados',
    hint: 'Dos alertas emitidos, quantos se confirmaram',
    value: '81%',
    delta: '+5 p.p.',
    up: false,
    color: '#2563eb',
  },
  {
    label: 'Surtos detectados',
    hint: 'Dos surtos reais, quantos foram capturados a tempo',
    value: '76%',
    delta: '+4 p.p.',
    up: true,
    color: '#f97316',
  },
  {
    label: 'Confiabilidade do alerta',
    hint: 'Equilíbrio operacional entre acerto e sensibilidade',
    value: '0,78',
    delta: '+0,04',
    up: true,
    color: '#8b5cf6',
  },
  {
    label: 'Alertas gerados',
    hint: 'Total de alertas revisáveis no período',
    value: '892',
    delta: '+12%',
    up: true,
    color: '#ec4899',
  },
];

const EXECUTIVE_FACTORS = [
  ['Chuva acumulada acima do padrão', '+18%', '#dc2626'],
  ['Temperatura média favorável ao vetor', '+14%', '#ea580c'],
  ['Aumento recente de casos prováveis', '+11%', '#ca8a04'],
  ['Alta exposição populacional', '+7%', '#8b5cf6'],
];

const NLG_EXPLANATIONS = [
  {
    title: 'Chuva acumulada',
    text: 'A chuva dos últimos 7 dias explica cerca de 40% do sinal de alerta porque aumenta a chance de criadouros ativos nas áreas urbanas monitoradas.',
  },
  {
    title: 'Casos recentes',
    text: 'O crescimento de casos na semana anterior elevou a prioridade operacional: o alerta não depende só do clima, mas também da aceleração epidemiológica.',
  },
  {
    title: 'Capacidade da rede',
    text: 'A ocupação de leitos e a disponibilidade de equipes reduzem a margem de resposta. Municípios com rede pressionada sobem no ranking de atendimento.',
  },
];

function MiniLineChart({ color = '#ef4444', up = true }) {
  const pts = up
    ? '0,25 15,22 30,20 45,16 60,14 75,10 90,8 105,4'
    : '0,8 15,11 30,14 45,12 60,16 75,18 90,22 105,24';
  return (
    <svg viewBox="0 0 105 30" width="105" height="30" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  );
}

export default function Relatorios() {
  const [activeTab, setActiveTab] = useState('Modo Executivo');
  const top5 = topByRisk(5);

  const riskDist = [
    { label: 'Muito alto', pct: 23, n: 146, color: '#dc2626' },
    { label: 'Alto', pct: 25, n: 156, color: '#ea580c' },
    { label: 'Moderado', pct: 27, n: 168, color: '#ca8a04' },
    { label: 'Baixo', pct: 13, n: 81, color: '#16a34a' },
    { label: 'Muito baixo', pct: 13, n: 81, color: '#4ade80' },
  ];

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Período</div>
          <button type="button" className="btn btn-secondary btn-sm">
            <Calendar size={12} /> Últimas 4 semanas <ChevronDown size={11} />
          </button>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="btn btn-secondary">
            <Download size={14} /> Exportar <ChevronDown size={12} />
          </button>
          <button type="button" className="btn btn-primary">
            <FileText size={14} /> Gerar relatório
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border)', marginBottom: 20 }}>
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '9px 18px',
              fontSize: 13,
              fontWeight: activeTab === tab ? 700 : 500,
              color: activeTab === tab ? 'var(--blue)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--blue)' : '2px solid transparent',
              marginBottom: -1,
              background: 'none',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="analytics-grid-top">
        {METRICS.map(({ label, hint, value, delta, up, color }) => (
          <div key={label} className="analytics-kpi" title={hint}>
            <div className="label">{label}</div>
            <div className="value" style={{ color }}>{value}</div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.3, marginBottom: 4, minHeight: 26 }}>{hint}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
              <MiniLineChart color={color} up={up} />
            </div>
            <div className={`delta ${up ? 'up' : 'down'}`}>
              {up ? '↑' : '↓'} {delta} <span style={{ fontWeight: 400, fontSize: 11, color: 'var(--text-muted)' }}>vs. período anterior</span>
            </div>
          </div>
        ))}
      </div>

      <div className="analytics-main-grid">
        <div className="card">
          <div className="card-header"><h3>Por que o risco aumentou?</h3></div>
          <div className="card-body">
            <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: 14 }}>
              O aumento do risco combina sinais epidemiológicos, clima favorável ao vetor e capacidade operacional pressionada.
            </p>
            {EXECUTIVE_FACTORS.map(([label, val, color]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <TrendingUp size={13} style={{ color }} />
                  <span>{label}</span>
                </div>
                <span style={{ fontWeight: 700, color }}>{val}</span>
              </div>
            ))}
            <button type="button" className="btn btn-ghost" style={{ marginTop: 12, padding: 0, fontSize: 12 }}>Ver análise completa →</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h3>Regiões com maior atenção</h3>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Ranking por risco previsto</p>
            </div>
          </div>
          <div className="card-body">
            {top5.map((m, i) => (
              <div key={m.geocode} className="ranking-row">
                <span className="rank-num">{i + 1}</span>
                <span className="rank-name">{m.municipio} ({m.uf})</span>
                <span className="rank-bar-wrap" style={{ flex: 1, maxWidth: 120 }}>
                  <div className="rank-bar" style={{ width: `${m.environmental_risk_score}%`, background: riskColor(m.environmental_risk_score), height: 6, borderRadius: 3 }} />
                </span>
                <span className={`rank-score ${m.environmental_risk_score >= 85 ? 'score-red' : m.environmental_risk_score >= 70 ? 'score-orange' : 'score-yellow'}`}>
                  {(m.environmental_risk_score / 10).toFixed(1)}
                </span>
              </div>
            ))}
            <button type="button" className="btn btn-ghost" style={{ marginTop: 12, padding: 0, fontSize: 12 }}>Ver todas as regiões →</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <h3>Distribuição do risco</h3>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Porcentagem de risco previsto</p>
            </div>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ position: 'relative', width: 80, height: 80, flexShrink: 0 }}>
                <svg viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                  {riskDist.reduce((acc, { pct, color }, i) => {
                    const prev = acc.offset;
                    acc.elements.push(
                      <circle key={i} cx="18" cy="18" r="15.9" fill="none" stroke={color}
                        strokeWidth="3" strokeDasharray={`${pct} ${100 - pct}`} strokeDashoffset={-prev}
                        strokeLinecap="butt" />
                    );
                    acc.offset += pct;
                    return acc;
                  }, { elements: [], offset: 0 }).elements}
                </svg>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 800 }}>625</div>
                  <div style={{ fontSize: 8, color: 'var(--text-muted)' }}>regiões</div>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                {riskDist.map(({ label, pct, n, color }) => (
                  <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5, fontSize: 11 }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                    <span style={{ flex: 1, color: 'var(--text-secondary)' }}>{label}</span>
                    <span style={{ fontWeight: 600 }}>{pct}%</span>
                    <span style={{ color: 'var(--text-muted)' }}>({n})</span>
                  </div>
                ))}
              </div>
            </div>
            <button type="button" className="btn btn-ghost" style={{ marginTop: 12, padding: 0, fontSize: 12 }}>Ver distribuição completa →</button>
          </div>
        </div>
      </div>

      <div style={{ marginTop: 20 }}>
        <div style={{ fontWeight: 800, fontSize: 18, marginBottom: 4 }}>Explicação para gestores</div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
          Resumo gerado em linguagem natural a partir das variáveis usadas pelo modelo.
        </div>

        <div className="analytics-main-grid">
          {NLG_EXPLANATIONS.map(({ title, text }) => (
            <div key={title} className="card">
              <div className="card-body">
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <div style={{ width: 34, height: 34, borderRadius: 10, background: 'var(--blue-light)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                    <MessageSquareText size={17} style={{ color: 'var(--blue)' }} />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 6 }}>{title}</div>
                    <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)' }}>{text}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 24 }}>
        © 2025 Vectra. Todos os direitos reservados. • Versão 2.4.1
      </div>
    </>
  );
}
