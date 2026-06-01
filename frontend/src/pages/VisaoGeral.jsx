import { useEffect, useMemo, useState } from 'react';
import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  Activity, AlertTriangle, ArrowUpRight,
  ChevronRight, Map,
} from 'lucide-react';
import { BRAZIL_MUNICIPALITIES, riskColor, topByRisk } from '../data/brazilMunicipalities.js';
import { loadStates, REGION_UFS, scoreColor } from '../data/geoLoader.js';
import { fetchLatestRisk } from '../api/vectraApi.js';

const REGION_BASE = { Norte: 78, Nordeste: 74, 'Centro-Oeste': 68, Sudeste: 62, Sul: 40 };
function ufRegion(uf) {
  return Object.entries(REGION_UFS).find(([, ufs]) => ufs.includes(uf))?.[0];
}

function Sparkline({ color = '#ef4444', up = true }) {
  const pts = up
    ? '0,28 10,24 20,26 30,20 40,18 50,14 60,16 70,10 80,8 90,4 100,2'
    : '0,4 10,8 20,6 30,10 40,12 50,16 60,14 70,20 80,22 90,26 100,28';
  return (
    <svg viewBox="0 0 100 30" className="kpi-sparkline" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

function CapacityBar({ value, color }) {
  return (
    <div className="capacity-bar">
      <div className="capacity-bar-fill" style={{ width: `${value}%`, background: color }} />
    </div>
  );
}

export default function VisaoGeral({ onNavigate }) {
  const [risk, setRisk]   = useState(BRAZIL_MUNICIPALITIES);
  const [states, setStates] = useState(null);

  useEffect(() => {
    fetchLatestRisk(30)
      .then((rows) => { if (rows?.length) setRisk(rows); })
      .catch(() => {});
    loadStates().then(setStates).catch(() => {});
  }, []);

  const stateStyle = (feature) => {
    const base = REGION_BASE[ufRegion(feature.properties.sigla)] || 60;
    return { fillColor: scoreColor(base), fillOpacity: 0.55, color: 'rgba(255,255,255,.35)', weight: 0.7 };
  };

  const summary = useMemo(() => {
    const total     = risk.length;
    const critical  = risk.filter((m) => m.environmental_risk_score >= 85).length;
    const affected  = risk.reduce((acc, m) => acc + (m.pop || 400000), 0);
    const bedPressure = risk.reduce((acc, m) => acc + (m.leitos_ocupacao_pct || 70), 0) / risk.length;
    return { total, critical, affected, bedPressure };
  }, [risk]);

  const top5 = topByRisk(5);
  const topAlert = BRAZIL_MUNICIPALITIES.find((m) => m.municipio === 'Fortaleza') || BRAZIL_MUNICIPALITIES[0];

  return (
    <>
      {/* Capacidade assistencial - prioridade operacional */}
      <div style={{ marginBottom: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18 }}>Capacidade assistencial</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              Pressão da rede antes de decidir onde agir primeiro.
            </div>
          </div>
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => onNavigate('actions')}>
            Ver alocação de recursos <ChevronRight size={13} />
          </button>
        </div>
        <div className="capacity-grid">
          {[
            { label: 'Leitos clínicos',     val: 62, sub: 'ocupação',     color: '#f97316' },
            { label: 'Leitos de UTI',       val: 58, sub: 'ocupação',     color: '#eab308' },
            { label: 'Unidades de saúde',   val: 71, sub: 'operacionais', color: '#22c55e' },
            { label: 'Equipes disponíveis', val: 85, sub: 'ativas',       color: '#2563eb' },
          ].map(({ label, val, sub, color }) => (
            <div key={label} className="capacity-card">
              <div className="capacity-label">{label}</div>
              <div className="capacity-value">{val}%</div>
              <div className="capacity-sub">{sub}</div>
              <CapacityBar value={val} color={color} />
            </div>
          ))}
        </div>
      </div>

      {/* KPI strip */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Situação atual</div>
          <div className="kpi-value" style={{ color: 'var(--text-primary)' }}>
            <AlertTriangle size={18} style={{ display: 'inline', marginRight: 6, color: 'var(--risk-critico)' }} />
            {summary.critical}
          </div>
          <Sparkline color="#ef4444" up />
          <div className="kpi-delta up">
            <ArrowUpRight size={13} /> +16%
            <span className="kpi-delta-label">vs. 7 dias</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>alertas ativos</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Municípios em risco</div>
          <div className="kpi-value">{summary.total}</div>
          <Sparkline color="#f97316" up />
          <div className="kpi-delta up">
            <ArrowUpRight size={13} /> +12%
            <span className="kpi-delta-label">vs. 7 dias</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>municípios</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Pessoas potenc. afetadas</div>
          <div className="kpi-value">{(summary.affected / 1e6).toFixed(1)}M</div>
          <Sparkline color="#f97316" up />
          <div className="kpi-delta up">
            <ArrowUpRight size={13} /> +9%
            <span className="kpi-delta-label">vs. 7 dias</span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>pessoas</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Tendência semanal</div>
          <div className="kpi-value" style={{ color: 'var(--risk-critico)', fontSize: 22, paddingTop: 4 }}>Em alta</div>
          <Sparkline color="#ef4444" up />
          <div className="kpi-delta up" style={{ marginTop: 2 }}>
            <ArrowUpRight size={13} /> Risco crescente
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="overview-grid">
        {/* Mapa */}
        <div className="overview-map-card">
          <div className="card-header" style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
            <div>
              <h3><Map size={15} style={{ display: 'inline', marginRight: 5 }} />Área mais crítica</h3>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Risco atual por município</p>
            </div>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => onNavigate('map')}>
              Abrir mapa completo <ChevronRight size={13} />
            </button>
          </div>

          <div className="mini-map-wrap">
            <MapContainer center={[-14, -52]} zoom={4} zoomControl={false} scrollWheelZoom={false}
              style={{ width: '100%', height: '100%' }} preferCanvas>
              <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" attribution="" />
              {states && <GeoJSON key="ov-states" data={states} style={stateStyle} />}
              {risk.slice(0, 30).map((m) => (
                <CircleMarker key={m.geocode}
                  center={[m.lat, m.lng]}
                  radius={m.environmental_risk_score >= 85 ? 7 : m.environmental_risk_score >= 70 ? 5 : 4}
                  pathOptions={{ color: '#fff', weight: 1, fillColor: riskColor(m.environmental_risk_score), fillOpacity: 0.9 }}>
                  <Popup>
                    <strong>{m.municipio} — {m.uf}</strong><br />
                    Risco: {m.environmental_risk_score} | Casos: {m.casos_dengue}
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          <div style={{ padding: '10px 16px', borderTop: '1px solid var(--border)', display: 'flex', gap: 16, fontSize: 12 }}>
            {[['#16a34a','Baixo'],['#ca8a04','Moderado'],['#ea580c','Alto'],['#dc2626','Muito alto']].map(([c,l]) => (
              <span key={l} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: c, display: 'inline-block' }} />
                {l}
              </span>
            ))}
          </div>
        </div>

        {/* Alerta crítico */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="alert-card-critical">
            <div className="alert-city-badge">
              <AlertTriangle size={12} /> PRIORIDADE MÁXIMA
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Alerta crítico</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 3 }}>{topAlert.municipio} — {topAlert.uf}</div>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
              Aumento acelerado de casos de dengue
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 14 }}>
              {[
                ['Risco', `${topAlert.environmental_risk_score}/100`, 'Muito alto'],
                ['Tendência', 'Acelerando', 'vs. 7 dias'],
                ['Em risco', `${(topAlert.pop/1e6).toFixed(1)}M`, 'estimadas'],
              ].map(([label, val, sub]) => (
                <div key={label} style={{ background: 'var(--bg)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                  <div style={{ fontSize: 17, fontWeight: 800, color: label === 'Risco' ? 'var(--risk-critico)' : 'var(--text-primary)' }}>{val}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>
                </div>
              ))}
            </div>

            <button type="button" className="btn btn-primary" style={{ width: '100%' }}
              onClick={() => onNavigate('actions')}>
              Ver plano de ação <ChevronRight size={14} />
            </button>
          </div>

          {/* Por que está crítico */}
          <div className="card">
            <div className="card-header"><h3>Por que está crítico?</h3></div>
            <div className="card-body" style={{ paddingTop: 10 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--risk-critico)' }}>
                  <ArrowUpRight size={20} style={{ display: 'inline' }} /> 56%
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>vs. 7 dias</div>
              </div>
              {[
                ['Positividade', '28%', 'Alta'],
                ['Ocupação leitos', '78%', 'Crescente'],
              ].map(([k, v, s]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                  <span style={{ fontWeight: 700 }}>{v} <span style={{ fontWeight: 400, color: 'var(--text-muted)', fontSize: 11 }}>{s}</span></span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* O que fazer agora */}
        <div className="card" style={{ alignSelf: 'start' }}>
          <div className="card-header"><h3>O que fazer agora</h3></div>
          <div className="card-body" style={{ paddingTop: 10 }}>
            <div className="action-list">
              {[
                ['Mobilizar equipes de saúde',       'Reforce o coberturas nas unidades.'],
                ['Ampliar testagem',                  'Priorize áreas com maior incidência.'],
                ['Comunicar à população',             'Oriente sobre prevenção e sinais de alerta.'],
                ['Acompanhar evolução',               'Monitore os indicadores nas próximas 48h.'],
              ].map(([title, sub]) => (
                <div key={title} className="action-item">
                  <Activity size={14} style={{ color: 'var(--blue)', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{sub}</div>
                  </div>
                  <ChevronRight size={13} style={{ marginLeft: 'auto', color: 'var(--text-muted)' }} />
                </div>
              ))}
            </div>
            <button type="button" className="btn btn-ghost" style={{ marginTop: 12, padding: 0 }}
              onClick={() => onNavigate('actions')}>
              Ver todas as ações →
            </button>
          </div>
        </div>
      </div>

      {/* Top 5 municípios */}
      <div style={{ marginTop: 20 }}>
        <div className="card">
          <div className="card-header" style={{ paddingBottom: 14 }}>
            <h3>Top 5 regiões críticas</h3>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => onNavigate('map')}>
              Ver mapa de risco →
            </button>
          </div>
          <div className="card-body" style={{ paddingTop: 0 }}>
            {top5.map((m, i) => (
              <div key={m.geocode} className="ranking-row">
                <span className="rank-num">{i + 1}</span>
                <span className="rank-name">{m.municipio} ({m.uf})</span>
                <span className="rank-bar-wrap">
                  <div className="rank-bar" style={{ width: `${m.environmental_risk_score}%`, background: riskColor(m.environmental_risk_score) }} />
                </span>
                <span className={`rank-score ${m.environmental_risk_score >= 85 ? 'score-red' : m.environmental_risk_score >= 70 ? 'score-orange' : 'score-yellow'}`}>
                  {(m.environmental_risk_score / 10).toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 24 }}>
        © 2025 Vectra. Todos os direitos reservados.
      </div>
    </>
  );
}
