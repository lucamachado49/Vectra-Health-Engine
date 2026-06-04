import { useEffect, useMemo, useState } from 'react';
import { GeoJSON, MapContainer, Marker, ZoomControl, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import HeatGlow from '../components/HeatGlow.jsx';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  AlertTriangle, ArrowUpRight, Bot, Building2, ChevronRight,
  Send, ShieldCheck,
} from 'lucide-react';
import { BRAZIL_MUNICIPALITIES } from '../data/brazilMunicipalities.js';
import { loadAllMunicipalities, riskGradient, riskHeatPoints } from '../data/geoLoader.js';
import { fetchLatestRisk } from '../api/vectraApi.js';
import Gauge from '../components/Gauge.jsx';

/* Enquadra o mapa no Brasil inteiro */
function FitBrazil({ geo }) {
  const map = useMap();
  useEffect(() => {
    if (!geo) return;
    try {
      map.fitBounds(L.geoJSON(geo).getBounds(), { padding: [10, 10] });
    } catch { /* noop */ }
  }, [geo, map]);
  return null;
}

/* Rótulos flutuantes (regiões + oceano) */
const REGION_LABELS = [
  ['NORTE', -3.2, -62.5, ''],
  ['NORDESTE', -8.6, -40.0, ''],
  ['CENTRO-OESTE', -15.6, -55.8, ''],
  ['SUDESTE', -20.6, -45.0, ''],
  ['SUL', -28.2, -52.5, ''],
  ['Oceano Atlântico', -17.5, -33.5, 'ocean'],
];
function labelIcon(text, kind) {
  return L.divIcon({
    html: `<span class="map-label ${kind}">${text}</span>`,
    className: 'map-label-icon',
    iconSize: [150, 22],
    iconAnchor: [75, 11],
  });
}

/* Capitais (rótulo com ponto) */
const CAPITALS = [
  ['Manaus', -3.10, -60.02], ['Belém', -1.46, -48.50], ['Fortaleza', -3.73, -38.52],
  ['Recife', -8.05, -34.88], ['Salvador', -12.97, -38.50], ['Brasília', -15.79, -47.88],
  ['Cuiabá', -15.60, -56.10], ['Goiânia', -16.68, -49.25], ['Belo Horizonte', -19.92, -43.94],
  ['São Paulo', -23.55, -46.63], ['Rio de Janeiro', -22.91, -43.20], ['Curitiba', -25.43, -49.27],
  ['Porto Alegre', -30.03, -51.23],
];
function capitalIcon(name) {
  return L.divIcon({
    html: `<span class="map-capital"><span class="cap-dot"></span>${name}</span>`,
    className: 'map-label-icon',
    iconSize: [120, 14],
    iconAnchor: [3, 7],
  });
}

/* Série sintética de 30 dias para o gráfico de tendências */
const TREND = [
  { d: '15/04', risco: 62, casos: 520,  alertas: 14 },
  { d: '18/04', risco: 64, casos: 560,  alertas: 15 },
  { d: '22/04', risco: 67, casos: 640,  alertas: 17 },
  { d: '25/04', risco: 70, casos: 720,  alertas: 19 },
  { d: '29/04', risco: 73, casos: 860,  alertas: 21 },
  { d: '02/05', risco: 76, casos: 980,  alertas: 24 },
  { d: '06/05', risco: 79, casos: 1080, alertas: 27 },
  { d: '09/05', risco: 82, casos: 1180, alertas: 29 },
  { d: '14/05', risco: 86, casos: 1280, alertas: 32 },
];

const RECENT_ALERTS = [
  ['Risco muito alto em 12 municípios', 'Sertão de Santana', '5 min', 'critico'],
  ['Aumento rápido de casos prováveis', 'Feira de Santana e entorno', '18 min', 'critico'],
  ['Chuvas acima da média previstas', 'Extremo Sul e Sul Baiano', '45 min', 'alto'],
  ['NDVI indica condições favoráveis ao vetor', 'Recôncavo Baiano', '1 h', 'atencao'],
];

const TODAY_ACTIONS = [
  ['Intensificar ações de bloqueio vetorial', 'Sertão de Santana e 8 municípios', 'Alta', 'alta'],
  ['Mobilizar equipes de campo', 'Feira de Santana e entorno', 'Alta', 'alta'],
  ['Comunicar risco à população', '12 municípios com risco muito alto', 'Média', 'media'],
  ['Monitorar condições climáticas', 'Extremo Sul e Sul Baiano', 'Baixa', 'baixa'],
];

function Spark({ color = '#f43f5e', up = true }) {
  const pts = up
    ? '0,24 14,20 28,22 42,15 56,16 70,9 84,11 100,3'
    : '0,4 14,8 28,7 42,12 56,11 70,17 84,15 100,22';
  return (
    <svg viewBox="0 0 100 26" width="100%" height="22" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

function Bars({ color = '#3b82f6' }) {
  const h = [7, 9, 8, 12, 11, 15, 14, 18];
  return (
    <svg viewBox="0 0 100 24" width="100%" height="22" preserveAspectRatio="none">
      {h.map((v, i) => (
        <rect key={i} x={i * 13} y={24 - v} width="8" height={v} rx="1.5" fill={color} opacity={0.45 + i * 0.07} />
      ))}
    </svg>
  );
}

export default function VisaoGeral({ onNavigate }) {
  const [risk, setRisk] = useState(BRAZIL_MUNICIPALITIES);
  const [brGeo, setBrGeo] = useState(null);

  useEffect(() => {
    fetchLatestRisk(30).then((rows) => { if (rows?.length) setRisk(rows); }).catch(() => {});
    loadAllMunicipalities().then(setBrGeo).catch(() => {});
  }, []);

  const top5 = [...risk]
    .sort((a, b) => (b.environmental_risk_score || 0) - (a.environmental_risk_score || 0))
    .slice(0, 5);

  const heatPoints = useMemo(() => riskHeatPoints(brGeo, 70), [brGeo]);

  const munStyle = (feature) => {
    const s = feature.properties.score || 0;
    return {
      fillColor: riskGradient(s),
      fillOpacity: 0.9,
      color: '#0a0e15',
      weight: 0.25,
    };
  };

  const KPIS = [
    { label: 'Municípios monitorados', value: '5.564', sub: 'cobertura nacional', delta: '+8 vs. ontem', dc: 'up', spark: <Spark color="#3b82f6" />, vcolor: 'var(--text-primary)' },
    { label: 'Alertas críticos', value: '132', sub: 'em 14 estados', delta: '+18 vs. ontem', dc: 'up', spark: <Spark color="#f43f5e" />, vcolor: '#f43f5e' },
    { label: 'População em risco', value: '18,4 mi', sub: 'pessoas', delta: '+1,2 mi vs. ontem', dc: 'up', spark: <Spark color="#a855f7" />, vcolor: 'var(--text-primary)' },
    { label: 'Impacto evitável', value: '42%', sub: 'com ações recomendadas', delta: '+7 p.p. vs. ontem', dc: 'down', spark: <Spark color="#22c55e" up={false} />, vcolor: '#22c55e' },
    { label: 'Confiança do modelo', value: '92%', sub: 'alta confiança', delta: '+2 p.p.', dc: 'down', spark: <Bars color="#3b82f6" />, vcolor: '#3b82f6' },
  ];

  return (
    <>
      {/* ── Faixa de KPIs ── */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
        <div className="kpi-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div className="kpi-label" style={{ alignSelf: 'flex-start' }}>Risco global</div>
          <Gauge score={86.4} size={104} />
          <span className="risk-badge critico" style={{ marginTop: 2 }}>Muito alto</span>
          <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: 5 }}>Percentil nacional: 94°</div>
        </div>

        {KPIS.map(({ label, value, sub, delta, dc, spark, vcolor }) => (
          <div key={label} className="kpi-card">
            <div className="kpi-label">{label}</div>
            <div className="kpi-value" style={{ color: vcolor }}>{value}</div>
            {spark}
            <div className={`kpi-delta ${dc}`}>
              {dc === 'up' ? <ArrowUpRight size={12} /> : <ArrowUpRight size={12} style={{ transform: 'rotate(90deg)' }} />}
              {delta}
            </div>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: 2 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* ── Mapa nacional + Tendências ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.55fr 1fr', gap: 16, marginBottom: 18 }}>
        {/* Visão do risco — heatmap nacional (Brasil inteiro) */}
        <div className="overview-map-card" style={{ height: 420 }}>
          <div className="card-header" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <h3>Visão do risco</h3>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                Panorama nacional do risco de dengue · arraste e dê zoom para explorar
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <select className="filter-select" style={{ width: 'auto', padding: '6px 28px 6px 10px', fontSize: 12 }}>
                <option>Risco (Dengue)</option>
              </select>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => onNavigate('map')}>
                Mapa completo <ChevronRight size={13} />
              </button>
            </div>
          </div>

          <div className="mini-map-wrap">
            <MapContainer center={[-15, -54]} zoom={4} minZoom={3} maxZoom={9} zoomControl={false}
              scrollWheelZoom={false} zoomSnap={0.25} attributionControl={false}
              style={{ width: '100%', height: '100%' }} preferCanvas>
              {brGeo && <FitBrazil geo={brGeo} />}
              {brGeo && <GeoJSON key="br-heat" data={brGeo} style={munStyle} />}
              <HeatGlow points={heatPoints} />
              {REGION_LABELS.map(([t, la, ln, k]) => (
                <Marker key={t} position={[la, ln]} icon={labelIcon(t, k)} interactive={false} />
              ))}
              {CAPITALS.map(([name, la, ln]) => (
                <Marker key={name} position={[la, ln]} icon={capitalIcon(name)} interactive={false} />
              ))}
              <ZoomControl position="topright" />
            </MapContainer>

            {/* Legenda sobreposta (estilo concept) */}
            <div className="risk-legend-overlay">
              <div className="rlo-title">Índice de risco</div>
              <div className="rlo-bar" />
              <div className="rlo-ticks"><span>0</span><span>25</span><span>50</span><span>75</span><span>100</span></div>
              <div className="rlo-labels">
                <span>Muito<br />Baixo</span><span>Baixo</span><span>Moderado</span><span>Alto</span><span>Muito<br />Alto</span>
              </div>
              <div className="rlo-scale"><span className="rlo-scale-bar" />500 km</div>
            </div>
          </div>
        </div>

        {/* Tendências */}
        <div className="card" style={{ height: 420, display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ paddingBottom: 8 }}>
            <div>
              <h3>Tendências</h3>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Últimos 30 dias</p>
            </div>
          </div>
          <div style={{ padding: '6px 16px 0', display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            {[['Índice de risco', '#f43f5e', '86,4'], ['Casos prováveis', '#f59e0b', '1.280'], ['Alertas críticos', '#38bdf8', '32']].map(([l, c, v]) => (
              <span key={l} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />{l} <strong style={{ color: 'var(--text-primary)' }}>{v}</strong>
              </span>
            ))}
          </div>
          <div style={{ flex: 1, minHeight: 0, padding: '8px 6px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={TREND} margin={{ top: 8, right: 6, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="rgba(148,163,184,.1)" vertical={false} />
                <XAxis dataKey="d" tick={{ fill: '#647689', fontSize: 10 }} tickLine={false} axisLine={{ stroke: 'rgba(148,163,184,.15)' }} />
                <YAxis yAxisId="l" domain={[0, 100]} tick={{ fill: '#647689', fontSize: 10 }} tickLine={false} axisLine={false} width={26} />
                <YAxis yAxisId="r" orientation="right" domain={[0, 2800]} tick={{ fill: '#647689', fontSize: 10 }} tickLine={false} axisLine={false} width={34} />
                <Tooltip contentStyle={{ background: '#0e1520', border: '1px solid rgba(148,163,184,.25)', borderRadius: 8, fontSize: 12 }} labelStyle={{ color: '#e8eef7' }} itemStyle={{ padding: 0 }} />
                <Line yAxisId="l" type="monotone" dataKey="risco" stroke="#f43f5e" strokeWidth={2} dot={false} name="Índice de risco" />
                <Line yAxisId="r" type="monotone" dataKey="casos" stroke="#f59e0b" strokeWidth={2} dot={false} name="Casos prováveis" />
                <Line yAxisId="l" type="monotone" dataKey="alertas" stroke="#38bdf8" strokeWidth={2} dot={false} name="Alertas críticos" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, padding: '8px 16px 14px', borderTop: '1px solid var(--border)' }}>
            {[['Risco médio', '+18%'], ['Casos prováveis', '+22%'], ['Alertas críticos', '+29%']].map(([l, v]) => (
              <div key={l}>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{l}</div>
                <div style={{ fontSize: 14, fontWeight: 800, color: '#f43f5e', display: 'flex', alignItems: 'center', gap: 2 }}><ArrowUpRight size={13} />{v}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 4 painéis inferiores ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, alignItems: 'start' }}>
        <div className="card">
          <div className="card-header" style={{ paddingBottom: 10 }}><h3>Principais regiões em atenção</h3></div>
          <div className="card-body" style={{ paddingTop: 4 }}>
            {top5.map((m) => {
              const lvl = m.environmental_risk_score >= 85 ? 'critico' : m.environmental_risk_score >= 70 ? 'alto' : 'atencao';
              return (
                <div key={m.geocode} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid var(--border-soft)' }}>
                  <Building2 size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.municipio} ({m.uf})</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{Math.round((m.pop || 400000) / 1000)} mil hab. em risco</div>
                  </div>
                  <span className={`risk-badge ${lvl}`}>{lvl === 'critico' ? 'Muito alto' : lvl === 'alto' ? 'Alto' : 'Moderado'}</span>
                </div>
              );
            })}
            <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: 8, padding: 0 }} onClick={() => onNavigate('map')}>Ver todas as regiões →</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header" style={{ paddingBottom: 10 }}><h3>Alertas recentes</h3></div>
          <div className="card-body" style={{ paddingTop: 4 }}>
            {RECENT_ALERTS.map(([titulo, regiao, tempo, lvl]) => (
              <div key={titulo} style={{ display: 'flex', gap: 9, padding: '8px 0', borderBottom: '1px solid var(--border-soft)' }}>
                <AlertTriangle size={14} style={{ color: `var(--risk-${lvl})`, flexShrink: 0, marginTop: 2 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600 }}>{titulo}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Região: {regiao}</div>
                </div>
                <span style={{ fontSize: 10.5, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{tempo}</span>
              </div>
            ))}
            <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: 8, padding: 0 }} onClick={() => onNavigate('alerts')}>Ver todos os alertas →</button>
          </div>
        </div>

        <div className="card">
          <div className="card-header" style={{ paddingBottom: 10 }}><h3>Ações recomendadas para hoje</h3></div>
          <div className="card-body" style={{ paddingTop: 4 }}>
            {TODAY_ACTIONS.map(([titulo, regiao, prio, cls]) => (
              <div key={titulo} style={{ display: 'flex', gap: 9, padding: '8px 0', borderBottom: '1px solid var(--border-soft)' }}>
                <ShieldCheck size={14} style={{ color: 'var(--blue)', flexShrink: 0, marginTop: 2 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12.5, fontWeight: 600 }}>{titulo}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{regiao}</div>
                </div>
                <span className={`action-priority ${cls}`} style={{ height: 'fit-content' }}>{prio}</span>
              </div>
            ))}
            <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: 8, padding: 0 }} onClick={() => onNavigate('actions')}>Ver todas as ações →</button>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ paddingBottom: 10 }}>
            <h3><Bot size={15} style={{ color: 'var(--blue)' }} /> Copilot <span className="topbar-badge-beta">BETA</span></h3>
          </div>
          <div className="card-body" style={{ paddingTop: 4, flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
              <div className="chat-avatar bot" style={{ width: 30, height: 30 }}><Bot size={15} /></div>
              <p style={{ fontSize: 12.5, lineHeight: 1.55, color: 'var(--text-secondary)' }}>
                O risco de dengue está <strong style={{ color: 'var(--risk-critico)' }}>muito alto</strong> no Nordeste e Norte.
                Recomendo priorizar as regiões em vermelho no mapa e intensificar a mobilização nos focos com aumento rápido de casos.
              </p>
            </div>
            <button type="button" className="btn btn-primary" style={{ width: '100%', marginBottom: 10 }} onClick={() => onNavigate('copilot')}>
              Ver análise completa <ChevronRight size={14} />
            </button>
            <div className="chat-input-row" style={{ marginTop: 'auto' }}>
              <input className="chat-textarea" style={{ minHeight: 38, padding: '9px 12px' }} placeholder="Pergunte ao Copilot..." readOnly onClick={() => onNavigate('copilot')} />
              <button type="button" className="chat-send-btn" style={{ width: 38, height: 38 }} onClick={() => onNavigate('copilot')}><Send size={15} /></button>
            </div>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 24 }}>
        © 2025 Vectra. Todos os direitos reservados. • Versão 2.4.1
      </div>
    </>
  );
}
