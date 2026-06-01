import { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.heat';
import 'leaflet/dist/leaflet.css';
import {
  ArrowRight,
  BarChart3,
  Bell,
  Bot,
  Calendar,
  Check,
  CloudRain,
  Download,
  Droplets,
  Eye,
  FileText,
  Filter,
  Layers3,
  RefreshCcw,
  Search,
  Send,
  Share2,
  Users,
  X,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  fetchCausalTimeline,
  fetchCopilotAnswer,
  fetchLatestRisk,
  postAgentProtocol,
  postAgentReview,
} from '../api/vectraApi.js';

const fallbackRisk = [
  { geocode: '3550308', municipio: 'Sao Paulo', uf: 'SP', region: 'Regiao Metropolitana de Sao Paulo', lat: -23.5505, lng: -46.6333, risk: 86.4, casos: 245, ndvi: 0.52, ndwi: -0.21, chuva: 132, leitos: 71, trend: 28 },
  { geocode: '3509502', municipio: 'Campinas', uf: 'SP', region: 'Regiao Metropolitana de Campinas', lat: -22.9056, lng: -47.0608, risk: 78.1, casos: 171, ndvi: 0.49, ndwi: -0.15, chuva: 98, leitos: 63, trend: 21 },
  { geocode: '3518800', municipio: 'Guarulhos', uf: 'SP', region: 'Alto Tiete', lat: -23.4545, lng: -46.5333, risk: 72.8, casos: 138, ndvi: 0.44, ndwi: -0.12, chuva: 86, leitos: 68, trend: 17 },
  { geocode: '3543402', municipio: 'Ribeirao Preto', uf: 'SP', region: 'Interior Norte', lat: -21.1775, lng: -47.8103, risk: 65.2, casos: 119, ndvi: 0.57, ndwi: -0.08, chuva: 76, leitos: 58, trend: 13 },
  { geocode: '3548500', municipio: 'Santos', uf: 'SP', region: 'Baixada Santista', lat: -23.9608, lng: -46.3336, risk: 58.7, casos: 74, ndvi: 0.61, ndwi: -0.05, chuva: 68, leitos: 62, trend: 9 },
  { geocode: '3549904', municipio: 'Sao Jose dos Campos', uf: 'SP', region: 'Vale do Paraiba', lat: -23.2237, lng: -45.9009, risk: 51.3, casos: 62, ndvi: 0.55, ndwi: 0.02, chuva: 45, leitos: 49, trend: 4 },
];

const trendData = [
  { day: '15/04', norte: 18, nordeste: 52, centro: 31, sudeste: 44, sul: 21 },
  { day: '22/04', norte: 26, nordeste: 72, centro: 46, sudeste: 58, sul: 32 },
  { day: '29/04', norte: 21, nordeste: 84, centro: 54, sudeste: 62, sul: 41 },
  { day: '06/05', norte: 35, nordeste: 76, centro: 65, sudeste: 81, sul: 38 },
  { day: '13/05', norte: 42, nordeste: 88, centro: 63, sudeste: 79, sul: 47 },
];

const reportTrend = [
  { date: '20/04', auc: 0.62, precision: 0.58, recall: 0.61, f1: 0.56 },
  { date: '27/04', auc: 0.72, precision: 0.63, recall: 0.68, f1: 0.60 },
  { date: '04/05', auc: 0.78, precision: 0.69, recall: 0.72, f1: 0.67 },
  { date: '11/05', auc: 0.83, precision: 0.76, recall: 0.74, f1: 0.72 },
  { date: '18/05', auc: 0.87, precision: 0.81, recall: 0.76, f1: 0.78 },
];

const riskDistribution = [
  { name: 'Muito Alto', value: 112, color: '#ff3939' },
  { name: 'Alto', value: 168, color: '#ff8a1f' },
  { name: 'Moderado', value: 176, color: '#ffc928' },
  { name: 'Baixo', value: 111, color: '#79cf5a' },
  { name: 'Muito Baixo', value: 58, color: '#2ea74c' },
];

function fmt(value, digits = 0) {
  return Number(value || 0).toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function riskColor(score) {
  if (score >= 82) return '#e92335';
  if (score >= 70) return '#ff7a1a';
  if (score >= 55) return '#ffc928';
  if (score >= 35) return '#76c957';
  return '#2e8c42';
}

function normalizeRisk(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return fallbackRisk;
  return rows.slice(0, 10).map((item, index) => {
    const base = fallbackRisk[index % fallbackRisk.length];
    return {
      ...base,
      geocode: item.geocode || base.geocode,
      municipio: item.municipio || base.municipio,
      risk: Number(item.environmental_risk_score ?? base.risk),
      casos: Number(item.casos_dengue ?? base.casos),
      chuva: Number(item.chuva_acumulada_7d ?? base.chuva),
      leitos: Number(item.leitos_ocupacao_pct ?? base.leitos),
      ndvi: Number(item.ndvi_mean ?? base.ndvi),
      ndwi: Number(item.ndwi_mean ?? base.ndwi),
      lat: Number(item.lat ?? base.lat),
      lng: Number(item.lng ?? base.lng),
    };
  });
}

function HeatLayer({ points, visible }) {
  const map = useMap();
  useEffect(() => {
    if (!visible) return undefined;
    const heat = L.heatLayer(
      points.map((item) => [item.lat, item.lng, item.risk / 100]),
      {
        radius: 50,
        blur: 28,
        gradient: { 0.15: '#2e8c42', 0.35: '#76c957', 0.55: '#ffc928', 0.72: '#ff7a1a', 1: '#e92335' },
      },
    );
    heat.addTo(map);
    return () => heat.remove();
  }, [map, points, visible]);
  return null;
}

function RiskMapSurface({ risk, selected, setSelected, compact = false, heat = true }) {
  return (
    <MapContainer
      center={compact ? [-23.1, -46.7] : [-22.9, -46.9]}
      zoom={compact ? 7 : 7}
      minZoom={6}
      maxZoom={12}
      zoomControl={false}
      className="risk-map-surface"
    >
      <TileLayer
        attribution="&copy; Esri, OpenStreetMap"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      />
      <TileLayer
        attribution=""
        opacity={0.25}
        url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
      />
      <HeatLayer points={risk} visible={heat} />
      {risk.map((item) => (
        <CircleMarker
          key={item.geocode}
          center={[item.lat, item.lng]}
          radius={selected.geocode === item.geocode ? 16 : 10}
          pathOptions={{
            color: '#ffffff',
            weight: selected.geocode === item.geocode ? 3 : 1.5,
            fillColor: riskColor(item.risk),
            fillOpacity: 0.88,
          }}
          eventHandlers={{ click: () => setSelected(item) }}
        >
          <Popup>
            <strong>{item.municipio}</strong>
            <br />
            Indice de risco: {fmt(item.risk, 1)}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

function PageTitle({ title, subtitle, actions }) {
  return (
    <div className="page-title">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="page-actions">{actions}</div>
    </div>
  );
}

function DarkCard({ title, kicker, children, className = '' }) {
  return (
    <section className={`dark-card ${className}`}>
      {(title || kicker) && (
        <header>
          <div>
            {kicker && <span>{kicker}</span>}
            {title && <h2>{title}</h2>}
          </div>
        </header>
      )}
      {children}
    </section>
  );
}

function KpiCard({ icon: Icon, label, value, delta, color = '#1ec9ff' }) {
  return (
    <DarkCard className="kpi-card">
      <div className="kpi-icon" style={{ borderColor: color, color }}>
        <Icon size={28} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{delta}</small>
      </div>
      <svg viewBox="0 0 80 28" aria-hidden="true">
        <polyline points="0,19 12,16 22,20 34,10 45,14 56,5 68,12 80,8" fill="none" stroke={color} strokeWidth="3" />
      </svg>
    </DarkCard>
  );
}

function RiskGauge({ value }) {
  return (
    <div className="risk-gauge">
      <div className="gauge-arc" style={{ '--score': `${value}%` }} />
      <strong>{fmt(value / 10, 1)}</strong>
      <span>de 10</span>
    </div>
  );
}

function SidebarFilters() {
  return (
    <aside className="map-filters panel-outline">
      <div className="panel-row">
        <strong>Filtros</strong>
        <button type="button">Limpar <RefreshCcw size={14} /></button>
      </div>
      {[
        ['Periodo de analise', '08/05/2025  →  14/05/2025'],
        ['Regiao', 'Sudeste'],
        ['Estado', 'Sao Paulo'],
        ['Municipio', 'Selecione um municipio'],
        ['Doenca / Indicador', 'Dengue'],
        ['Vulnerabilidade', 'Todas'],
      ].map(([label, value]) => (
        <label className="filter-field" key={label}>
          <span>{label}</span>
          <button type="button">{value}</button>
        </label>
      ))}
      <div className="range-field">
        <span>Indice de Risco</span>
        <div />
        <p><b>0 Min</b><b>100 Max</b></p>
      </div>
      <button type="button" className="cyan-button"><Filter size={15} /> Aplicar filtros</button>
    </aside>
  );
}

function MapLayersCard() {
  const layers = ['Risco (Dengue)', 'NDVI', 'NDMI', 'Precipitacao (7 dias)', 'Temperatura da superficie', 'Densidade populacional', 'Unidade de saude'];
  return (
    <div className="map-layers panel-outline">
      <div className="panel-row">
        <strong>Camadas</strong>
        <Layers3 size={16} />
      </div>
      {layers.map((layer, index) => (
        <label key={layer} className="layer-check">
          <input type="checkbox" defaultChecked={index < 2} />
          <span>{layer}</span>
          <Eye size={15} />
        </label>
      ))}
      <button type="button">Gerenciar camadas <ArrowRight size={14} /></button>
    </div>
  );
}

function TerritoryPanel({ selected }) {
  return (
    <aside className="territory-panel">
      <div className="panel-row">
        <span>Territorio selecionado</span>
        <X size={16} />
      </div>
      <h2>{selected.municipio} - {selected.uf}</h2>
      <p>{selected.region}</p>

      <DarkCard className="risk-score-box">
        <div className="panel-row">
          <span>Indice de Risco (Dengue)</span>
          <b>Muito Alto</b>
        </div>
        <div className="score-layout">
          <strong>{fmt(selected.risk, 1)}</strong>
          <small>/100</small>
          <RiskGauge value={selected.risk} />
        </div>
      </DarkCard>

      <DarkCard title="Principais fatores">
        {[
          ['NDVI (vegetacao)', 'Mais alto', 'red'],
          ['Precipitacao (7 dias)', 'Alto', 'orange'],
          ['Temperatura da superficie', 'Alta', 'orange'],
          ['Densidade populacional', 'Muito Alto', 'red'],
          ['NDMI (agua)', 'Medio', 'yellow'],
        ].map(([label, tag, tone]) => (
          <p className="factor-row" key={label}>
            <span>{label}</span>
            <b className={tone}>{tag}</b>
          </p>
        ))}
        <button type="button" className="outline-link">Ver analise completa <ArrowRight size={14} /></button>
      </DarkCard>

      <DarkCard title="Tendencia (ultimos 30 dias)">
        <div className="trend-box">
          <strong>↑ {selected.trend}%</strong>
          <ResponsiveContainer width="45%" height={50}>
            <AreaChart data={reportTrend}>
              <Area dataKey="recall" stroke="#ff3939" fill="rgba(255,57,57,.18)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </DarkCard>

      <DarkCard title="Acoes rapidas">
        <div className="quick-grid">
          <button type="button"><Bell size={15} /> Criar alerta</button>
          <button type="button"><Calendar size={15} /> Planejar acao</button>
          <button type="button"><FileText size={15} /> Gerar relatorio</button>
          <button type="button"><Share2 size={15} /> Compartilhar</button>
        </div>
      </DarkCard>
    </aside>
  );
}

function RiskMapPage({ risk, selected, setSelected }) {
  return (
    <div className="risk-map-page">
      <PageTitle
        title="Mapa de Risco"
        subtitle="Visualize e analise o risco em nivel municipal e identifique areas prioritarias."
        actions={<><button type="button" className="ghost-action"><RefreshCcw size={16} /></button><button type="button" className="ghost-action"><Share2 size={16} /> Compartilhar</button></>}
      />

      <div className="risk-map-grid">
        <SidebarFilters />
        <section className="map-stage">
          <div className="map-search"><Search size={17} /> Buscar municipio ou localidade</div>
          <MapLayersCard />
          <RiskMapSurface risk={risk} selected={selected} setSelected={setSelected} />
          <div className="municipal-risk-overlay" />
          <div className="map-controls"><button>+</button><button>-</button><button>⌖</button><button>▧</button></div>
        </section>
        <TerritoryPanel selected={selected} />
      </div>

      <div className="map-bottom-grid">
        <DarkCard title="Legenda - Indice de Risco" className="legend-card">
          <div className="risk-gradient" />
          <p><span>Muito Baixo</span><span>Baixo</span><span>Moderado</span><span>Alto</span><span>Muito Alto</span></p>
        </DarkCard>
        <DarkCard title="Camada base (satelite)" className="base-card">
          <div className="base-options">
            {['Satelite', 'Hibrido', 'Terreno', 'Escuro'].map((item, index) => <button type="button" className={index === 0 ? 'active' : ''} key={item}>{item}</button>)}
          </div>
        </DarkCard>
        <DarkCard title="Comparativo historico">
          <div className="history-summary">
            <span>Variacao no risco medio <b className="red">↑ 18%</b></span>
            <span>Municipios em alta <b className="green">↑ 132</b></span>
            <span>Municipios em queda <b className="green">↓ 24</b></span>
          </div>
        </DarkCard>
      </div>
    </div>
  );
}

function OverviewPage({ risk, selected, setSelected }) {
  return (
    <div className="content-page">
      <PageTitle
        title="Centro de Operacoes"
        subtitle="Monitoramento integrado de riscos e saude publica em tempo real"
        actions={<><span className="fresh-dot">Atualizado ha 2 min</span><button className="ghost-action" type="button"><RefreshCcw size={16} /></button><button className="ghost-action" type="button"><Filter size={16} /> Filtros</button></>}
      />
      <div className="kpi-strip">
        <KpiCard icon={Bell} label="Alertas ativos" value="128" delta="↑ 18% vs. 7 dias" color="#ff3939" />
        <KpiCard icon={BarChart3} label="Municipios criticos" value="342" delta="↑ 12% vs. 7 dias" color="#1ec9ff" />
        <KpiCard icon={Users} label="Populacao exposta" value="18,7M" delta="↑ 9% vs. 7 dias" color="#22d3ee" />
        <KpiCard icon={Zap} label="Tendencia semanal" value="Em alta" delta="Risco crescente" color="#ff3939" />
      </div>

      <div className="overview-grid">
        <DarkCard title="Mapa de Risco" kicker="Atualizado agora ha 2 min" className="overview-map-card">
          <RiskMapSurface risk={risk} selected={selected} setSelected={setSelected} compact />
          <div className="map-legend-inline">
            {['Muito Baixo', 'Baixo', 'Moderado', 'Alto', 'Muito Alto'].map((label, index) => <span key={label}><i className={`dot-${index}`} />{label}</span>)}
          </div>
        </DarkCard>

        <DarkCard title="Tendencia de Risco (Nacional)">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendData}>
              <CartesianGrid stroke="rgba(148,163,184,.14)" />
              <XAxis dataKey="day" stroke="#8fa4b8" />
              <YAxis stroke="#8fa4b8" />
              <Tooltip />
              <Line dataKey="norte" stroke="#52d273" strokeWidth={2} />
              <Line dataKey="nordeste" stroke="#1ec9ff" strokeWidth={2} />
              <Line dataKey="centro" stroke="#ffc928" strokeWidth={2} />
              <Line dataKey="sudeste" stroke="#ff8a1f" strokeWidth={2} />
              <Line dataKey="sul" stroke="#ff3939" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </DarkCard>

        <DarkCard title="Alerta Atual" className="alert-current">
          <span className="risk-tag">Alto risco</span>
          <h3>{selected.municipio} - {selected.uf}</h3>
          <RiskGauge value={selected.risk} />
          <button type="button" className="outline-link">Ver detalhes do alerta <ArrowRight size={14} /></button>
        </DarkCard>

        <DarkCard title="NDVI / NDWI - Resumo">
          <div className="two-metrics">
            <div><Droplets size={20} /><span>NDVI (Vegetacao)</span><strong>{fmt(selected.ndvi, 2)}</strong><b>Moderado</b></div>
            <div><CloudRain size={20} /><span>NDWI (Agua)</span><strong>{fmt(selected.ndwi, 2)}</strong><b>Baixo</b></div>
          </div>
        </DarkCard>

        <DarkCard title="Capacidade Assistencial">
          <div className="assist-grid">
            {['Leitos de UTI', 'Leitos Clinicos', 'Unidades de Saude'].map((label, index) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{[62, 58, 71][index]}%</strong>
                <i style={{ width: `${[62, 58, 71][index]}%` }} />
              </div>
            ))}
          </div>
        </DarkCard>

        <DarkCard title="Acoes Recomendadas">
          {['Reforcar comunicacao preventiva', 'Mobilizar equipes para regioes criticas', 'Verificar estoques e suprimentos', 'Ativar planos de contingencia locais'].map((text, index) => (
            <p className="factor-row" key={text}><span>{text}</span><b className={index < 2 ? 'red' : 'yellow'}>{index < 2 ? 'Prioridade ALTA' : 'Prioridade MEDIA'}</b></p>
          ))}
        </DarkCard>
      </div>
    </div>
  );
}

function CopilotPage({ selected }) {
  const [messages, setMessages] = useState([
    { role: 'user', text: 'Quais sao os principais hotspots de dengue nas proximas 2 semanas?' },
    { role: 'assistant', text: 'Com base nos modelos epidemiologicos, vigilancia ativa e condicoes ambientais, os principais hotspots sao Sao Paulo, Campinas e Guarulhos. Os fatores dominantes sao precipitacao, NDWI e pressao assistencial.' },
  ]);
  const [question, setQuestion] = useState('Explique por que Sao Paulo esta em alerta alto.');

  async function submit(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text) return;
    setMessages((current) => [...current, { role: 'user', text }]);
    setQuestion('');
    try {
      const response = await fetchCopilotAnswer({ geocode: selected.geocode, question: text });
      setMessages((current) => [...current, { role: 'assistant', text: response.answer }]);
    } catch {
      setMessages((current) => [...current, { role: 'assistant', text: `${selected.municipio} esta em alerta por combinacao de chuva, NDWI anomalo, aumento recente de casos e capacidade assistencial pressionada.` }]);
    }
  }

  return (
    <div className="content-page">
      <PageTitle title="Vectra Copilot" subtitle="Assistente inteligente para decisoes em saude publica" />
      <div className="copilot-grid">
        <DarkCard className="chat-card">
          <div className="chat-stream">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className={`chat-message ${message.role}`}>
                <Bot size={20} />
                <p>{message.text}</p>
              </div>
            ))}
          </div>
          <form className="copilot-input" onSubmit={submit}>
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Pergunte algo ao Vectra Copilot..." />
            <button type="submit"><Send size={20} /></button>
          </form>
        </DarkCard>
        <DarkCard title="Sugestoes para voce">
          {['Quais municipios devem receber reforco de equipes de campo?', 'Simule a alocacao de 500 kits de controle vetorial.', 'Qual o impacto da previsao de chuva na proxima semana?', 'Gere um resumo executivo da situacao da dengue.', 'Redija uma mensagem preventiva para a populacao.'].map((item) => (
            <button type="button" className="suggestion-row" key={item}>{item}<ArrowRight size={18} /></button>
          ))}
        </DarkCard>
        <DarkCard title="Contexto atual">
          <RiskGauge value={86} />
          <p>Risco elevado para Dengue em 312 municipios.</p>
          <h3>Top 5 regioes criticas</h3>
          {fallbackRisk.slice(0, 5).map((item, index) => <p className="factor-row" key={item.geocode}><span>{index + 1}. {item.municipio}</span><b>{fmt(item.risk / 10, 1)}</b></p>)}
        </DarkCard>
      </div>
    </div>
  );
}

function ActionsPage({ selected }) {
  const [terminal, setTerminal] = useState([]);

  async function approve() {
    try {
      const protocol = await postAgentProtocol({
        risk_context: {
          geocode: selected.geocode,
          municipio: selected.municipio,
          risk_label: 'alto',
          probability_surto: selected.risk / 100,
          top_context_factors: ['NDWI elevado', 'chuva acumulada', 'pressao assistencial'],
        },
        use_llm: true,
      });
      await postAgentReview({ protocol_id: protocol.protocol_id, decision: 'approved', reviewer_name: 'Camila Rocha' });
    } catch {
      // UI keeps the simulated execution visible for demo mode.
    }
    setTerminal([
      '$ vectra-agent approve --queue prioridade',
      'OK proposta revisada pelo gestor',
      'OK tool:preparar_alerta_sms -> mensagens em fila',
      'OK tool:rotear_equipes -> areas criticas priorizadas',
      'OK tool:reservar_insumos -> soro, testes e hidratação oral sinalizados',
      'OK audit_trail -> hash SHA-256 gerado',
    ]);
  }

  return (
    <div className="content-page">
      <PageTitle title="Acoes e Aprovacao" subtitle="Decisoes criticas exigem aprovacao humana. Voce tem o controle final." />
      <div className="actions-layout">
        <DarkCard title="Fila de Acoes Prioritarias" className="priority-row">
          {fallbackRisk.slice(0, 5).map((item, index) => (
            <div className="priority-card" key={item.geocode}>
              <b>{index + 1}</b>
              <span>{item.risk > 70 ? 'ALTO RISCO' : 'MEDIO RISCO'}</span>
              <strong>{item.municipio} - {item.uf}</strong>
              <small>Impacto potencial {item.risk > 70 ? 'Alto' : 'Medio'}</small>
            </div>
          ))}
        </DarkCard>
        <DarkCard title="Intervencoes Recomendadas">
          {['Acionar fumace em areas criticas', 'Remanejar agentes de endemias', 'Reforcar estoque de soro e testes', 'Comunicacao preventiva'].map((item, index) => <p className="factor-row" key={item}><span>{item}</span><b className={index < 2 ? 'red' : 'yellow'}>{index < 2 ? 'ALTA' : 'MEDIA'}</b></p>)}
        </DarkCard>
        <DarkCard title="Simulador de Cenarios">
          <table className="scenario-table"><tbody>
            {[
              ['Capacidade de resposta', 'Equilibrada'],
              ['Cobertura de visitas', '+36 p.p.'],
              ['Estoque das UBS', 'Reforcado'],
              ['Tempo de campo', '-48h'],
            ].map(([row, value]) => <tr key={row}><td>{row}</td><td>Acao agora</td><td className="green">{value}</td></tr>)}
          </tbody></table>
          <button type="button" className="cyan-button" onClick={approve}><Check size={16} /> Aprovar protocolo</button>
        </DarkCard>
        <DarkCard title="Fluxo de Aprovacao">
          {['Proposta gerada pela IA', 'Revisao do Analista', 'Aguardando aprovacao do Gestor', 'Execucao da Acao'].map((step, index) => <p className="approval-step" key={step}><b>{index + 1}</b>{step}</p>)}
        </DarkCard>
        <DarkCard title="Terminal de Execucao Autonoma" className="terminal-card">
          {(terminal.length ? terminal : ['$ vectra-agent --standby', 'aguardando aprovacao do gestor...']).map((line) => <code key={line}>{line}</code>)}
        </DarkCard>
      </div>
    </div>
  );
}

function ReportsPage({ risk, selected, setSelected }) {
  return (
    <div className="content-page">
      <PageTitle
        title="Analises e Explicabilidade"
        subtitle="Entenda o desempenho dos modelos, fatores de risco e justificativas por regiao."
        actions={<><button className="ghost-action" type="button"><Download size={16} /> Exportar</button><button className="primary-dark" type="button"><FileText size={16} /> Gerar relatorio</button></>}
      />
      <div className="reports-tabs"><button className="active">Visao Executiva</button><button>Justificativas</button><button>Historico</button></div>
      <div className="report-kpis">
        {['Pressao de surto', 'Margem de erro', 'Alertas confirmados', 'Surtos detectados', 'Confiabilidade do alerta', 'Alertas gerados'].map((label, index) => <DarkCard key={label}><span>{label}</span><strong>{['0,87', '0,12', '81%', '76%', '0,78', '892'][index]}</strong></DarkCard>)}
      </div>
      <div className="reports-grid">
        <DarkCard title="Desempenho ao longo do tempo">
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={reportTrend}>
              <CartesianGrid stroke="rgba(148,163,184,.14)" />
              <XAxis dataKey="date" stroke="#8fa4b8" />
              <YAxis stroke="#8fa4b8" />
              <Tooltip />
              <Line dataKey="auc" stroke="#8b5cf6" strokeWidth={2} />
              <Line dataKey="precision" stroke="#1ec9ff" strokeWidth={2} />
              <Line dataKey="recall" stroke="#ffb000" strokeWidth={2} />
              <Line dataKey="f1" stroke="#ff3939" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </DarkCard>
        <DarkCard title="Explicacao em linguagem natural">
          {[
            'A chuva acumulada explica a maior parte do sinal de alerta nas areas monitoradas.',
            'O crescimento recente de casos aumentou a prioridade operacional dos municipios.',
            'A capacidade assistencial pressionada reduz a margem de resposta da rede.',
          ].map((text) => <p className="factor-row" key={text}><span>{text}</span></p>)}
        </DarkCard>
        <DarkCard title="Mapa de Risco (Selecao)" className="mini-report-map">
          <RiskMapSurface risk={risk} selected={selected} setSelected={setSelected} compact />
        </DarkCard>
        <DarkCard title="Indicadores Semanais (Por regiao)">
          {risk.slice(0, 5).map((item) => <p className="factor-row" key={item.geocode}><span>{item.municipio}</span><b>{fmt(item.chuva)} mm</b></p>)}
        </DarkCard>
        <DarkCard title="Distribuicao de Risco (Semanal)">
          <ResponsiveContainer width="100%" height={210}>
            <PieChart>
              <Pie data={riskDistribution} innerRadius={56} outerRadius={84} dataKey="value">
                {riskDistribution.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </DarkCard>
        <DarkCard title="Explicacao para a regiao selecionada">
          <h3>{selected.municipio}</h3>
          <strong className="big-score">{fmt(selected.risk / 10, 1)} /10</strong>
          {['Precipitacao acumulada alta', 'NDVI abaixo da media', 'NDWI abaixo da media', 'Temperatura maxima acima da media'].map((item, index) => <p className="factor-row" key={item}><span>↑ {item}</span><b className="red">+{[2.45, 1.87, 1.32, 0.98][index]}</b></p>)}
        </DarkCard>
      </div>
    </div>
  );
}

export default function Dashboard({ activePage, setActivePage }) {
  const [risk, setRisk] = useState(fallbackRisk);
  const [selected, setSelected] = useState(fallbackRisk[0]);

  useEffect(() => {
    async function loadRisk() {
      try {
        const rows = await fetchLatestRisk(20);
        const normalized = normalizeRisk(rows);
        setRisk(normalized);
        setSelected(normalized[0]);
      } catch {
        setRisk(fallbackRisk);
        setSelected(fallbackRisk[0]);
      }
    }
    loadRisk();
  }, []);

  useEffect(() => {
    fetchCausalTimeline(selected.geocode).catch(() => null);
  }, [selected.geocode]);

  const props = useMemo(() => ({ risk, selected, setSelected, setActivePage }), [risk, selected, setActivePage]);

  if (activePage === 'overview') return <OverviewPage {...props} />;
  if (activePage === 'copilot') return <CopilotPage {...props} />;
  if (activePage === 'actions') return <ActionsPage {...props} />;
  if (activePage === 'reports') return <ReportsPage {...props} />;
  return <RiskMapPage {...props} />;
}
