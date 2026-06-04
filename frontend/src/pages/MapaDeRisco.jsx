import { useEffect, useMemo, useState } from 'react';
import { GeoJSON, MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { AlertTriangle, ArrowUpRight, Calendar, Filter, Layers, Loader2, RefreshCw } from 'lucide-react';
import {
  loadAllMunicipalities, loadManifest, loadNationalRisk, loadRegionMunicipalities,
  REGION_UFS, REGION_VIEW, riskGradient, riskHeatPoints, scoreColor,
} from '../data/geoLoader.js';
import HeatGlow from '../components/HeatGlow.jsx';

const BASEMAPS = {
  satelite: { label: 'Satélite', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}' },
  hibrido:  { label: 'Híbrido',  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}' },
  terreno:  { label: 'Terreno',  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}' },
  escuro:   { label: 'Escuro',   url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png' },
};

const REGIONS = ['Todos', 'Sudeste', 'Nordeste', 'Norte', 'Centro-Oeste', 'Sul'];
const DISEASES = ['Dengue', 'Chikungunya', 'Zika'];
const RISK_LEVELS = [
  { key: 'baixo',   label: 'Baixo',    color: '#16a34a', min: 0,  max: 50 },
  { key: 'atencao', label: 'Atenção',  color: '#ca8a04', min: 50, max: 70 },
  { key: 'alto',    label: 'Alto',     color: '#ea580c', min: 70, max: 85 },
  { key: 'critico', label: 'Crítico',  color: '#dc2626', min: 85, max: 101 },
];

function labelOf(score) {
  if (score >= 85) return 'critico';
  if (score >= 70) return 'alto';
  if (score >= 50) return 'atencao';
  return 'baixo';
}

/** Reposiciona o mapa quando a região muda */
function MapView({ view }) {
  const map = useMap();
  useEffect(() => {
    if (view) map.flyTo(view.center, view.zoom, { duration: 0.8 });
  }, [view, map]);
  return null;
}

function RiskGauge({ score }) {
  const color = scoreColor(score);
  return (
    <svg width="80" height="60" viewBox="0 0 80 60" className="risk-gauge-svg">
      <path d="M10,55 A35,35 0 1,1 70,55" fill="none" stroke="rgba(148,163,184,.18)" strokeWidth="8" strokeLinecap="round" />
      <path d="M10,55 A35,35 0 1,1 70,55" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
        strokeDasharray={`${(score / 100) * 110} 110`} />
      <circle cx="40" cy="40" r="4" fill={color} />
    </svg>
  );
}

export default function MapaDeRisco() {
  const [region, setRegion]       = useState('Todos');
  const [disease, setDisease]     = useState('Dengue');
  const [geojson, setGeojson]     = useState(null);
  const [risk, setRisk]           = useState({});
  const [loading, setLoading]     = useState(true);
  const [selected, setSelected]   = useState(null);
  const [manifest, setManifest]   = useState(null);
  const [basemap, setBasemap]     = useState('satelite');
  const [activeRisks, setActiveRisks] = useState(new Set(['baixo','atencao','alto','critico']));

  // carrega risco nacional + estados + manifest uma vez
  useEffect(() => {
    loadNationalRisk().then(setRisk).catch(() => {});
    loadManifest().then(setManifest).catch(() => {});
  }, []);

  // carrega municípios — Brasil inteiro ('Todos') ou região específica
  useEffect(() => {
    let cancel = false;
    setLoading(true);
    const loader = region === 'Todos' ? loadAllMunicipalities() : loadRegionMunicipalities(region);
    loader
      .then((fc) => {
        if (cancel) return;
        setGeojson(fc);
        // seleciona o município de maior risco do recorte atual
        const top = [...fc.features].sort((a, b) => b.properties.score - a.properties.score)[0];
        if (top) setSelected(top.properties);
      })
      .catch(() => !cancel && setGeojson(null))
      .finally(() => !cancel && setLoading(false));
    return () => { cancel = true; };
  }, [region]);

  const view = REGION_VIEW[region] || REGION_VIEW.Todos;

  function toggleRisk(key) {
    setActiveRisks((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  // estilo do choropleth municipal — efeito de calor sobre satélite
  const munStyle = (feature) => {
    const score = feature.properties.score || 0;
    const visible = activeRisks.has(labelOf(score));
    // opacidade cresce com o score → áreas mais quentes "queimam" mais forte
    const heat = 0.5 + (score / 100) * 0.45; // 0.50 → 0.95
    const isSel = selected?.geocode === feature.properties.geocode;
    return {
      fillColor: riskGradient(score),
      fillOpacity: visible ? heat : 0.04,
      color: isSel ? '#ffffff' : 'rgba(255,255,255,.16)',
      weight: isSel ? 2.6 : 0.25,
    };
  };

  const onEachMun = (feature, layer) => {
    const p = feature.properties;
    layer.bindTooltip(`${p.name} — ${p.uf} · risco ${p.score}`, { sticky: true });
    layer.on('click', () => setSelected(p));
  };

  const geoKey = `${region}-${[...activeRisks].sort().join('')}-${selected?.geocode || ''}`;

  // contadores
  const counts = useMemo(() => {
    if (!geojson) return { total: 0 };
    return { total: geojson.features.length };
  }, [geojson]);

  const heatPoints = useMemo(() => riskHeatPoints(geojson, 70), [geojson]);

  const reasons = [
    'Transmissão em alta e sazonalidade atual',
    'Incidência por 100 mil habitantes acima da média',
    'Muitos casos prováveis nas últimas semanas',
    'Condições climáticas favoráveis',
  ];
  const actions = [
    { label: 'Intensificar visitação e controle vetorial', priority: 'Alta' },
    { label: 'Mobilizar equipes para eliminação de criadouros', priority: 'Alta' },
    { label: 'Comunicar risco à população e reforçar prevenção', priority: 'Média' },
  ];

  const selScore = selected?.score ?? 0;
  const selRisk  = selected ? risk[selected.geocode] : null;

  return (
    <div className="map-page-layout">
      {/* ── Filtros ── */}
      <div className="card map-filters-panel">
        <div className="card-header" style={{ paddingBottom: 14, borderBottom: '1px solid var(--border)' }}>
          <h3><Filter size={14} /> Filtros</h3>
          <button type="button" className="btn btn-ghost btn-sm" style={{ color: 'var(--text-muted)' }}
            onClick={() => { setActiveRisks(new Set(['baixo','atencao','alto','critico'])); setRegion('Todos'); }}>
            <RefreshCw size={12} /> Limpar
          </button>
        </div>

        <div className="filter-section">
          <div className="filter-label">Região</div>
          <select className="filter-select" value={region} onChange={(e) => setRegion(e.target.value)}>
            {REGIONS.map((r) => <option key={r}>{r}</option>)}
          </select>
        </div>

        <div className="filter-section">
          <div className="filter-label">Doença</div>
          <select className="filter-select" value={disease} onChange={(e) => setDisease(e.target.value)}>
            {DISEASES.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>

        <div className="filter-section">
          <div className="filter-label">Período</div>
          <div className="filter-date-range">
            <Calendar size={13} /> 08/05/2025 — 14/05/2025
          </div>
        </div>

        <div className="filter-section">
          <div className="filter-label">Nível de risco</div>
          <div className="risk-checkbox-group">
            {RISK_LEVELS.map(({ key, label, color }) => (
              <label key={key} className="risk-checkbox">
                <input type="checkbox" checked={activeRisks.has(key)} onChange={() => toggleRisk(key)} />
                <span className="risk-dot" style={{ background: color, borderRadius: 3 }} />
                {label}
              </label>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <div className="filter-label">Cobertura</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            <strong>{region === 'Todos' ? '27 estados' : `${counts.total} municípios`}</strong>
            {region !== 'Todos' && ` · ${REGION_UFS[region]?.length} UFs`}
          </div>
        </div>

        <div style={{ padding: '16px 18px' }}>
          <button type="button" className="btn btn-primary" style={{ width: '100%' }}>
            <Filter size={14} /> Aplicar filtros
          </button>
        </div>
      </div>

      {/* ── Mapa ── */}
      <div className="map-container-card">
        <div className="map-container-header">
          <div>
            <div style={{ fontWeight: 700, fontSize: 14 }}>Risco de surto por município</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {loading ? 'Carregando municípios...' :
                region === 'Todos' ? '27 estados · visão nacional' : `${counts.total} municípios monitorados · ${region}`}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {manifest?.real_data && (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600,
                color: 'var(--green)', background: 'var(--risk-baixo-bg)', padding: '4px 9px', borderRadius: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--green)' }} />
                {manifest.real_data.municipalities_with_real_score} munic. com dado real (InfoDengue)
              </span>
            )}
            {loading && <Loader2 size={16} className="loading-pulse" style={{ color: 'var(--blue)' }} />}
          </div>
        </div>

        <div className="map-leaflet-wrap">
          <MapContainer center={view.center} zoom={view.zoom} minZoom={3} maxZoom={12}
            style={{ width: '100%', height: '100%' }} preferCanvas>
            <TileLayer key={basemap} url={BASEMAPS[basemap].url} attribution="" />
            {basemap === 'hibrido' && (
              <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}" attribution="" />
            )}
            <MapView view={view} />

            {/* Choropleth municipal — Brasil inteiro ou região */}
            {geojson && (
              <GeoJSON key={geoKey} data={geojson} style={munStyle} onEachFeature={onEachMun} />
            )}
            {geojson && <HeatGlow points={heatPoints} />}
          </MapContainer>

          {/* Seletor de camada base (overlay) */}
          <div className="basemap-switcher">
            {Object.entries(BASEMAPS).map(([key, b]) => (
              <button key={key} type="button"
                className={basemap === key ? 'active' : ''}
                onClick={() => setBasemap(key)}>
                {b.label}
              </button>
            ))}
          </div>
        </div>

        <div className="map-legend">
          <span className="map-legend-title">Índice de risco</span>
          {RISK_LEVELS.map(({ label, color }) => (
            <div key={label} className="map-legend-item">
              <span className="legend-dot" style={{ background: color }} />{label}
            </div>
          ))}
          <span className="map-legend-scale">
            <span style={{ background: 'linear-gradient(90deg,#16a34a,#65a30d,#ca8a04,#ea580c,#dc2626)' }} />
            0 — 100
          </span>
        </div>
      </div>

      {/* ── Painel direito ── */}
      <div className="card map-detail-panel" style={{ overflowY: 'auto' }}>
        {selected ? (
          <>
            <div className="territory-header">
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>Território selecionado</div>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
                <div>
                  <div className="territory-name">{selected.name} – {selected.uf}</div>
                  <div className="territory-sub">Região {selected.region}</div>
                </div>
                <span className={`risk-badge ${labelOf(selScore)}`}>
                  {labelOf(selScore) === 'critico' ? 'Muito alto risco' :
                   labelOf(selScore) === 'alto' ? 'Alto risco' :
                   labelOf(selScore) === 'atencao' ? 'Atenção' : 'Baixo risco'}
                </span>
              </div>
            </div>

            <div className="risk-gauge-wrap">
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Índice de Risco ({disease})</div>
                <div className="risk-gauge-value" style={{ color: scoreColor(selScore) }}>
                  {selScore.toFixed(1)}<span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-muted)' }}> /100</span>
                </div>
                <div className="risk-gauge-label">Percentil nacional: {Math.round(selScore * 0.97)}°</div>
                <div style={{ fontSize: 10, marginTop: 4, display: 'inline-flex', alignItems: 'center', gap: 4,
                  color: selRisk?.real ? 'var(--green)' : 'var(--text-muted)' }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%',
                    background: selRisk?.real ? 'var(--green)' : 'var(--text-muted)' }} />
                  {selRisk?.real ? 'Fonte: InfoDengue (dado real)' : 'Estimativa do modelo'}
                </div>
              </div>
              <RiskGauge score={selScore} />
            </div>

            {selRisk && (
              <div className="territory-section" style={{ display: 'flex', gap: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Casos (semana)</div>
                  <div style={{ fontSize: 20, fontWeight: 800 }}>{selRisk.c}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Incidência /100k</div>
                  <div style={{ fontSize: 20, fontWeight: 800 }}>{selRisk.i}</div>
                </div>
              </div>
            )}

            <div className="territory-section">
              <div className="territory-section-title"><AlertTriangle size={13} /> Por que está em risco?</div>
              {reasons.map((r) => (
                <div key={r} className="reason-item">
                  <ArrowUpRight size={13} style={{ color: 'var(--risk-critico)', marginTop: 1, flexShrink: 0 }} />{r}
                </div>
              ))}
            </div>

            <div className="territory-section">
              <div className="territory-section-title">Tendência recente (últimos 30 dias)</div>
              <div className="trend-block">
                <div className="trend-value"><ArrowUpRight size={18} /> 28%</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Crescente</div>
              </div>
            </div>

            <div className="territory-section">
              <div className="territory-section-title">O que fazer agora</div>
              <div className="action-list">
                {actions.map(({ label, priority }) => (
                  <div key={label} className="action-item" style={{ fontSize: 12 }}>
                    <span style={{ flex: 1 }}>{label}</span>
                    <span className={`action-priority ${priority.toLowerCase()}`}>{priority}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
            <Layers size={36} style={{ margin: '0 auto 12px', opacity: .3, display: 'block' }} />
            <p style={{ fontSize: 13 }}>Selecione um município no mapa para ver os detalhes.</p>
          </div>
        )}
      </div>
    </div>
  );
}
