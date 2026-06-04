/**
 * geoLoader.js — Carregamento sob demanda dos assets geoespaciais.
 * Os arquivos vivem em /public/geo/ e são servidos estaticamente pelo Vite.
 */

const GEO_BASE = '/geo';

/** Mapa de região → lista de UFs */
export const REGION_UFS = {
  Norte:          ['RO', 'AC', 'AM', 'RR', 'PA', 'AP', 'TO'],
  Nordeste:       ['MA', 'PI', 'CE', 'RN', 'PB', 'PE', 'AL', 'SE', 'BA'],
  'Centro-Oeste': ['MS', 'MT', 'GO', 'DF'],
  Sudeste:        ['MG', 'ES', 'RJ', 'SP'],
  Sul:            ['PR', 'SC', 'RS'],
};

/** Centro/zoom aproximado por região para o mapa */
export const REGION_VIEW = {
  Todos:          { center: [-14.5, -52], zoom: 4 },
  Norte:          { center: [-4, -60],    zoom: 5 },
  Nordeste:       { center: [-9, -40],    zoom: 5 },
  'Centro-Oeste': { center: [-15, -54],   zoom: 5 },
  Sudeste:        { center: [-20, -45],   zoom: 6 },
  Sul:            { center: [-28, -52],   zoom: 6 },
};

const _cache = new Map();

async function _fetchJson(path) {
  if (_cache.has(path)) return _cache.get(path);
  const res = await fetch(path);
  if (!res.ok) throw new Error(`GeoJSON não encontrado: ${path}`);
  const data = await res.json();
  _cache.set(path, data);
  return data;
}

/** Carrega o manifest (cobertura de dados reais, UFs disponíveis). */
export const loadManifest = () => _fetchJson(`${GEO_BASE}/manifest.json`);

/** Carrega os polígonos dos 27 estados. */
export const loadStates = () => _fetchJson(`${GEO_BASE}/brazil-states.json`);

/** Carrega o risco nacional sintético (geocode → {s,c,i,uf,n,r}). */
export const loadNationalRisk = () => _fetchJson(`${GEO_BASE}/risk-national.json`);

/** Carrega os municípios de uma UF específica. */
export const loadStateMunicipalities = (uf) => _fetchJson(`${GEO_BASE}/mun/${uf}.json`);

/**
 * Carrega e combina os municípios de todos os estados de uma região.
 * @param {string} region
 * @returns {Promise<{type:'FeatureCollection', features:Array}>}
 */
export async function loadRegionMunicipalities(region) {
  const ufs = REGION_UFS[region] || [];
  const collections = await Promise.all(
    ufs.map((uf) => loadStateMunicipalities(uf).catch(() => null)),
  );
  const features = collections
    .filter(Boolean)
    .flatMap((fc) => fc.features);
  return { type: 'FeatureCollection', features };
}

/** Todas as UFs do Brasil. */
export const ALL_UFS = Object.values(REGION_UFS).flat();

/**
 * Carrega TODOS os municípios do Brasil (27 UFs, ~5.564 polígonos).
 * @returns {Promise<{type:'FeatureCollection', features:Array}>}
 */
export async function loadAllMunicipalities() {
  const collections = await Promise.all(
    ALL_UFS.map((uf) => loadStateMunicipalities(uf).catch(() => null)),
  );
  const features = collections.filter(Boolean).flatMap((fc) => fc.features);
  return { type: 'FeatureCollection', features };
}

/** Cor de risco por score (mesma escala do design system). */
export function scoreColor(score) {
  if (score >= 85) return '#dc2626';
  if (score >= 70) return '#ea580c';
  if (score >= 50) return '#ca8a04';
  if (score >= 30) return '#65a30d';
  return '#16a34a';
}

/** Escala de risco CONTÍNUA (verde → vermelho), interpolada por score 0–100.
 *  Dá um mapa de calor mais detalhado e suave que a versão em degraus. */
const RISK_STOPS = [
  [0,   [22, 163, 74]],
  [25,  [132, 204, 22]],
  [50,  [250, 204, 21]],
  [75,  [249, 115, 22]],
  [100, [220, 38, 38]],
];
export function riskGradient(score) {
  const s = Math.max(0, Math.min(100, Number(score) || 0));
  for (let i = 0; i < RISK_STOPS.length - 1; i++) {
    const [s0, c0] = RISK_STOPS[i];
    const [s1, c1] = RISK_STOPS[i + 1];
    if (s <= s1) {
      const t = (s - s0) / (s1 - s0);
      const r = Math.round(c0[0] + (c1[0] - c0[0]) * t);
      const g = Math.round(c0[1] + (c1[1] - c0[1]) * t);
      const b = Math.round(c0[2] + (c1[2] - c0[2]) * t);
      return `rgb(${r},${g},${b})`;
    }
  }
  return 'rgb(220,38,38)';
}

/** Centroide aproximado (média amostrada do anel externo) — [lat, lng]. */
function _centroid(feature) {
  const g = feature.geometry;
  if (!g) return null;
  let ring;
  if (g.type === 'Polygon') ring = g.coordinates[0];
  else if (g.type === 'MultiPolygon') ring = g.coordinates[0][0];
  else return null;
  if (!ring || !ring.length) return null;
  let x = 0;
  let y = 0;
  let n = 0;
  const step = Math.max(1, Math.floor(ring.length / 10));
  for (let i = 0; i < ring.length; i += step) { x += ring[i][0]; y += ring[i][1]; n += 1; }
  return n ? [y / n, x / n] : null;
}

/** Pontos [lat, lng, intensidade] dos municípios quentes (score >= threshold),
 *  para o brilho de calor (leaflet.heat). */
export function riskHeatPoints(geo, threshold = 55) {
  if (!geo || !geo.features) return [];
  const pts = [];
  for (const f of geo.features) {
    const s = (f.properties && f.properties.score) || 0;
    if (s < threshold) continue;
    const c = _centroid(f);
    if (c) pts.push([c[0], c[1], s / 100]);
  }
  return pts;
}
